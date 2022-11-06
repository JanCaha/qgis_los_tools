from typing import Optional, Union
import numpy as np
from functools import partial

from qgis.PyQt.QtWidgets import (QWidget, QFormLayout, QComboBox, QPushButton, QAction)
from qgis.PyQt.QtCore import (Qt, pyqtSignal)
from qgis.PyQt.QtGui import (QKeyEvent)
from qgis.core import (QgsWkbTypes, QgsGeometry, QgsVectorLayer, QgsPointLocator, Qgis, QgsPoint,
                       QgsPointXY, QgsVertexId, QgsFeature, QgsTask, QgsTaskManager,
                       QgsCoordinateReferenceSystem, QgsCoordinateTransform, QgsProject)
from qgis.gui import (QgisInterface, QgsMapToolEdit, QgsDoubleSpinBox, QgsMapMouseEvent,
                      QgsSnapIndicator)

from ..tools.util_functions import get_max_decimal_numbers, round_all_values
from ..constants.field_names import FieldNames
from ..constants.names_constants import NamesConstants
from .utils import prepare_user_input_widget
from ..tools.util_functions import segmentize_los_line
from .dialog_raster_validations import RasterValidations
from .dialog_los_settings import LoSSettings, DistanceWidget, Distance
from ..classes.sampling_distance_matrix import SamplingDistanceMatrix
from ..classes.list_raster import ListOfRasters


class CreateLoSMapTool(QgsMapToolEdit):

    featuresAdded = pyqtSignal()

    def __init__(self,
                 iface: QgisInterface,
                 raster_validation_dialog: RasterValidations,
                 los_settings_dialog: LoSSettings,
                 los_layer: QgsVectorLayer = None,
                 add_result_action: QAction = None) -> None:

        super().__init__(iface.mapCanvas())
        self._iface = iface
        self._canvas = self._iface.mapCanvas()

        self.task_manager = QgsTaskManager()

        self._los_layer = los_layer

        self._raster_validation_dialog = raster_validation_dialog
        self._los_settings_dialog = los_settings_dialog

        self.add_result_action = add_result_action

        self._start_point: QgsPointXY = None

        self._last_towards_point: QgsPointXY = None

        self._snapper = self._canvas.snappingUtils()
        self.snap_marker = QgsSnapIndicator(self._canvas)

        self._los_rubber_band = self.createRubberBand(QgsWkbTypes.LineGeometry)

        self.floating_widget = LoSNoTargetInputWidget()
        self.floating_widget.hide()
        self.floating_widget.valuesChanged.connect(partial(self.draw_los, None))
        self.floating_widget.saveToLayerClicked.connect(self.add_los_to_layer)

        self.user_input_widget = prepare_user_input_widget(self._canvas, self.floating_widget)

    def set_los_layer(self, layer: QgsVectorLayer) -> None:
        self._los_layer = layer

    def show_widgets(self) -> None:
        self.user_input_widget.show()
        self.floating_widget.show()

    def hide_widgets(self) -> None:
        self.user_input_widget.hide()
        self.floating_widget.hide()

    def activate(self) -> None:
        self.messageDiscarded.emit()
        self._canvas = self._iface.mapCanvas()
        self._snapper = self._canvas.snappingUtils()
        if self._canvas.mapSettings().destinationCrs().isGeographic():
            self.messageEmitted.emit(
                "Tool only works if canvas is in projected CRS. Currently canvas is in geographic CRS.",
                Qgis.Critical)
            self.hide_widgets()
            self.deactivate()
            return
        if not ListOfRasters.validate(self._raster_validation_dialog.list_of_selected_rasters):
            self.messageEmitted.emit("Tool needs valid setup in `Raster Validatations` dialog.",
                                     Qgis.Critical)
            self.deactivate()
            return
        # self.floating_widget.set_units(self._canvas.mapSettings().destinationCrs().mapUnits())
        self.show_widgets()
        return super(CreateLoSMapTool, self).activate()

    def clean(self) -> None:
        self.floating_widget.disableAddLos()
        self.hide_widgets()
        self.snap_marker.setVisible(False)
        self._los_rubber_band.hide()
        self._start_point = None

    def deactivate(self) -> None:
        self.clean()
        self._iface.mapCanvas().unsetMapTool(self)
        super(CreateLoSMapTool, self).deactivate()

    def canvasReleaseEvent(self, e: QgsMapMouseEvent) -> None:
        if e.button() == Qt.RightButton:
            self.clean()
        elif e.button() == Qt.LeftButton:
            self.show_widgets()
            if self._start_point is None:
                if self._snap_point:
                    self._start_point = self._snap_point
                else:
                    self._start_point = e.mapPoint()
            else:
                self.draw_los(self._snap_point)
                self.floating_widget.enableAddLos()
                self._start_point = None

    def canvasMoveEvent(self, event: QgsMapMouseEvent) -> None:
        result = self._snapper.snapToMap(event.pos())
        self.snap_marker.setMatch(result)
        if result.type() == QgsPointLocator.Vertex:
            self._snap_point = result.point()
        else:
            self._snap_point = event.mapPoint()

        if self._start_point is not None:
            self.draw_los(self._snap_point)

    def keyPressEvent(self, e: QKeyEvent) -> None:
        if e.key() == Qt.Key_Escape:
            self.deactivate()
            self._iface.mapCanvas().unsetMapTool(self)
        return super().keyPressEvent(e)

    def draw_los(self, towards_point: QgsPointXY):

        if towards_point is None:
            towards_point = self._last_towards_point

        canvas_crs = self._canvas.mapSettings().destinationCrs()

        if canvas_crs.isGeographic():
            self.hide_widgets()
            self._iface.messageBar().pushMessage(
                "LoS can be drawn only for projected CRS. Canvas is currently in geographic CRS.",
                Qgis.Critical,
                duration=5)
            return

        if self._start_point and towards_point:

            self._los_rubber_band.hide()

            rasters_extent = self._raster_validation_dialog.listOfRasters.extent_polygon()

            if self.floating_widget.los_local or self.floating_widget.los_global:

                if self.floating_widget.los_local:
                    line = QgsGeometry.fromPolylineXY([self._start_point, towards_point])

                if self.floating_widget.los_global:
                    line = QgsGeometry.fromPolylineXY([self._start_point, towards_point])

                    if self._start_point.distance(towards_point) > 0:
                        line = line.extendLine(
                            0,
                            self._raster_validation_dialog.listOfRasters.maximal_diagonal_size())

                        # insert target point
                        line.get().insertVertex(QgsVertexId(0, 0, 1),
                                                QgsPoint(towards_point.x(), towards_point.y()))

                line = line.intersection(rasters_extent)

                self._los_rubber_band.setToGeometry(line,
                                                    self._canvas.mapSettings().destinationCrs())

            if self.floating_widget.los_no_target:

                self._los_rubber_band.setToGeometry(QgsGeometry(),
                                                    self._canvas.mapSettings().destinationCrs())

                maximal_length_distance = self._los_settings_dialog.los_maximal_length()

                if maximal_length_distance is None:
                    maximal_length = self._raster_validation_dialog.listOfRasters.maximal_diagonal_size(
                    )
                else:
                    maximal_length = maximal_length_distance.inUnits(
                        self._los_layer.crs().mapUnits())

                angle = self._start_point.azimuth(towards_point)

                angles = np.arange(
                    angle - self.floating_widget.angle_difference,
                    angle + self.floating_widget.angle_difference +
                    0.000000001 * self.floating_widget.angle_step,
                    self.floating_widget.angle_step).tolist()
                round_digits = get_max_decimal_numbers([
                    angle - self.floating_widget.angle_difference,
                    angle + self.floating_widget.angle_difference +
                    0.000000001 * self.floating_widget.angle_step, self.floating_widget.angle_step
                ])
                angles = round_all_values(angles, round_digits)
                size_constant = 1
                for angle in angles:
                    new_point = self._start_point.project(size_constant, angle)
                    line = QgsGeometry.fromPolylineXY([self._start_point, new_point])
                    line = line.extendLine(0, maximal_length - size_constant)

                    line = line.intersection(rasters_extent)

                    self._los_rubber_band.addGeometry(line,
                                                      self._canvas.mapSettings().destinationCrs())

            self._los_rubber_band.show()

        if towards_point:
            self._last_towards_point = QgsPointXY(towards_point.x(), towards_point.y())

    def set_result_action_active(self, active: bool) -> None:
        if self.add_result_action:
            self.add_result_action.setEnabled(active)

    def add_los_to_layer(self) -> None:
        los_geometry = self._los_rubber_band.asGeometry()

        list_of_rasters = self._raster_validation_dialog.listOfRasters

        # text = self.add_result_action.text()
        # self.add_result_action.setText("Obtaining data ...")
        self.set_result_action_active(False)

        if los_geometry.get().partCount() == 1:

            task = PrepareLoSTask(
                los_geometry,
                self.floating_widget.sampling_distance.inUnits(self._los_layer.crs().mapUnits()),
                self._los_layer, list_of_rasters, self.floating_widget.observer_offset,
                self.floating_widget.target_offset, self.floating_widget.los_global,
                self._iface.mapCanvas().mapSettings().destinationCrs())

        else:

            task = PrepareLoSWithoutTargetTask(
                los_geometry, self._los_layer, list_of_rasters, self._los_settings_dialog,
                self.floating_widget.observer_offset, self.floating_widget.angle_step,
                self._iface.mapCanvas().mapSettings().destinationCrs())

        task.taskCompleted.connect(self.task_finished)

        self.task_manager.addTask(task)

    def task_finished(self) -> None:
        self.featuresAdded.emit()
        self.set_result_action_active(True)
        self._iface.messageBar().pushMessage("LoS Without Target Processing Finished",
                                             Qgis.MessageLevel.Info, 2)


class LoSNoTargetInputWidget(QWidget):

    valuesChanged = pyqtSignal()
    saveToLayerClicked = pyqtSignal()

    def __init__(self, parent: Optional[QWidget] = None) -> None:
        super().__init__(parent)

        self._support_storing: bool = False

        self.form_layout = QFormLayout()
        self.form_layout.setContentsMargins(0, 0, 0, 0)
        self.setLayout(self.form_layout)

        self._los_type = QComboBox(self)
        self._los_type.addItem("Local")
        self._los_type.addItem("Global")
        self._los_type.addItem("No Target")
        self._los_type.currentIndexChanged.connect(self.change_setting_enabled)

        self._observers_offset = QgsDoubleSpinBox(self)
        self._observers_offset.setMinimum(0.0)
        self._observers_offset.setMaximum(999999.999)
        self._observers_offset.setValue(1.6)
        self._observers_offset.setClearValue(1.6)

        self._target_offset = QgsDoubleSpinBox(self)
        self._target_offset.setMinimum(0.0)
        self._target_offset.setMaximum(999999.999)
        self._target_offset.setValue(0.0)
        self._target_offset.setClearValue(0.0)

        self._sampling_distance = DistanceWidget(self)
        self._sampling_distance.setMinimum(0.01)
        self._sampling_distance.setMaximum(999999.999)
        self._sampling_distance.setValue(1.0)
        self._sampling_distance.setClearValue(1.0)
        self._sampling_distance.setDecimals(2)

        self._angle_difference = QgsDoubleSpinBox(self)
        self._angle_difference.setMinimum(0.000)
        self._angle_difference.setMaximum(180.000)
        self._angle_difference.setValue(10.000)
        self._angle_difference.setClearValue(10.000)
        self._angle_difference.setDecimals(3)
        self._angle_difference.setEnabled(False)
        self._angle_difference.setSuffix("°")
        self._angle_difference.valueChanged.connect(self.emit_values_changed)

        self._angle_step = QgsDoubleSpinBox(self)
        self._angle_step.setMinimum(0.001)
        self._angle_step.setMaximum(90)
        self._angle_step.setValue(1)
        self._angle_step.setClearValue(1)
        self._angle_step.setDecimals(3)
        self._angle_step.setEnabled(False)
        self._angle_step.setSuffix("°")
        self._angle_step.valueChanged.connect(self.angle_step_changed)
        self._angle_step.valueChanged.connect(self.emit_values_changed)

        self._add_los_to_layer = QPushButton("Add LoS to Plugin Layer")
        self._add_los_to_layer.setEnabled(False)
        self._add_los_to_layer.clicked.connect(self.clickedAddLosToLayer)

        self.form_layout.addRow("LoS Type", self._los_type)
        self.form_layout.addRow("Observer Offset", self._observers_offset)
        self.form_layout.addRow("Target Offset", self._target_offset)
        self.form_layout.addRow("Sampling Distance", self._sampling_distance)
        self.form_layout.addRow("Angle Difference", self._angle_difference)
        self.form_layout.addRow("Angle Step", self._angle_step)
        self.form_layout.addWidget(self._add_los_to_layer)

    def change_setting_enabled(self) -> None:
        self._angle_difference.setEnabled(self.los_no_target)
        self._angle_step.setEnabled(self.los_no_target)
        if self.los_local or self.los_global:
            self._angle_difference.setEnabled(False)
            self._angle_step.setEnabled(False)
            self._sampling_distance.setEnabled(True)
            self._target_offset.setEnabled(True)
        else:
            self._angle_difference.setEnabled(True)
            self._angle_step.setEnabled(True)
            self._sampling_distance.setEnabled(False)
            self._target_offset.setEnabled(False)

    def angle_step_changed(self) -> None:
        if self._angle_step.value() > self._angle_difference.value() * 2:
            self._angle_step.setValue(self._angle_difference.value() * 2)

    @property
    def sampling_distance(self) -> Distance:
        return self._sampling_distance.distance()

    @property
    def observer_offset(self) -> float:
        return self._observers_offset.value()

    @property
    def target_offset(self) -> float:
        return self._target_offset.value()

    @property
    def angle_step(self) -> float:
        return self._angle_step.value()

    @property
    def angle_difference(self) -> float:
        return self._angle_difference.value()

    @property
    def los_type(self) -> str:
        return self._los_type.currentText()

    @property
    def los_local(self) -> bool:
        return self._los_type.currentText() == "Local"

    @property
    def los_global(self) -> bool:
        return self._los_type.currentText() == "Global"

    @property
    def los_no_target(self) -> bool:
        return self._los_type.currentText() == "No Target"

    def emit_values_changed(self) -> None:
        self.valuesChanged.emit()

    def clickedAddLosToLayer(self) -> None:
        self.saveToLayerClicked.emit()
        self.disableAddLos()

    def enableAddLos(self) -> None:
        if self._support_storing:
            self._add_los_to_layer.setEnabled(True)

    def disableAddLos(self) -> None:
        self._add_los_to_layer.setEnabled(False)

    def set_support_storing(self, support_storing: bool) -> None:
        self._support_storing = support_storing

    @property
    def support_storing(self) -> bool:
        return self._support_storing


class PrepareLoSWithoutTargetTask(QgsTask):

    def __init__(self,
                 lines: QgsGeometry,
                 los_layer: QgsVectorLayer,
                 list_of_rasters: ListOfRasters,
                 los_settings: LoSSettings,
                 observer_offset: float,
                 angle_step: float,
                 canvas_crs: QgsCoordinateReferenceSystem,
                 description: str = "Prepare LoS without Target",
                 flags: Union['QgsTask.Flags', 'QgsTask.Flag'] = QgsTask.Flag.CanCancel) -> None:
        super().__init__(description, flags)
        self.lines = lines
        self.list_of_rasters = list_of_rasters

        self.sampling_distance_matrix = SamplingDistanceMatrix(los_settings.create_data_layer())
        self.sampling_distance_matrix.replace_minus_one_with_value(
            list_of_rasters.maximal_diagonal_size())

        self.fields = los_layer.fields()
        self.los_layer = los_layer
        self.observer_offset = observer_offset
        self.angle_step = angle_step
        self.canvas_crs = canvas_crs

        values = self.los_layer.uniqueValues(self.fields.indexFromName(FieldNames.ID_OBSERVER))
        if values:
            self.observer_max_id = max(values)
        else:
            self.observer_max_id = 0

        values = self.los_layer.uniqueValues(self.fields.indexFromName(FieldNames.ID_TARGET))
        if values:
            self.target_max_id = max(values)
        else:
            self.target_max_id = 0

        self.setDependentLayers([self.los_layer])

    def run(self):

        number_of_lines = self.lines.get().partCount()

        partsIterator = self.lines.get().parts()

        feature_template = QgsFeature(self.fields)

        ctToRaster = QgsCoordinateTransform(self.canvas_crs, self.list_of_rasters.crs(),
                                            QgsProject.instance())

        ctToLayer = QgsCoordinateTransform(self.list_of_rasters.crs(), self.los_layer.crs(),
                                           QgsProject.instance())

        j = 1
        while (partsIterator.hasNext()):

            geom = partsIterator.next()

            observer_point = geom.vertexAt(QgsVertexId(0, 0, 0))
            line = self.sampling_distance_matrix.build_line(observer_point,
                                                            geom.vertexAt(QgsVertexId(0, 0, 1)))

            line.transform(ctToRaster)

            line = self.list_of_rasters.add_z_values(line.points())

            f = QgsFeature(feature_template)

            line.transform(ctToLayer)

            f.setGeometry(line)

            azimuth = observer_point.azimuth(geom.vertexAt(QgsVertexId(0, 0, 1)))
            if azimuth < 0:
                azimuth = azimuth + 360

            f.setAttribute(f.fieldNameIndex(FieldNames.LOS_TYPE), NamesConstants.LOS_NO_TARGET)
            f.setAttribute(f.fieldNameIndex(FieldNames.ID_OBSERVER), int(self.observer_max_id + 1))
            f.setAttribute(f.fieldNameIndex(FieldNames.ID_TARGET), int(self.target_max_id + j))
            f.setAttribute(f.fieldNameIndex(FieldNames.OBSERVER_OFFSET), self.observer_offset)
            f.setAttribute(f.fieldNameIndex(FieldNames.AZIMUTH), azimuth)
            f.setAttribute(f.fieldNameIndex(FieldNames.OBSERVER_X), observer_point.x())
            f.setAttribute(f.fieldNameIndex(FieldNames.OBSERVER_Y), observer_point.y())
            f.setAttribute(f.fieldNameIndex(FieldNames.ANGLE_STEP), self.angle_step)

            self.los_layer.dataProvider().addFeature(f)
            self.setProgress((j / number_of_lines) * 100)
            j += 1

        return True


class PrepareLoSTask(QgsTask):

    def __init__(self,
                 los_geometry: QgsGeometry,
                 segment_length: float,
                 los_layer: QgsVectorLayer,
                 list_of_rasters: ListOfRasters,
                 observer_offset: float,
                 target_offset: float,
                 los_global: bool,
                 canvas_crs: QgsCoordinateReferenceSystem,
                 description: str = "Prepare LoS without Target",
                 flags: Union['QgsTask.Flags', 'QgsTask.Flag'] = QgsTask.Flag.CanCancel) -> None:
        super().__init__(description, flags)
        self.los_geometry = los_geometry
        self.segment_lenght = segment_length
        self.list_of_rasters = list_of_rasters

        self.fields = los_layer.fields()
        self.los_layer = los_layer
        self.observer_offset = observer_offset
        self.target_offset = target_offset
        self.los_global = los_global
        self.canvas_crs = canvas_crs

        values = self.los_layer.uniqueValues(self.fields.indexFromName(FieldNames.ID_OBSERVER))
        if values:
            self.observer_max_id = max(values)
        else:
            self.observer_max_id = 0

        values = self.los_layer.uniqueValues(self.fields.indexFromName(FieldNames.ID_TARGET))
        if values:
            self.target_max_id = max(values)
        else:
            self.target_max_id = 0

        self.setDependentLayers([self.los_layer])

    def run(self):

        ct = QgsCoordinateTransform(self.canvas_crs, self.list_of_rasters.crs(),
                                    QgsProject.instance())

        line = segmentize_los_line(self.los_geometry, self.segment_lenght)

        line.transform(ct)

        line = self.list_of_rasters.add_z_values(line.points())

        f = QgsFeature(self.fields)

        ct = QgsCoordinateTransform(self.list_of_rasters.crs(), self.los_layer.crs(),
                                    QgsProject.instance())

        line.transform(ct)

        f.setGeometry(line)
        f.setAttribute(f.fieldNameIndex(FieldNames.ID_OBSERVER), int(self.observer_max_id + 1))
        f.setAttribute(f.fieldNameIndex(FieldNames.ID_TARGET), int(self.target_max_id + 1))
        f.setAttribute(f.fieldNameIndex(FieldNames.OBSERVER_OFFSET),
                       float(self.floating_widget.observer_offset))
        f.setAttribute(f.fieldNameIndex(FieldNames.TARGET_OFFSET),
                       float(self.floating_widget.target_offset))

        if self.los_global:
            f.setAttribute(f.fieldNameIndex(FieldNames.TARGET_X),
                           float(self.los_geometry.vertexAt(1).x()))
            f.setAttribute(f.fieldNameIndex(FieldNames.TARGET_Y),
                           float(self.los_geometry.vertexAt(1).y()))
            f.setAttribute(f.fieldNameIndex(FieldNames.LOS_TYPE), NamesConstants.LOS_GLOBAL)
        else:
            f.setAttribute(f.fieldNameIndex(FieldNames.LOS_TYPE), NamesConstants.LOS_LOCAL)

        self.los_layer.dataProvider().addFeature(f)

        return True
