from typing import List, Dict

from qgis.core import (QgsProject, QgsRasterLayer, QgsPointXY)
from qgis.PyQt.QtWidgets import (QDialog, QPushButton, QFormLayout, QTreeWidget, QLabel,
                                 QTreeWidgetItem, QGroupBox, QTextBrowser, QLineEdit)
from qgis.PyQt.QtCore import (Qt)

from ..classes.list_raster import ListOfRasters
from .dialog_tool_set_camera import PointCaptureMapTool


class RasterValidations(QDialog):

    def __init__(self, iface=None) -> None:
        super().__init__(iface.mainWindow())

        self._iface = iface
        self._canvas = self._iface.mapCanvas()

        self._point = None
        self._point_crs = None

        self.map_tool = PointCaptureMapTool(self._canvas)
        self.map_tool.canvasClicked.connect(self.update_test_point)

        self.rasters: List[QgsRasterLayer] = []
        self.rasters_selected: Dict[str, bool] = {}

        self.init_gui()

    def init_gui(self):

        self.setWindowTitle("Rasters Validation and Sampling")

        layout = QFormLayout(self)
        self.setLayout(layout)

        layout.addRow(QLabel("Select RasterLayers to use"))

        self._rasters_view = QTreeWidget(self)
        self._rasters_view.setColumnCount(1)
        self._rasters_view.setHeaderLabels(["Rasters", "Cell size"])
        self._rasters_view.setMaximumHeight(150)
        layout.addRow(self._rasters_view)

        self.text = QTextBrowser(self)
        self.text.setMaximumHeight(75)

        layout.addRow(QLabel("Validation messages"))
        layout.addRow(self.text)

        self._rasters_view.itemChanged.connect(self.validate)
        self._rasters_view.itemChanged.connect(self.test_interpolated_value_at_point)
        self._rasters_view.itemChanged.connect(self.update_selected_rasters)

        self.select_point = QPushButton()
        self.select_point.setText("Choose sample point on the map")
        self.select_point.clicked.connect(self.select_sample_point)

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
        group_layout.addRow(QLabel("Selected point"))
        group_layout.addRow(self.point_coordinate)
        group_layout.addRow("Value sampled from", self.sampled_from_raster)
        group_layout.addRow("Sampled value", self.sampled_value)

        layout.addRow(group_box)

    def _populate_raster_view(self) -> None:
        self._rasters_view.clear()
        for raster in self.rasters:
            item = QTreeWidgetItem()
            item.setText(0, raster.name())
            item.setData(0, Qt.UserRole, raster)
            if self.rasters_selected.get(raster.id()) is not None:
                if self.rasters_selected.get(raster.id()):
                    item.setCheckState(0, Qt.CheckState.Checked)
                else:
                    item.setCheckState(0, Qt.CheckState.Unchecked)
            else:
                item.setCheckState(0, Qt.CheckState.Unchecked)

            distance_unit = raster.crs().mapUnits()
            distance_unit = QgsUnitTypes.toAbbreviatedString(distance_unit)

            item.setText(
                1, "{} {} - {} {}".format(round(raster.extent().width() / raster.width(),
                                                3), distance_unit,
                                          round(raster.extent().height() / raster.height(), 3),
                                          distance_unit))
            item.setData(1, Qt.UserRole, raster.extent().width() / raster.width())

            self._rasters_view.addTopLevelItem(item)

    def _raster_layers(self) -> List[QgsRasterLayer]:
        project = QgsProject.instance()
        rasters_tmp = []
        for layerId in self._raster_layers_ids():
            layer = project.mapLayer(layerId)
            if isinstance(layer, QgsRasterLayer):
                rasters_tmp.append(layer)

        return rasters_tmp

    def _raster_layers_ids(self) -> List[str]:
        project = QgsProject.instance()
        layers = [x for x in project.mapLayers(True)]
        return layers

    def _data_reset(self) -> None:
        self._prev_map_tool = self._canvas.mapTool()
        self._prev_cursor = self._canvas.cursor()

        rasters_tmp = self._raster_layers()

        if self.rasters != rasters_tmp:
            self.rasters = rasters_tmp
            self._populate_raster_view()

    def open(self) -> None:
        self._data_reset()
        super().open()

    def exec(self) -> int:
        self._data_reset()
        return super().exec()

    def select_sample_point(self) -> None:
        self._canvas.setMapTool(self.map_tool)
        self.close()

    def update_test_point(self, point):
        self.restore_canvas_tools()
        self.open()
        canvas_crs = self._canvas.mapSettings().destinationCrs()
        text_point = "{:.3f};{:.3f}[{}]".format(point.x(), point.y(), canvas_crs.authid())
        self.point_coordinate.setText(text_point)
        self._point = QgsPointXY(point.x(), point.y())
        self._point_crs = canvas_crs
        self.test_interpolated_value_at_point()

    def restore_canvas_tools(self) -> None:
        self._canvas.setMapTool(self._prev_map_tool)
        self._canvas.setCursor(self._prev_cursor)

    def update_selected_rasters(self, item: QTreeWidgetItem, column: int) -> None:
        raster: QgsRasterLayer = item.data(0, Qt.UserRole)
        self.rasters_selected[raster.id()] = item.checkState(0) == Qt.CheckState.Checked

    @property
    def listOfRasters(self) -> ListOfRasters:
        return ListOfRasters(self.list_of_selected_rasters)

    def test_interpolated_value_at_point(self):

        if self.list_of_selected_rasters and self._point and self._point_crs:

            list_of_rasters = self.listOfRasters
            value = list_of_rasters.extract_interpolated_value_at_point(
                self._point, self._point_crs)
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
                rasters_selected.append(item.data(0, Qt.UserRole))

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
