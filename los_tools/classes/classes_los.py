import math
from typing import List, Union

from qgis.core import (QgsPoint)

from los_tools.tools.util_functions import calculate_distance


class LoS:

    X = 0
    Y = 1
    Z = 3
    DISTANCE = 2
    VERTICAL_ANGLE = 4

    def __init__(self,
                 points: List[List[float]],
                 is_global: bool = False,
                 is_without_target: bool = False,
                 observer_offset: float = 0,
                 target_offset: float = 0,
                 target_x: float = None,
                 target_y: float = None,
                 sampling_distance: float = None,
                 use_curvature_corrections: bool = True,
                 refraction_coefficient: float = 0.13):

        self.is_global: bool = is_global
        self.is_without_target: bool = is_without_target
        self.use_curvature_corrections: bool = use_curvature_corrections
        self.refraction_coefficient: float = refraction_coefficient
        self.observer_offset: float = observer_offset
        self.target_offset: float = target_offset
        self.target_x: float = target_x
        self.target_y: float = target_y
        self.target_index: int = None

        if sampling_distance is None:
            sampling_distance = calculate_distance(points[0][0], points[0][1], points[1][0], points[1][1])

        self.points: List = []
        self.previous_max_angle: List = []
        self.visible: List = []
        self.horizon: List = []

        self.__parse_points(points,
                            sampling_distance=sampling_distance)

        self.__identify_horizons()

        if self.is_global:
            self.limit_angle = self.points[self.target_index][4]
            self.is_visible = True

    def __identify_horizons(self) -> None:

        for i in range(0, len(self.points)):
            if i == len(self.points) - 1:
                self.horizon.append(False)
            else:
                self.horizon.append((self.visible[i] is True) and (self.visible[i+1] is False))

    def __parse_points(self,
                       points: List[List[float]],
                       sampling_distance: float) -> None:

        max_angle_temp = -180

        first_point_x = points[0][0]
        first_point_y = points[0][1]
        first_point_z = points[0][2] + self.observer_offset

        if self.is_global:
            target_distance = calculate_distance(first_point_x, first_point_y,
                                                 self.target_x, self.target_y)

        for i in range(0, len(points)):
            point_x = points[i][0]
            point_y = points[i][1]
            point_z = points[i][2]

            distance = calculate_distance(first_point_x, first_point_y, point_x, point_y)

            if self.use_curvature_corrections:
                point_z = self._curvature_corrections(point_z,
                                                      distance,
                                                      self.refraction_coefficient)
                target_offset = self._curvature_corrections(self.target_offset,
                                                            distance,
                                                            self.refraction_coefficient)

            if i == 0:
                self.points.append([point_x, point_y, 0, first_point_z, -90])
            elif self.is_global and math.fabs(target_distance - distance) < sampling_distance / 2:
                self.points.append(
                    [point_x, point_y, distance, point_z + target_offset,
                     self._angle_vertical(distance, point_z + target_offset - first_point_z)])
                self.target_index = i
            elif not self.is_global and not self.is_without_target and i == len(points)-1:
                self.points.append(
                    [point_x, point_y, distance, point_z + target_offset,
                     self._angle_vertical(distance, point_z + target_offset - first_point_z)])
            else:
                self.points.append([point_x, point_y, distance, point_z,
                                    self._angle_vertical(distance, point_z - first_point_z)])

            # first store max angle before this point and then add new max angle
            self.previous_max_angle.append(max_angle_temp)

            if max_angle_temp < self.points[-1][self.VERTICAL_ANGLE]:
                if self.is_global:
                    if i != self.target_index:
                        max_angle_temp = self.points[-1][self.VERTICAL_ANGLE]
                else:
                    max_angle_temp = self.points[-1][self.VERTICAL_ANGLE]

            # is visible is only valid if previous_max_angle is smaller then current angle
            if i == 0:
                self.visible.append(True)
            else:
                self.visible.append(self.previous_max_angle[i] < self.points[-1][self.VERTICAL_ANGLE])

    def __str__(self):

        string = ""
        for i in range(0, len(self.points)):
            string += ("{} - {} {} {} (prev. {}) - vis. {} hor. {} \n".format(
                i,
                self.points[i][self.DISTANCE],
                self.points[i][self.Z],
                self.points[i][self.VERTICAL_ANGLE],
                self.previous_max_angle[i],
                self.visible[i],
                self.horizon[i]
            ))
        return string

    @staticmethod
    def _angle_vertical(distance: float,
                        elev_diff: float) -> float:

        return 90 if distance == 0 else math.degrees(math.atan(elev_diff / distance))

    @staticmethod
    def _curvature_corrections(elev: float,
                               dist: float,
                               ref_coeff: float,
                               earth_diameter: float = 12740000) -> float:

        return elev - (math.pow(dist, 2) / earth_diameter) + ref_coeff * (math.pow(dist, 2) / earth_diameter)

    def is_visible_at_index(self, index: int, return_integer: bool = False) -> Union[bool, int]:

        return int(self.visible[index]) if return_integer else self.visible[index]

    def get_geom_at_index(self, index: int) -> QgsPoint:

        point = QgsPoint(self.points[index][self.X],
                         self.points[index][self.Y],
                         self.points[index][self.Z])
        return point

    def get_horizons(self) -> List[QgsPoint]:

        points: List[QgsPoint] = []

        for i in range(0, len(self.horizon)):
            if self.horizon[i]:
                points.append(self.get_geom_at_index(i))

        return points


class LoSLocal(LoS):

    def __init__(self,
                 points: list,
                 observer_offset: float = 0,
                 target_offset: float = 0,
                 sampling_distance: float = None,
                 use_curvature_corrections: bool = True,
                 refraction_coefficient: float = 0.13):

        super().__init__(points,
                         observer_offset=observer_offset,
                         target_offset=target_offset,
                         sampling_distance=sampling_distance,
                         use_curvature_corrections=use_curvature_corrections,
                         refraction_coefficient=refraction_coefficient)

        self.target_angle = self.points[-1][self.VERTICAL_ANGLE]
        self.highest_local_horizon_index = None

    def is_target_visible(self, return_integer: bool = False):

        return self.is_visible_at_index(index=-1, return_integer=return_integer)

    def get_view_angle(self) -> float:

        return self.target_angle

    def get_elevation_difference(self) -> float:

        return self.points[0][self.Z] - self.points[-1][self.Z]

    def get_max_local_horizon(self) -> QgsPoint:

        index = self._get_max_local_horizon_index()

        if index is None:
            index = 0

        return self.get_geom_at_index(index)

    def get_angle_difference_local_horizon(self) -> float:

        return self.target_angle - self.points[self._get_max_local_horizon_index()][self.VERTICAL_ANGLE]

    def get_elevation_difference_local_horizon(self) -> float:

        return self.points[-1][self.Z] - self.points[0][self.Z] - \
               math.tan(math.radians(self.points[self._get_max_local_horizon_index()][self.VERTICAL_ANGLE])) * \
               self.points[-1][self.DISTANCE]

    def get_los_slope_difference(self) -> float:

        los_slope = math.degrees(math.atan((self.points[-1][self.Z] - self.points[-2][self.Z]) /
                                           (self.points[-1][self.DISTANCE] - self.points[-2][self.DISTANCE])))
        return los_slope - self.target_angle

    def get_local_horizon_distance(self) -> float:

        return self.points[self._get_max_local_horizon_index()][self.DISTANCE]

    def get_local_horizon_count(self) -> int:

        return math.fsum(self.horizon)

    def get_fuzzy_visibility(self,
                             object_size: float = 10,
                             recognition_acuinty: float = 0.017,
                             clear_visibility_distance: float = 500) -> float:

        b1 = clear_visibility_distance
        h = object_size
        beta = recognition_acuinty

        b2 = h / (2 * math.tan(beta / 2))

        if self.points[-1][2] < b1:
            return 1
        else:
            return 1 / (1 + math.pow((self.points[-1][self.DISTANCE] - b1) / b2, 2))

    def _get_max_local_horizon_index(self) -> int:

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

    def __init__(self,
                 points: list,
                 observer_offset: float = 0,
                 target_offset: float = 0,
                 target_x: float = 0,
                 target_y: float = 0,
                 sampling_distance: float = None,
                 use_curvature_corrections: bool = True,
                 refraction_coefficient: float = 0.13):

        super().__init__(points,
                         is_global=True,
                         observer_offset=observer_offset,
                         target_offset=target_offset,
                         target_x=target_x,
                         target_y=target_y,
                         sampling_distance=sampling_distance,
                         use_curvature_corrections=use_curvature_corrections,
                         refraction_coefficient=refraction_coefficient)

        self.global_horizon_index = None

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
            self.global_horizon_index = horizon_index
            return self.global_horizon_index

    def get_angle_difference_global_horizon(self) -> float:

        horizon_angle = -90
        if self._get_global_horizon_index() != 0:
            horizon_angle = self.points[self._get_global_horizon_index()][self.VERTICAL_ANGLE]
        return self.points[self.target_index][self.VERTICAL_ANGLE] - horizon_angle

    def get_elevation_difference_global_horizon(self) -> float:

        elev_difference_horizon = self.points[self.target_index][self.Z] - (
                self.points[0][self.Z] +
                math.tan(math.radians(self.points[self._get_global_horizon_index()][self.VERTICAL_ANGLE])) *
                self.points[self.target_index][self.Z])
        return elev_difference_horizon

    def get_horizon_distance(self) -> float:

        return self.points[self._get_global_horizon_index()][self.DISTANCE]

    def get_horizon_count(self) -> int:

        return int(math.fsum(self.horizon[self.target_index+1:]))

    def __get_global_horizon_index(self) -> int:

        index = None

        for i in range(len(self.points) - 1, -1, -1):
            if self.horizon[i]:
                index = i
                break

        return index

    def get_global_horizon(self) -> QgsPoint:

        index = self.__get_global_horizon_index()

        if index is None:
            index = -1

        return self.get_geom_at_index(index)

    def _get_max_local_horizon_index(self) -> int:

        index = None

        for i in range(self.target_index-1, -1, -1):
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

    def __init__(self,
                 points: list,
                 observer_offset: float = 0,
                 sampling_distance: float = None,
                 use_curvature_corrections: bool = True,
                 refraction_coefficient: float = 0.13):

        super().__init__(points=points,
                         is_without_target=True,
                         observer_offset=observer_offset,
                         sampling_distance=sampling_distance,
                         use_curvature_corrections=use_curvature_corrections,
                         refraction_coefficient=refraction_coefficient)

    def get_horizontal_angle(self) -> float:

        return QgsPoint(self.points[0][self.X],
                        self.points[0][self.Y]).azimuth(QgsPoint(self.points[-1][self.X],
                                                                 self.points[-1][self.Y]))

    def get_maximal_vertical_angle(self) -> float:
        angles = [row[self.VERTICAL_ANGLE] for row in self.points]
        return max(angles)

    def __get_max_local_horizon_index(self) -> int:

        index_visible = None
        index_horizon = None

        for i in range(len(self.points) - 1, -1, -1):
            if self.visible[i]:
                index_visible = i
                break

        if 0 < index_visible:
            for i in range(index_visible - 1, -1, -1):
                if self.horizon[i]:
                    index_horizon = i
                    break

        return index_horizon

    def get_max_local_horizon_angle(self) -> float:

        index_horizon = self.__get_max_local_horizon_index()

        if index_horizon is not None:
            return self.points[index_horizon][self.VERTICAL_ANGLE]
        else:
            return -90

    def get_max_local_horizon_distance(self) -> float:

        index_horizon = self.__get_max_local_horizon_index()

        if index_horizon is not None:
            return self.points[index_horizon][self.DISTANCE]
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

    def __get_global_horizon_index(self) -> int:

        index = None

        for i in range(len(self.points)-1, -1, -1):
            if self.horizon[i]:
                index = i
                break

        return index

    def get_global_horizon_distance(self) -> float:

        index = self.__get_global_horizon_index()

        if index is not None:
            return self.points[index][2]
        else:
            return 0

    def get_global_horizon_angle(self) -> float:

        index = self.__get_global_horizon_index()

        if index is not None:
            return self.points[index][self.VERTICAL_ANGLE]
        else:
            return 90

    def get_global_horizon(self) -> QgsPoint:

        index = self.__get_global_horizon_index()

        if index is None:
            index = -1

        return self.get_geom_at_index(index)
