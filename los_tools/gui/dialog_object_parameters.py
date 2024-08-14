import math
from enum import Enum, auto
from typing import Optional, Union

from qgis.PyQt.QtCore import Qt
from qgis.PyQt.QtWidgets import QComboBox, QDialog, QDoubleSpinBox, QFormLayout, QWidget

from .custom_classes import DistanceWidget


class CalculationType(Enum):
    SIZE = auto()
    DISTANCE = auto()
    ANGLE = auto()


class ObjectParameters(QDialog):
    def __init__(
        self,
        parent: Optional[QWidget] = None,
        flags: Union[Qt.WindowFlags, Qt.WindowType] = Qt.Dialog,
    ) -> None:
        super().__init__(parent, flags)

        self.init_gui()

    def init_gui(self) -> None:
        self.setWindowTitle("Object Visibility Parameters")
        self.setMinimumWidth(600)

        layout = QFormLayout(self)
        self.setLayout(layout)

        self.what_calculate = QComboBox(self)
        self.what_calculate.addItem("Object Distance", CalculationType.DISTANCE)
        self.what_calculate.addItem("Object Size", CalculationType.SIZE)
        self.what_calculate.addItem("Object Angle", CalculationType.ANGLE)
        self.what_calculate.currentIndexChanged.connect(self.enable_gui_elements)

        self.object_size = DistanceWidget(self)
        self.object_size.setValue(1)
        self.object_size.setClearValue(1)
        self.object_size.valueChanged.connect(self.calculate)

        self.object_distance = DistanceWidget(self)
        self.object_distance.setValue(1000)
        self.object_distance.setClearValue(1000)
        self.object_distance.valueChanged.connect(self.calculate)

        self.object_angle_size = QDoubleSpinBox(self)
        self.object_angle_size.setDecimals(3)
        self.object_angle_size.setSuffix("°")
        self.object_angle_size.setMinimum(0.001)
        self.object_angle_size.setSingleStep(0.01)
        self.object_angle_size.valueChanged.connect(self.calculate)

        layout.addRow("Calculate", self.what_calculate)
        layout.addRow("Object Size", self.object_size)
        layout.addRow("Object Distance", self.object_distance)
        layout.addRow("Object Angle Size", self.object_angle_size)

        self.enable_gui_elements()

    @property
    def calculation_type(self) -> CalculationType:
        return self.what_calculate.currentData(Qt.ItemDataRole.UserRole)

    def enable_gui_elements(self) -> None:
        if self.calculation_type == CalculationType.DISTANCE:
            self.object_distance.setEnabled(False)
            self.object_angle_size.setEnabled(True)
            self.object_size.setEnabled(True)
        elif self.calculation_type == CalculationType.SIZE:
            self.object_distance.setEnabled(True)
            self.object_angle_size.setEnabled(True)
            self.object_size.setEnabled(False)
        elif self.calculation_type == CalculationType.ANGLE:
            self.object_distance.setEnabled(True)
            self.object_angle_size.setEnabled(False)
            self.object_size.setEnabled(True)
        else:
            # default is distance
            self.object_distance.setEnabled(False)
            self.object_angle_size.setEnabled(True)
            self.object_size.setEnabled(True)

    def calculate(self) -> None:
        self.block_all_signals(True)

        if self.calculation_type == CalculationType.DISTANCE:
            self.object_distance.setValue(
                round(
                    self.object_size.value() / math.tan(math.radians(self.object_angle_size.value())),
                    3,
                )
            )

        elif self.calculation_type == CalculationType.SIZE:
            self.object_size.setValue(
                round(
                    (math.tan(math.radians(self.object_angle_size.value()))) * self.object_distance.value(),
                    3,
                )
            )

        elif self.calculation_type == CalculationType.ANGLE:
            self.object_angle_size.setValue(
                math.degrees(math.atan(self.object_size.value() / self.object_distance.value()))
            )

        else:
            self.object_distance.setValue(
                round(
                    self.object_size.value() / math.tan(math.radians(self.object_angle_size.value())),
                    3,
                )
            )

        self.block_all_signals(False)

    def block_all_signals(self, b: bool) -> None:
        self.object_distance.blockSignals(b)
        self.object_size.blockSignals(b)
        self.object_angle_size.blockSignals(b)
