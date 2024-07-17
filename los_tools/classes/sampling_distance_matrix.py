from typing import List, Union

import numpy as np
from qgis.core import QgsFeature, QgsGeometry, QgsLineString, QgsPoint, QgsVectorLayer

from los_tools.constants.field_names import FieldNames


class SamplingDistanceMatrix:
    NUMBER_OF_COLUMNS = 2

    INDEX_SAMPLING_DISTANCE = 0
    INDEX_DISTANCE = 1

    def __init__(self, data: QgsVectorLayer):
        self.data = []

        feature: QgsFeature

        for feature in data.getFeatures():
            self.data.append(
                [
                    feature.attribute(FieldNames.SIZE),
                    feature.attribute(FieldNames.DISTANCE),
                ]
            )

        self.sort_data()

    def __repr__(self):
        strings = ["Sampling distance, Distance Limit"]

        for row in self.data:
            strings.append(f"{row[0]}, {row[1]}")

        return "\n".join(strings)

    def __len__(self):
        return len(self.data)

    def sort_data(self):
        self.data = sorted(self.data, key=lambda d: d[self.INDEX_DISTANCE])

    def replace_minus_one_with_value(self, value: float) -> None:
        sampling_distance_limit = self.data[0][self.INDEX_SAMPLING_DISTANCE]

        for row in self.data:
            if value < row[self.INDEX_DISTANCE]:
                sampling_distance_limit = row[self.INDEX_SAMPLING_DISTANCE]
                break

        if self.minimum_distance == -1:
            self.data[0][self.INDEX_DISTANCE] = value
            self.data[0][self.INDEX_SAMPLING_DISTANCE] = sampling_distance_limit

            if 1 < len(self.data):
                while self.data[0][self.INDEX_DISTANCE] < self.data[-1][self.INDEX_DISTANCE]:
                    self.data.remove(self.data[-1])

            self.sort_data()

    def get_row(self, index: int) -> List[float]:
        return self.data[index]

    def get_row_distance(self, index: int):
        return self.get_row(index)[self.INDEX_DISTANCE]

    def get_row_sampling_distance(self, index: int):
        return self.get_row(index)[self.INDEX_SAMPLING_DISTANCE]

    @staticmethod
    def validate_table(data: QgsVectorLayer):
        field_names = data.fields().names()

        if FieldNames.SIZE_ANGLE not in field_names:
            return (
                False,
                f"Field `{FieldNames.SIZE_ANGLE}` does not exist but is required.",
            )

        if FieldNames.DISTANCE not in field_names:
            return (
                False,
                f"Field `{FieldNames.DISTANCE}` does not exist but is required.",
            )

        if FieldNames.SIZE not in field_names:
            return False, f"Field `{FieldNames.SIZE}` does not exist but is required."

        if data.featureCount() < 1:
            return (
                False,
                "There are no features in the sampling distance - distance table (layer).",
            )

        return True, ""

    @property
    def minimum_distance(self) -> float:
        return self.data[0][self.INDEX_DISTANCE]

    @property
    def maximum_distance(self) -> float:
        return self.data[-1][self.INDEX_DISTANCE]

    def next_distance(self, current_distance: float) -> float:
        value_to_add = 0.0

        row: List[float]

        for row in self.data:
            if row[self.INDEX_DISTANCE] < current_distance + row[self.INDEX_SAMPLING_DISTANCE]:
                value_to_add = row[self.INDEX_SAMPLING_DISTANCE]

        return current_distance + value_to_add

    def build_line(self, origin_point: QgsPoint, direction_point: QgsPoint) -> QgsLineString:
        line: Union[QgsLineString, QgsGeometry]

        lines = []

        for i in range(len(self)):
            if i == 0:
                line_res = self.densified_line(
                    origin_point,
                    origin_point.project(
                        self.get_row_distance(i + 1),
                        origin_point.azimuth(direction_point),
                    ),
                    i,
                )

                lines.append(line_res)

            else:
                if i + 1 < len(self):
                    this_line: QgsLineString = lines[-1].clone()
                    this_line.extend(0, self.get_row_distance(i + 1) - self.get_row_distance(i))

                    line_res = self.densified_line(lines[-1].endPoint(), this_line.endPoint(), i)

                    lines.append(line_res)

        result_line = QgsLineString()

        for line_part in lines:
            result_line.append(line_part)

        return result_line

    def densified_line(self, start_point: QgsPoint, end_point: QgsPoint, sampling_row_index: int) -> QgsLineString:
        line = QgsGeometry.fromPolyline([start_point, end_point])

        line = line.densifyByDistance(distance=np.nextafter(self.get_row_sampling_distance(sampling_row_index), np.Inf))

        return QgsLineString([x for x in line.vertices()])
