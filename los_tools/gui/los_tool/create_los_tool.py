import typing

from qgis.core import QgsGeometry, QgsPoint, QgsPointXY, QgsTask, QgsVectorLayer, QgsVertexId
from qgis.gui import QgisInterface, QgsMapMouseEvent
from qgis.PyQt.QtCore import Qt

from los_tools.classes.list_raster import ListOfRasters
from los_tools.gui.los_tasks import PrepareLoSTask
from los_tools.gui.los_tool.create_los_widget import LoSInputWidget
from los_tools.gui.tools.los_digitizing_tool_with_widget import LoSDigitizingToolWithWidget


class CreateLoSMapTool(LoSDigitizingToolWithWidget):

    def __init__(
        self,
        iface: QgisInterface,
        raster_list: ListOfRasters,
        los_layer: QgsVectorLayer = None,
    ) -> None:
        super().__init__(iface, raster_list, los_layer)

        self.create_widget()

    def create_widget(self):
        self._widget = LoSInputWidget()
        self._widget.valuesChanged.connect(self.draw_los)
        super().create_widget()

    def clean(self) -> None:
        super().clean()
        if self._widget:
            self._widget.setAddLoSEnabled(False)

    def canvasReleaseEvent(self, e: typing.Optional[QgsMapMouseEvent]) -> None:
        if e.button() == Qt.MouseButton.RightButton and self._start_point is None and self._los_rubber_band.size() == 0:
            self.deactivate()
        if e.button() == Qt.MouseButton.RightButton:
            self.clean()
        elif e.button() == Qt.MouseButton.LeftButton:
            if self._start_point is None or (self._start_point and self._end_point):
                self._end_point = None
                if self._snap_point:
                    self._start_point = self._snap_point
                else:
                    self._start_point = e.mapPoint()
            else:
                if self._snap_point:
                    self._end_point = self._snap_point
                else:
                    self._end_point = e.mapPoint()
                self.draw_los()
                self.addLoSStatusChanged.emit(True)

    def canvasMoveEvent(self, event: QgsMapMouseEvent) -> None:
        super().canvasMoveEvent(event)

        if self._start_point is not None:
            if self._snap_point:
                self._direction_point = self._snap_point
            else:
                self._direction_point = event.mapPoint()
            self.draw_los()

    def draw_los(self):

        if not self.canvas_crs_is_projected():
            return

        point: QgsPointXY = None
        if self._end_point:
            point = self._end_point
        elif self._direction_point:
            point = self._direction_point

        if self._start_point and point:
            self._los_rubber_band.hide()

            rasters_extent = self._raster_list.extent_polygon()

            if self._widget.los_local or self._widget.los_global:
                line = QgsGeometry.fromPolylineXY([self._start_point, point])

                if self._widget.los_global:

                    if self._start_point.distance(point) > 0:
                        line = line.extendLine(
                            0,
                            self._raster_list.maximal_diagonal_size(),
                        )

                        # insert target point
                        line.get().insertVertex(
                            QgsVertexId(0, 0, 1),
                            QgsPoint(point.x(), point.y()),
                        )

                line = line.intersection(rasters_extent)

                self._los_rubber_band.setToGeometry(line, self.canvas().mapSettings().destinationCrs())

    def prepare_task(self) -> QgsTask:
        task = PrepareLoSTask(
            self._los_rubber_band.asGeometry(),
            self._widget.sampling_distance.inUnits(self._los_layer.crs().mapUnits()),
            self._los_layer,
            self._raster_list,
            self._widget.observer_offset,
            self._widget.target_offset,
            self._widget.los_global,
            self._iface.mapCanvas().mapSettings().destinationCrs(),
        )
        return task

    def add_los_to_layer(self) -> None:
        geom = self._los_rubber_band.asGeometry()
        if geom.get().partCount() != 1:
            return
        super().add_los_to_layer()
