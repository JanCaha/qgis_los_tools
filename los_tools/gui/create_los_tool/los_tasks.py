from typing import Union

from qgis.core import (
    QgsCoordinateReferenceSystem,
    QgsCoordinateTransform,
    QgsFeature,
    QgsGeometry,
    QgsProject,
    QgsTask,
    QgsTaskManager,
    QgsVectorLayer,
    QgsVertexId,
)
from qgis.PyQt.QtCore import pyqtSignal

from los_tools.classes.list_raster import ListOfRasters
from los_tools.classes.sampling_distance_matrix import SamplingDistanceMatrix
from los_tools.constants.field_names import FieldNames
from los_tools.constants.names_constants import NamesConstants
from los_tools.processing.tools.util_functions import segmentize_los_line


class AbstractPrepareLoSTask(QgsTask):
    taskFinishedTime = pyqtSignal(int)

    def __init__(
        self,
        los_geometry: QgsGeometry,
        los_layer: QgsVectorLayer,
        list_of_rasters: ListOfRasters,
        observer_offset: float,
        canvas_crs: QgsCoordinateReferenceSystem,
        description: str,
        flags: Union[QgsTask.Flags, QgsTask.Flag] = QgsTask.Flag.CanCancel,
    ) -> None:
        super().__init__(description, flags)

        self.los_geometry = los_geometry
        self.list_of_rasters = list_of_rasters
        self.los_layer = los_layer
        self.observer_offset = observer_offset
        self.canvas_crs = canvas_crs

        self.fields = self.los_layer.fields()

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

        self.ct_to_raster = QgsCoordinateTransform(self.canvas_crs, self.list_of_rasters.crs(), QgsProject.instance())

        self.ct_to_layer = QgsCoordinateTransform(
            self.list_of_rasters.crs(), self.los_layer.crs(), QgsProject.instance()
        )

        self.feature_template = QgsFeature(self.fields)


class PrepareLoSWithoutTargetTask(AbstractPrepareLoSTask):

    def __init__(
        self,
        los_geometry: QgsGeometry,
        los_layer: QgsVectorLayer,
        list_of_rasters: ListOfRasters,
        sampling_distance_matrix: SamplingDistanceMatrix,
        observer_offset: float,
        angle_step: float,
        canvas_crs: QgsCoordinateReferenceSystem,
        description: str = "Prepare LoS without Target",
        flags: Union["QgsTask.Flags", "QgsTask.Flag"] = QgsTask.Flag.CanCancel,
    ) -> None:
        super().__init__(los_geometry, los_layer, list_of_rasters, observer_offset, canvas_crs, description, flags)

        self.sampling_distance_matrix = sampling_distance_matrix
        self.sampling_distance_matrix.replace_minus_one_with_value(list_of_rasters.maximal_diagonal_size())

        self.angle_step = angle_step

    def run(self):
        number_of_lines = self.los_geometry.get().partCount()

        partsIterator = self.los_geometry.get().parts()

        j = 1
        while partsIterator.hasNext():
            geom = partsIterator.next()

            observer_point = geom.vertexAt(QgsVertexId(0, 0, 0))

            line = self.sampling_distance_matrix.build_line(observer_point, geom.vertexAt(QgsVertexId(0, 0, 1)))

            line.transform(self.ct_to_raster)

            line = self.list_of_rasters.add_z_values(line.points())

            line.transform(self.ct_to_layer)

            f = QgsFeature(self.feature_template)

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

        self.taskFinishedTime.emit(self.elapsedTime())

        return True


class PrepareLoSTask(AbstractPrepareLoSTask):

    def __init__(
        self,
        los_geometry: QgsGeometry,
        segment_length: float,
        los_layer: QgsVectorLayer,
        list_of_rasters: ListOfRasters,
        observer_offset: float,
        target_offset: float,
        los_global: bool,
        canvas_crs: QgsCoordinateReferenceSystem,
        description: str = "Prepare LoS without Target",
        flags: Union["QgsTask.Flags", "QgsTask.Flag"] = QgsTask.Flag.CanCancel,
    ) -> None:
        super().__init__(los_geometry, los_layer, list_of_rasters, observer_offset, canvas_crs, description, flags)

        self.segment_length = segment_length

        self.target_offset = target_offset
        self.los_global = los_global

    def run(self):
        line = segmentize_los_line(self.los_geometry, self.segment_length)

        line.transform(self.ct_to_raster)

        line = self.list_of_rasters.add_z_values(line.points())

        line.transform(self.ct_to_layer)

        f = QgsFeature(self.feature_template)

        f.setGeometry(line)
        f.setAttribute(f.fieldNameIndex(FieldNames.ID_OBSERVER), int(self.observer_max_id + 1))
        f.setAttribute(f.fieldNameIndex(FieldNames.ID_TARGET), int(self.target_max_id + 1))
        f.setAttribute(f.fieldNameIndex(FieldNames.OBSERVER_OFFSET), float(self.observer_offset))
        f.setAttribute(f.fieldNameIndex(FieldNames.TARGET_OFFSET), float(self.target_offset))

        if self.los_global:
            f.setAttribute(
                f.fieldNameIndex(FieldNames.TARGET_X),
                float(self.los_geometry.vertexAt(1).x()),
            )
            f.setAttribute(
                f.fieldNameIndex(FieldNames.TARGET_Y),
                float(self.los_geometry.vertexAt(1).y()),
            )
            f.setAttribute(f.fieldNameIndex(FieldNames.LOS_TYPE), NamesConstants.LOS_GLOBAL)
        else:
            f.setAttribute(f.fieldNameIndex(FieldNames.LOS_TYPE), NamesConstants.LOS_LOCAL)

        self.los_layer.dataProvider().addFeature(f)

        self.taskFinishedTime.emit(self.elapsedTime())

        return True


class LoSExtractionTaskManager(QgsTaskManager):
    def active_los_tasks(self) -> int:
        count = 0
        for task in self.tasks():
            if task.description().startswith("Prepare LoS"):
                count += 1
        return count

    def all_los_tasks_finished(self) -> bool:
        return self.active_los_tasks() == 0
