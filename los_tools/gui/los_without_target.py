from typing import Optional
import numpy as np

from qgis.PyQt.QtWidgets import (QWidget, QFormLayout)
from qgis.PyQt.QtCore import (Qt, pyqtSignal)
from qgis.PyQt.QtGui import (QColor, QKeyEvent)
from qgis.core import (QgsWkbTypes, QgsGeometry, QgsPoint, QgsPointLocator, Qgis)
from qgis.gui import (QgisInterface, QgsMapToolEdit, QgsUserInputWidget, QgsDoubleSpinBox,
                      QgsFloatingWidget, QgsMapMouseEvent, QgsRubberBand, QgsSnapIndicator)

from ..tools.util_functions import get_max_decimal_numbers, round_all_values
from .utils import prepare_user_input_widget


class LosNoTargetMapTool(QgsMapToolEdit):

    def __init__(self, iface: QgisInterface) -> None:
        super().__init__(iface.mapCanvas())
        self._iface = iface
        self._canvas = self._iface.mapCanvas()

        self._point = None

        self._snapper = self._canvas.snappingUtils()
        self.snap_marker = QgsSnapIndicator(self._canvas)

        self._los_rubber_band = self.createRubberBand(QgsWkbTypes.LineGeometry)

        self.floating_widget = LoSNoTargetInputWidget()
        self.floating_widget.hide()
        self.floating_widget.valuesChanged.connect(self.draw_los)

        self.user_input_widget = prepare_user_input_widget(self._canvas, self.floating_widget)

    def show_widgets(self) -> None:
        self.user_input_widget.show()
        self.floating_widget.show()

    def hide_widgets(self) -> None:
        self.user_input_widget.hide()
        self.floating_widget.hide()

    def activate(self) -> None:
        self.show_widgets()
        self._snapper = self._canvas.snappingUtils()
        return super(LosNoTargetMapTool, self).activate()

    def clean(self) -> None:
        self.hide_widgets()
        self.snap_marker.setVisible(False)
        self._rubber_band.hide()

    def deactivate(self) -> None:
        self.clean()
        self._iface.mapCanvas().unsetMapTool(self)
        super(LosNoTargetMapTool, self).deactivate()

    def canvasReleaseEvent(self, e: QgsMapMouseEvent) -> None:
        if e.button() == Qt.RightButton:
            self.deactivate()
        elif e.button() == Qt.LeftButton:
            self.show_widgets()
            if self._snap_point:
                self._point = self._snap_point
            else:
                self._point = e.mapPoint()
            self.draw_los()

    def canvasMoveEvent(self, event: QgsMapMouseEvent) -> None:
        result = self._snapper.snapToMap(event.pos())
        self.snap_marker.setMatch(result)
        if result.type() == QgsPointLocator.Vertex:
            self._snap_point = result.point()
        else:
            self._snap_point = None

    def keyPressEvent(self, e: QKeyEvent) -> None:
        if e.key() == Qt.Key_Escape:
            self.deactivate()
            self._iface.mapCanvas().unsetMapTool(self)
        return super().keyPressEvent(e)

    def draw_los(self):

        canvas_crs = self._canvas.mapSettings().destinationCrs()

        if canvas_crs.isGeographic():
            self.hide_widgets()
            self._iface.messageBar().pushMessage(
                "LoS can be drawn only for projected CRS. Canvas is currently in geographic CRS.",
                Qgis.Critical,
                duration=5)
            return

        if self._point:
            vlayer = self.currentVectorLayer()
            self._rubber_band.setToGeometry(QgsGeometry(), vlayer)
            angles = np.arange(self.floating_widget.min_angle,
                               self.floating_widget.max_angle +
                               0.000000001 * self.floating_widget.angle_step,
                               step=self.floating_widget.angle_step).tolist()
            round_digits = get_max_decimal_numbers([
                self.floating_widget.min_angle, self.floating_widget.max_angle,
                self.floating_widget.angle_step
            ])
            angles = round_all_values(angles, round_digits)

            for angle in angles:
                click_point = self.toLayerCoordinatesV2(vlayer,
                                                        QgsPoint(self._point.x(), self._point.y()))
                new_point = click_point.project(1, angle)
                geom = QgsGeometry.fromPolyline([click_point, new_point
                                                ]).extendLine(0, self.floating_widget.length - 1)
                self._rubber_band.addGeometry(geom, vlayer)
            self._rubber_band.show()


class LoSNoTargetInputWidget(QWidget):

    valuesChanged = pyqtSignal()

    def __init__(self, parent: Optional[QWidget] = None) -> None:
        super().__init__(parent)
        layout = QFormLayout()
        layout.setContentsMargins(0, 0, 0, 0)
        self.setLayout(layout)

        self._min_angle = QgsDoubleSpinBox(self)
        self._min_angle.setMinimum(-359.999)
        self._min_angle.setMaximum(359.999)
        self._min_angle.setValue(0)
        self._min_angle.setClearValue(0)
        self._min_angle.setDecimals(3)
        self._min_angle.valueChanged.connect(self._on_minimum_changed)
        self._min_angle.valueChanged.connect(self.emit_values_changed)
        self._max_angle = QgsDoubleSpinBox(self)
        self._max_angle.setMinimum(-359.999)
        self._max_angle.setMaximum(359.999)
        self._max_angle.setValue(359.999)
        self._max_angle.setClearValue(359)
        self._max_angle.setDecimals(3)
        self._max_angle.valueChanged.connect(self._on_maximum_changed)
        self._max_angle.valueChanged.connect(self.emit_values_changed)
        self._angle_step = QgsDoubleSpinBox(self)
        self._angle_step.setMinimum(0.001)
        self._angle_step.setMaximum(90)
        self._angle_step.setValue(1)
        self._angle_step.setClearValue(1)
        self._angle_step.setDecimals(3)
        self._angle_step.valueChanged.connect(self.emit_values_changed)
        self._length = QgsDoubleSpinBox(self)
        self._length.setMinimum(1)
        self._length.setMaximum(999999999)
        self._length.setValue(100)
        self._length.setClearValue(100)
        self._length.setDecimals(2)
        self._length.valueChanged.connect(self.emit_values_changed)

        layout.addRow("Minimum Azimuth", self._min_angle)
        layout.addRow("Maximal Azimuth", self._max_angle)
        layout.addRow("Angle Step", self._angle_step)
        layout.addRow("LoS Length", self._length)

    def set_units(self, unit: QgsUnitTypes) -> None:
        self._length.setSuffix(" {}".format(QgsUnitTypes.toString(unit)))

    def _on_minimum_changed(self) -> None:
        if self._max_angle.value() < self._min_angle.value():
            self._max_angle.setValue(self._min_angle.value())

    def _on_maximum_changed(self) -> None:
        if self._min_angle.value() > self._max_angle.value():
            self._min_angle.setValue(self._max_angle.value())

    def emit_values_changed(self) -> None:
        self.valuesChanged.emit()

    @property
    def min_angle(self) -> float:
        return self._min_angle.value()

    @property
    def max_angle(self) -> float:
        return self._max_angle.value()

    @property
    def angle_step(self) -> float:
        if self._angle_step.value() == 0:
            return 0.01
        return self._angle_step.value()

    @property
    def length(self) -> float:
        return self._length.value()
