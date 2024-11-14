import pytest

from los_tools.gui.dialog_object_parameters import ObjectParameters


def test_widget_object_distance():
    widget = ObjectParameters()

    assert widget is not None

    widget.what_calculate.setCurrentIndex(0)
    widget.object_size.setValue(1)
    widget.object_angle_size.setValue(0.1)

    assert widget.object_distance.isEnabled() is False
    assert widget.object_distance.value() == pytest.approx(572.96, abs=0.01)

    widget.object_angle_size.setValue(0.5)

    assert widget.object_distance.isEnabled() is False
    assert widget.object_distance.value() == pytest.approx(114.59, abs=0.01)


def test_widget_object_size():
    widget = ObjectParameters()

    assert widget is not None

    widget.what_calculate.setCurrentIndex(1)

    widget.object_distance.setValue(1000)
    widget.object_angle_size.setValue(0.1)

    assert widget.object_size.isEnabled() is False
    assert widget.object_size.value() == pytest.approx(1.75, abs=0.01)

    widget.object_angle_size.setValue(0.5)

    assert widget.object_size.isEnabled() is False
    assert widget.object_size.value() == pytest.approx(8.73, abs=0.01)


def test_widget_object_angle():
    widget = ObjectParameters()

    assert widget is not None

    widget.what_calculate.setCurrentIndex(2)

    widget.object_size.setValue(2)
    widget.object_distance.setValue(1000)

    assert widget.object_angle_size.isEnabled() is False
    assert widget.object_angle_size.value() == pytest.approx(0.115, abs=0.001)

    widget.object_size.setValue(5)

    assert widget.object_angle_size.isEnabled() is False
    assert widget.object_angle_size.value() == pytest.approx(0.286, abs=0.001)

    widget.object_size.setValue(1)

    assert widget.object_angle_size.isEnabled() is False
    assert widget.object_angle_size.value() == pytest.approx(0.057, abs=0.001)
