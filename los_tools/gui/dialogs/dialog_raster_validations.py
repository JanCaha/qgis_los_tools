from typing import List

from qgis.core import QgsPointXY, QgsProject, QgsRasterLayer, QgsUnitTypes
from qgis.gui import QgisInterface
from qgis.PyQt.QtCore import Qt, pyqtSignal
from qgis.PyQt.QtWidgets import (
    QDialog,
    QFormLayout,
    QGroupBox,
    QHeaderView,
    QLabel,
    QLineEdit,
    QPushButton,
    QTextBrowser,
    QTreeWidget,
    QTreeWidgetItem,
)

from los_tools.classes.list_raster import ListOfRasters
from los_tools.gui.tools.point_capture_map_tool import PointCaptureMapTool


class RasterValidations(QDialog):

    map_tool: PointCaptureMapTool
    list_of_rasters: ListOfRasters

    selectedRastersChanged = pyqtSignal()

    def __init__(self, iface: QgisInterface = None) -> None:
        super().__init__(iface.mainWindow())

        self._iface = iface
        self._canvas = self._iface.mapCanvas()

        self._point = None
        self._point_crs = None

        self.list_of_rasters = ListOfRasters([])

        self.init_gui()

        self._setup_layers()

    def init_gui(self):
        self.setMinimumWidth(600)
        self.setWindowTitle("Rasters Validation and Sampling")

        layout = QFormLayout(self)
        self.setLayout(layout)

        layout.addRow(QLabel("Select RasterLayers to use"))

        self._rasters_view = QTreeWidget(self)
        self._rasters_view.setColumnCount(2)
        self._rasters_view.setHeaderLabels(["Rasters", "Cell size (x - y)"])
        self._rasters_view.setMaximumHeight(150)
        self._rasters_view.header().setSectionResizeMode(QHeaderView.ResizeToContents)
        layout.addRow(self._rasters_view)

        self.text = QTextBrowser(self)
        self.text.setMaximumHeight(75)

        layout.addRow(QLabel("Validation messages"))
        layout.addRow(self.text)

        self._rasters_view.itemChanged.connect(self.validate)
        self._rasters_view.itemChanged.connect(self.test_interpolated_value_at_point)
        self._rasters_view.itemChanged.connect(self.selectedRastersChanged.emit)

        self.select_point = QPushButton()
        self.select_point.setText("Choose sample point on the map")
        self.select_point.clicked.connect(self.select_sample_point)
        self.select_point.setEnabled(False)

        self.point_coordinate = QLineEdit()
        self.point_coordinate.setReadOnly(True)

        self.sampled_from_raster = QLineEdit()
        self.sampled_from_raster.setReadOnly(True)

        self.sampled_value = QLineEdit()
        self.sampled_value.setReadOnly(True)

        group_box = QGroupBox("Test Sampling", self)
        group_layout = QFormLayout()
        group_box.setLayout(group_layout)

        group_layout.addRow(self.select_point)
        group_layout.addRow("Selected point", self.point_coordinate)
        group_layout.addRow("Value sampled from", self.sampled_from_raster)
        group_layout.addRow("Sampled value", self.sampled_value)

        layout.addRow(group_box)

    def _setup_layers(self) -> None:
        self._rasters_view.clear()

        project = QgsProject.instance()

        layers = [x for x in project.mapLayers(True)]

        rasters_tmp: List[QgsRasterLayer] = []

        for layerId in layers:
            layer = project.mapLayer(layerId)
            if isinstance(layer, QgsRasterLayer):
                if layer.providerType() == "wms":
                    continue
                rasters_tmp.append(layer)

        for raster in rasters_tmp:
            item_name = raster.name()

            if self._rasters_view.findItems(item_name, Qt.MatchFlag.MatchExactly):
                continue

            item = QTreeWidgetItem()
            item.setText(0, raster.name())
            item.setData(0, Qt.UserRole, raster.id())
            item.setCheckState(0, Qt.CheckState.Unchecked)

            distance_unit = raster.crs().mapUnits()
            distance_unit = QgsUnitTypes.toAbbreviatedString(distance_unit)

            item.setText(
                1,
                f"{round(raster.extent().width() / raster.width(), 3)} {distance_unit}"
                " - "
                f"{round(raster.extent().height() / raster.height(), 3)} {distance_unit}",
            )
            item.setData(1, Qt.UserRole, raster.extent().width() / raster.width())

            self._rasters_view.addTopLevelItem(item)

    def sync(self):
        self._rasters_view.blockSignals(True)

        rasters = self.list_of_rasters.rasters

        for raster in rasters:
            for item in self._rasters_view.findItems(raster.name(), Qt.MatchFlag.MatchExactly):
                data = item.data(0, Qt.UserRole)
                if data == raster.id():
                    item.setCheckState(0, Qt.CheckState.Checked)
                    break

        self._rasters_view.blockSignals(False)

    def setup_used_rasters(self, list_of_rasters: ListOfRasters) -> None:
        self.list_of_rasters = list_of_rasters
        self.sync()

    def open(self) -> None:
        self.validate()
        super().open()

    def exec(self) -> int:
        self.validate()
        return super().exec()

    def select_sample_point(self) -> None:
        self.map_tool = PointCaptureMapTool(self._canvas)
        self.map_tool.canvasClicked.connect(self.update_test_point)
        self.map_tool.canvasClicked.connect(self.map_tool.deactivate)
        self.map_tool.deactivated.connect(self.show)

        self._canvas.setMapTool(self.map_tool)
        self.hide()

    def update_test_point(self, point: QgsPointXY) -> None:
        self.show()
        canvas_crs = self._canvas.mapSettings().destinationCrs()
        text_point = f"{point.x():.3f};{point.y():.3f}[{canvas_crs.authid()}]"
        self.point_coordinate.setText(text_point)
        self._point = QgsPointXY(point.x(), point.y())
        self._point_crs = canvas_crs
        self.test_interpolated_value_at_point()

    @property
    def listOfRasters(self) -> ListOfRasters:
        try:
            return ListOfRasters(self.list_of_selected_rasters)
        except ValueError:
            return ListOfRasters([])

    def test_interpolated_value_at_point(self):
        if self.list_of_selected_rasters and self._point and self._point_crs:
            list_of_rasters = self.listOfRasters
            if not list_of_rasters.is_empty():
                value = list_of_rasters.extract_interpolated_value_at_point(self._point, self._point_crs)
                if value:
                    value = str(round(value, 6))
                else:
                    value = "No value"

                self.sampled_from_raster.setText(
                    f"{list_of_rasters.sampling_from_raster_at_point(self._point, self._point_crs)} (Raster Layer)"
                )
                self.sampled_value.setText(value)

    @property
    def list_of_selected_rasters(self) -> List[QgsRasterLayer]:
        rasters_selected = []

        for i in range(self._rasters_view.topLevelItemCount()):
            item = self._rasters_view.topLevelItem(i)
            if item.checkState(0) == Qt.CheckState.Checked:
                layer: QgsRasterLayer = QgsProject.instance().mapLayer(item.data(0, Qt.UserRole))
                rasters_selected.append(layer)

        return rasters_selected

    def validate(self):
        rasters = self.list_of_selected_rasters

        all_msgs = []

        if 0 < len(rasters):
            valid, msg = ListOfRasters.validate_bands(rasters)
            if not valid:
                all_msgs.append(msg)

            valid, msg = ListOfRasters.validate_crs(rasters)
            if not valid:
                all_msgs.append(msg)

            valid, msg = ListOfRasters.validate_ordering(rasters)
            if not valid:
                all_msgs.append(msg)

            valid, msg = ListOfRasters.validate_square_cell_size(rasters)
            if not valid:
                all_msgs.append(msg)

        else:
            all_msgs.append("No raster layers selected, nothing to check.")

        if all_msgs:
            self.text.setText("\n\n".join(all_msgs))
        else:
            self.text.setText("Selection is valid and can be used in LoS creation tools.")

        self.select_point.setEnabled(not self.listOfRasters.is_empty())
