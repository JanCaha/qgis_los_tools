from __future__ import annotations

import copy
import math
from typing import List, Optional, Union

from qgis.core import QgsFeature, QgsGeometry, QgsPoint

from los_tools.constants.field_names import FieldNames
from los_tools.processing.tools.util_functions import calculate_distance, line_geometry_to_coords


class PointOnLoS:
    def __init__(self, x: float, y: float, distance: float, z: float, vertical_angle: float):
        self.x = x
        self.y = y
        self.distance = distance
        self.z = z
        self.vertical_angle = vertical_angle


class LoS:

    def __init__(
        self,
        line: QgsGeometry,
        is_global: bool = False,
        is_without_target: bool = False,
        observer_offset: float = 0,
        target_offset: float = 0,
        target_x: float = None,
        target_y: float = None,
        use_curvature_corrections: bool = True,
        refraction_coefficient: float = 0.13,
    ):
        points = line_geometry_to_coords(line)
        self.is_global: bool = is_global
        self.is_without_target: bool = is_without_target
        self.use_curvature_corrections: bool = use_curvature_corrections
        self.refraction_coefficient: float = refraction_coefficient
        self.observer_offset: float = observer_offset
        self.target_offset: float = target_offset
        self.target_x: float = target_x
        self.target_y: float = target_y
        self.target_index: int = None
        self.global_horizon_index = None

        self.points: List[PointOnLoS] = [None for x in range(len(points))]
        self.previous_max_angle: List = []
        self.visible: List = []
        self.horizon: List = []

        self.__parse_points(points)

        self.__identify_horizons()

        if self.is_global:
            self.limit_angle = self.points[self.target_index].vertical_angle
            self.is_visible = True

    def __identify_horizons(self) -> None:
        for i in range(0, len(self.points)):
            if i == len(self.points) - 1:
                self.horizon.append(False)
            else:
                self.horizon.append((self.visible[i] is True) and (self.visible[i + 1] is False))

    def __parse_points(self, points: List[List[float]]) -> None:
        max_angle_temp = -180.0

        first_point_x = points[0][0]
        first_point_y = points[0][1]
        first_point_z = points[0][2] + self.observer_offset

        target_distance = 0.0
        sampling_distance = 1.0
        target_offset = 0.0

        if self.is_global:
            target_distance = calculate_distance(first_point_x, first_point_y, self.target_x, self.target_y)
            sampling_distance = calculate_distance(points[0][0], points[0][1], points[1][0], points[1][1])

        for i, point in enumerate(points):
            point_x = point[0]
            point_y = point[1]
            point_z = point[2]

            distance = calculate_distance(first_point_x, first_point_y, point_x, point_y)

            if self.use_curvature_corrections:
                point_z = self._curvature_corrections(point_z, distance, self.refraction_coefficient)
                target_offset = self._curvature_corrections(self.target_offset, distance, self.refraction_coefficient)

            # first point
            if i == 0:
                self.points[i] = PointOnLoS(point_x, point_y, 0, first_point_z, -90)

            # target point global los
            elif self.is_global and math.fabs(target_distance - distance) < sampling_distance / 2:
                self.points[i] = PointOnLoS(
                    point_x,
                    point_y,
                    distance,
                    point_z + target_offset,
                    self._angle_vertical(distance, point_z + target_offset - first_point_z),
                )

                self.target_index = i

            # target point local los
            elif not self.is_global and not self.is_without_target and i == len(points) - 1:
                self.points[i] = PointOnLoS(
                    point_x,
                    point_y,
                    distance,
                    point_z + target_offset,
                    self._angle_vertical(distance, point_z + target_offset - first_point_z),
                )

            # points
            else:
                self.points[i] = PointOnLoS(
                    point_x,
                    point_y,
                    distance,
                    point_z,
                    self._angle_vertical(distance, point_z - first_point_z),
                )

            # first store max angle before this point and then add new max angle
            self.previous_max_angle.append(max_angle_temp)

            if i != 0:
                if max_angle_temp < self._angle_vertical(distance, point_z - first_point_z):
                    if self.is_global and i == self.target_index:
                        pass
                    else:
                        max_angle_temp = self._angle_vertical(distance, point_z - first_point_z)

            # is visible is only valid if previous_max_angle is smaller then current angle
            if i == 0:
                self.visible.append(True)
            else:
                self.visible.append(self.previous_max_angle[i] < self.points[i].vertical_angle)

    def __str__(self):
        string = ""
        for i, point in enumerate(self.points):
            string += (
                f"{i} - {point.distance} {point.z} {point.vertical_angle} "
                f"(prev. {self.previous_max_angle[i]}) - vis. {self.visible[i]} hor. {self.horizon[i]} \n"
            )
        return string

    @staticmethod
    def _angle_vertical(distance: float, elev_diff: float) -> float:
        return 90 if distance == 0 else math.degrees(math.atan(elev_diff / distance))

    @staticmethod
    def _curvature_corrections(elev: float, dist: float, ref_coeff: float, earth_diameter: float = 12740000) -> float:
        return elev - (math.pow(dist, 2) / earth_diameter) + ref_coeff * (math.pow(dist, 2) / earth_diameter)

    def is_visible_at_index(self, index: int, return_integer: bool = False) -> Union[bool, int]:
        return int(self.visible[index]) if return_integer else self.visible[index]

    def get_geom_at_index(self, index: int) -> QgsPoint:
        if index == -1:
            index = 0
        point = QgsPoint(
            self.points[index].x,
            self.points[index].y,
            self.points[index].z,
        )
        return point

    def get_horizons(self) -> List[QgsPoint]:
        points: List[QgsPoint] = []

        for i, horizon in enumerate(self.horizon):
            if horizon:
                points.append(self.get_geom_at_index(i))

        return points

    def _get_global_horizon_index(self) -> Optional[int]:
        if self.global_horizon_index is None:
            for i in range(len(self.points) - 1, -1, -1):
                if self.horizon[i]:
                    self.global_horizon_index = i  # type: ignore
                    break

        return self.global_horizon_index

    def get_global_horizon(self) -> QgsPoint:
        index = self._get_global_horizon_index()

        if index is None:
            index = -1

        return self.get_geom_at_index(index)

    def get_global_horizon_distance(self) -> float:
        index = self._get_global_horizon_index()

        if index is not None:
            return self.points[index].distance
        else:
            return 0

    def get_global_horizon_angle(self) -> float:
        index = self._get_global_horizon_index()

        if index is not None:
            return self.points[index].vertical_angle
        else:
            return 90

    def get_angle_difference_global_horizon_at_point(self, index_point: int) -> float:
        horizon_angle = -90.0
        global_horizon_index = self._get_global_horizon_index()
        if global_horizon_index:
            horizon_angle = self.points[global_horizon_index].vertical_angle

        return self.points[index_point].vertical_angle - horizon_angle

    def get_elevation_difference_global_horizon_at_point(self, index_point: int) -> float:
        global_horizon_index = self._get_global_horizon_index()
        if global_horizon_index:
            elev_difference_horizon = self.points[index_point].z - (
                self.points[0].z
                + math.tan(math.radians(self.points[global_horizon_index].vertical_angle))
                * self.points[index_point].distance
            )
            return elev_difference_horizon

        return self.points[index_point].z

    def __get_previous_horizon_index(self, index_point: int) -> Optional[int]:
        index = None

        for i in range(index_point - 1, -1, -1):
            if self.horizon[i]:
                index = i
                break

        return index

    def get_angle_difference_horizon_at_point(self, index_point: int) -> float:
        if 1 < index_point:
            horizon_index = self.__get_previous_horizon_index(index_point)

            if horizon_index:
                horizon_angle = self.points[index_point].vertical_angle - self.points[horizon_index].vertical_angle
            else:
                horizon_angle = self.points[index_point].vertical_angle
        else:
            horizon_angle = -90.0

        return horizon_angle

    def get_elevation_difference_horizon_at_point(self, index_point: int) -> float:
        if 1 < index_point:
            horizon_index = self.__get_previous_horizon_index(index_point)

            if horizon_index is not None:
                elev_difference_horizon = self.points[index_point].z - (
                    self.points[0].z
                    + math.tan(math.radians(self.points[horizon_index].vertical_angle))
                    * self.points[index_point].distance
                )
            else:
                elev_difference_horizon = self.points[index_point].z - self.points[0].z
        else:
            elev_difference_horizon = 0

        return elev_difference_horizon


class LoSLocal(LoS):
    def __init__(
        self,
        line: QgsGeometry,
        observer_offset: float = 0,
        target_offset: float = 0,
        use_curvature_corrections: bool = True,
        refraction_coefficient: float = 0.13,
    ):
        super().__init__(
            line,
            observer_offset=observer_offset,
            target_offset=target_offset,
            use_curvature_corrections=use_curvature_corrections,
            refraction_coefficient=refraction_coefficient,
        )

        self.target_angle = self.points[-1].vertical_angle
        self.highest_local_horizon_index = None

    @classmethod
    def from_feature(
        cls,
        feature: QgsFeature,
        curvature_corrections: bool = True,
        refraction_coefficient: float = 0.13,
    ) -> LoSLocal:
        return cls(
            feature.geometry(),
            observer_offset=feature.attribute(FieldNames.OBSERVER_OFFSET),
            target_offset=feature.attribute(FieldNames.TARGET_OFFSET),
            use_curvature_corrections=curvature_corrections,
            refraction_coefficient=refraction_coefficient,
        )

    def is_target_visible(self, return_integer: bool = False):
        return self.is_visible_at_index(index=-1, return_integer=return_integer)

    def get_view_angle(self) -> float:
        return self.target_angle

    def get_elevation_difference(self) -> float:
        return self.points[0].z - self.points[-1].z

    def get_angle_difference_local_horizon(self) -> float:
        max_local_horizon_index = self._get_max_local_horizon_index()
        if max_local_horizon_index:
            return self.target_angle - self.points[max_local_horizon_index].vertical_angle
        return self.target_angle - self.points[0].vertical_angle

    def get_elevation_difference_local_horizon(self) -> float:
        local_horizon_index = self._get_max_local_horizon_index()
        if local_horizon_index:
            return (
                self.points[-1].z
                - self.points[0].z
                - math.tan(math.radians(self.points[local_horizon_index].vertical_angle)) * self.points[-1].distance
            )

        return self.points[-1].z - self.points[0].z

    def get_los_slope_difference(self) -> float:
        los_slope = math.degrees(
            math.atan((self.points[-1].z - self.points[-2].z) / (self.points[-1].distance - self.points[-2].distance))
        )
        return los_slope - self.target_angle

    def get_local_horizon_distance(self) -> float:
        max_local_horizon_index = self._get_max_local_horizon_index()
        if max_local_horizon_index:
            return self.points[max_local_horizon_index].distance
        return self.points[-1].distance

    def get_local_horizon_count(self) -> int:
        return int(math.fsum(self.horizon))

    def get_fuzzy_visibility(
        self,
        object_size: float = 10,
        recognition_acuinty: float = 0.017,
        clear_visibility_distance: float = 500,
    ) -> float:
        b1 = clear_visibility_distance
        h = object_size
        beta = recognition_acuinty

        b2 = h / (2 * math.tan(beta / 2))

        if self.points[-1].distance < b1:
            return 1
        else:
            return 1 / (1 + math.pow((self.points[-1].distance - b1) / b2, 2))

    def _get_max_local_horizon_index(self) -> Optional[int]:
        index = None

        for i in range(len(self.points) - 1, -1, -1):
            if self.horizon[i]:
                index = i
                break

        return index

    def get_max_local_horizon(self) -> QgsPoint:
        index = self._get_max_local_horizon_index()

        if index is None:
            index = self.target_index

        return self.get_geom_at_index(index)


class LoSGlobal(LoS):
    def __init__(
        self,
        line: QgsGeometry,
        observer_offset: float = 0,
        target_offset: float = 0,
        target_x: float = 0,
        target_y: float = 0,
        use_curvature_corrections: bool = True,
        refraction_coefficient: float = 0.13,
    ):
        super().__init__(
            line,
            is_global=True,
            observer_offset=observer_offset,
            target_offset=target_offset,
            target_x=target_x,
            target_y=target_y,
            use_curvature_corrections=use_curvature_corrections,
            refraction_coefficient=refraction_coefficient,
        )

        self.global_horizon_index = None

    @classmethod
    def from_feature(
        cls,
        feature: QgsFeature,
        curvature_corrections: bool = True,
        refraction_coefficient: float = 0.13,
    ) -> LoSGlobal:
        return cls(
            feature.geometry(),
            observer_offset=feature.attribute(FieldNames.OBSERVER_OFFSET),
            target_offset=feature.attribute(FieldNames.TARGET_OFFSET),
            target_x=feature.attribute(FieldNames.TARGET_X),
            target_y=feature.attribute(FieldNames.TARGET_Y),
            use_curvature_corrections=curvature_corrections,
            refraction_coefficient=refraction_coefficient,
        )

    def is_target_visible(self, return_integer: bool = False) -> Union[bool, int]:
        return self.is_visible_at_index(index=self.target_index, return_integer=return_integer)

    def _get_global_horizon_index(self) -> int:
        if self.global_horizon_index is not None:
            return self.global_horizon_index
        else:
            horizon_index = 0
            for i in range(1, len(self.points) - 1):
                if self.horizon[i] and i != self.target_index:
                    horizon_index = i
            self.global_horizon_index = horizon_index  # type: ignore
            return self.global_horizon_index

    def get_angle_difference_global_horizon(self) -> float:
        horizon_angle = -90.0
        global_horizon_index = self._get_global_horizon_index()
        if global_horizon_index:
            horizon_angle = self.points[global_horizon_index].vertical_angle
        return self.points[self.target_index].vertical_angle - horizon_angle

    def get_elevation_difference_global_horizon(self) -> float:
        global_horizon_index = self._get_global_horizon_index()
        if global_horizon_index:
            elev_difference_horizon = self.points[self.target_index].z - (
                self.points[0].z
                + math.tan(math.radians(self.points[global_horizon_index].vertical_angle))
                * self.points[self.target_index].distance
            )
        else:
            elev_difference_horizon = self.points[self.target_index].z - self.points[0].z

        return elev_difference_horizon

    def get_horizon_distance(self) -> float:
        return self.points[self._get_global_horizon_index()].distance

    def get_horizon_count(self) -> int:
        return int(math.fsum(self.horizon[self.target_index + 1 :]))

    def _get_max_local_horizon_index(self) -> Optional[int]:
        index = None

        for i in range(self.target_index - 1, -1, -1):
            if self.horizon[i] and i != self.target_index:
                index = i
                break

        return index

    def get_max_local_horizon(self) -> QgsPoint:
        index = self._get_max_local_horizon_index()

        if index is None:
            index = self.target_index

        return self.get_geom_at_index(index)


class LoSWithoutTarget(LoS):
    def __init__(
        self,
        line: QgsGeometry,
        observer_offset: float = 0,
        use_curvature_corrections: bool = True,
        refraction_coefficient: float = 0.13,
    ):
        super().__init__(
            line,
            is_without_target=True,
            observer_offset=observer_offset,
            use_curvature_corrections=use_curvature_corrections,
            refraction_coefficient=refraction_coefficient,
        )

    @classmethod
    def from_feature(
        cls,
        feature: QgsFeature,
        curvature_corrections: bool = True,
        refraction_coefficient: float = 0.13,
    ) -> LoSWithoutTarget:
        return cls(
            feature.geometry(),
            observer_offset=feature.attribute(FieldNames.OBSERVER_OFFSET),
            use_curvature_corrections=curvature_corrections,
            refraction_coefficient=refraction_coefficient,
        )

    @classmethod
    def from_another(
        cls,
        other: LoSWithoutTarget,
        distance_limit: Optional[float] = None,
    ) -> LoSWithoutTarget:
        obj = LoSWithoutTarget.__new__(LoSWithoutTarget)
        obj.observer_offset = other.observer_offset
        obj.use_curvature_corrections = other.use_curvature_corrections
        obj.refraction_coefficient = other.refraction_coefficient
        obj.is_global = False
        obj.is_without_target = True
        obj.target_offset = 0
        obj.target_x = None
        obj.target_y = None
        obj.target_index = None
        obj.global_horizon_index = None

        if distance_limit is None:
            obj.points = copy.deepcopy(other.points)
            obj.previous_max_angle = copy.deepcopy(other.previous_max_angle)
            obj.visible = copy.deepcopy(other.visible)
            obj.horizon = copy.deepcopy(other.horizon)
        else:
            index_limit = other._get_distance_limit_index(distance_limit)
            obj.points = copy.deepcopy(other.points[:index_limit])
            obj.previous_max_angle = copy.deepcopy(other.previous_max_angle[:index_limit])
            obj.visible = copy.deepcopy(other.visible[:index_limit])
            obj.horizon = copy.deepcopy(other.horizon[:index_limit])

        return obj

    def get_horizontal_angle(self) -> float:
        azimuth = QgsPoint(self.points[0].x, self.points[0].y).azimuth(QgsPoint(self.points[-1].x, self.points[-1].y))

        return azimuth

    def get_maximal_vertical_angle(self) -> float:
        angles = [row.vertical_angle for row in self.points]
        return max(angles)

    def __get_max_local_horizon_index(self) -> Optional[int]:
        index_horizon = None
        global_horizon_index = self._get_global_horizon_index()
        if global_horizon_index:
            for i in range(global_horizon_index - 1, -1, -1):
                if self.horizon[i]:
                    index_horizon = i
                    break

        return index_horizon

    def get_max_local_horizon_angle(self) -> float:
        index_horizon = self.__get_max_local_horizon_index()

        if index_horizon is not None:
            return self.points[index_horizon].vertical_angle
        else:
            return -90

    def get_max_local_horizon_distance(self) -> float:
        index_horizon = self.__get_max_local_horizon_index()

        if index_horizon is not None:
            return self.points[index_horizon].distance
        else:
            return 0

    def get_max_local_horizon(self, direction_point=False) -> QgsPoint:
        index = self.__get_max_local_horizon_index()

        if index is None:
            # if we want to extract direction from horizon we cannot have observer returned
            if direction_point:
                index = 1
            else:
                index = 0

        return self.get_geom_at_index(index)

    def get_global_horizon_angle_difference(self) -> Optional[float]:
        global_horizon_index = self._get_global_horizon_index()
        local_horizon_index = self.__get_max_local_horizon_index()

        if global_horizon_index is not None and local_horizon_index is not None:
            return self.points[global_horizon_index].vertical_angle - self.points[local_horizon_index].vertical_angle
        else:
            return None

    def get_global_horizon_elevation_difference(self) -> Optional[float]:
        global_horizon_index = self._get_global_horizon_index()
        local_horizon_index = self.__get_max_local_horizon_index()

        if global_horizon_index is not None and local_horizon_index is not None:
            return (
                self.points[global_horizon_index].z
                - math.tan(math.radians(self.points[local_horizon_index].vertical_angle))
                * self.points[global_horizon_index].distance
            )

        else:
            return None

    def _get_distance_limit_index(self, distance: float) -> int:
        index = len(self.points) - 1

        for i in range(1, len(self.points)):
            if self.points[i].distance > distance:
                index = i
                break

        return index
