from functools import partial

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
        self._widget.valuesChanged.connect(partial(self.draw_los, None))
        super().create_widget()

    def clean(self) -> None:
        super().clean()
        if self._widget:
            self._widget.setAddLoSEnabled(False)

    def canvasReleaseEvent(self, event: QgsMapMouseEvent) -> None:
        if event.button() == Qt.RightButton and self._start_point is None and self._los_rubber_band.size() == 0:
            self.deactivate()
        if event.button() == Qt.RightButton:
            self.clean()
        elif event.button() == Qt.LeftButton:
            if self._start_point is None:
                if self._snap_point:
                    self._start_point = self._snap_point
                else:
                    self._start_point = event.mapPoint()
            else:
                if self._snap_point:
                    self._end_point = self._snap_point
                else:
                    self._end_point = event.mapPoint()
                self.draw_los()
                self.addLoSStatusChanged.emit(True)
                self._start_point = None
                self._end_point = None

    def canvasMoveEvent(self, event: QgsMapMouseEvent) -> None:
        super().canvasMoveEvent(event)

        if self._start_point is not None:
            if self._snap_point:
                self._direction_point = self._snap_point
            else:
                self._direction_point = event.mapPoint()
            self.draw_los()

    def draw_los(self, towards_point: QgsPointXY):
        if towards_point is None:
            towards_point = self._last_towards_point

        if not self.canvas_crs_is_projected():
            return

        if self._start_point and towards_point:
            self._los_rubber_band.hide()

            rasters_extent = self._raster_list.extent_polygon()

            if self._widget.los_local or self._widget.los_global:
                if self._widget.los_local:
                    line = QgsGeometry.fromPolylineXY([self._start_point, towards_point])

                if self._widget.los_global:
                    line = QgsGeometry.fromPolylineXY([self._start_point, towards_point])

                    if self._start_point.distance(towards_point) > 0:
                        line = line.extendLine(
                            0,
                            self._raster_list.maximal_diagonal_size(),
                        )

                        # insert target point
                        line.get().insertVertex(
                            QgsVertexId(0, 0, 1),
                            QgsPoint(towards_point.x(), towards_point.y()),
                        )

                line = line.intersection(rasters_extent)

                self._los_rubber_band.setToGeometry(line, self._canvas.mapSettings().destinationCrs())

        if towards_point:
            self._last_towards_point = QgsPointXY(towards_point.x(), towards_point.y())

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
