import pytest
from qgis.core import QgsFeature, QgsVectorLayer

from los_tools.classes.classes_los import LoSGlobal, LoSLocal, LoSWithoutTarget


def test_los_creation(los_local: QgsVectorLayer) -> None:

    feature = los_local.getFeature(1)

    los_local_object = LoSLocal.from_feature(
        feature,
    )

    assert los_local_object.points
    assert len(los_local_object.points) == 63


def test_local_los(local_los_feature: QgsFeature) -> None:
    local_los = LoSLocal.from_feature(local_los_feature)

    assert len(local_los.points) == 11

    assert local_los.visible[0]
    assert local_los.visible[1]
    assert local_los.visible[2]
    assert local_los.visible[3]
    assert local_los.visible[4] is False
    assert local_los.visible[5] is False
    assert local_los.visible[6]
    assert local_los.visible[7] is False
    assert local_los.visible[8] is False
    assert local_los.visible[9]
    assert local_los.visible[10] is False

    assert local_los.horizon[0] is False
    assert local_los.horizon[1] is False
    assert local_los.horizon[2] is False
    assert local_los.horizon[3]
    assert local_los.horizon[4] is False
    assert local_los.horizon[5] is False
    assert local_los.horizon[6]
    assert local_los.horizon[7] is False
    assert local_los.horizon[8] is False
    assert local_los.horizon[9]
    assert local_los.horizon[10] is False

    assert local_los.is_global is False
    assert local_los.is_without_target is False

    assert local_los._get_global_horizon_index() == 9
    assert pytest.approx(local_los.target_angle, rel=1e-2) == 41.984
    assert local_los.is_target_visible() is False
    assert local_los.get_local_horizon_count() == 3


def test_global_los(global_los_feature: QgsFeature) -> None:
    global_los = LoSGlobal.from_feature(global_los_feature)

    assert len(global_los.points) == 11

    assert global_los.visible[0]
    assert global_los.visible[1]
    assert global_los.visible[2]
    assert global_los.visible[3]
    assert global_los.visible[4] is False
    assert global_los.visible[5] is False
    assert global_los.visible[6]
    assert global_los.visible[7] is False
    assert global_los.visible[8] is False
    assert global_los.visible[9]
    assert global_los.visible[10] is False

    assert global_los.horizon[0] is False
    assert global_los.horizon[1] is False
    assert global_los.horizon[2] is False
    assert global_los.horizon[3]
    assert global_los.horizon[4] is False
    assert global_los.horizon[5] is False
    assert global_los.horizon[6]
    assert global_los.horizon[7] is False
    assert global_los.horizon[8] is False
    assert global_los.horizon[9]
    assert global_los.horizon[10] is False

    assert global_los.is_global
    assert global_los.is_without_target is False

    assert global_los._get_global_horizon_index() == 9
    assert global_los.is_target_visible() is True
    assert global_los.get_horizon_count() == 1


def test_notarget_los(notarget_los_feature: QgsFeature) -> None:
    notarget_los = LoSWithoutTarget.from_feature(notarget_los_feature)

    assert len(notarget_los.points) == 11

    assert notarget_los.visible[0]
    assert notarget_los.visible[1]
    assert notarget_los.visible[2]
    assert notarget_los.visible[3]
    assert notarget_los.visible[4] is False
    assert notarget_los.visible[5] is False
    assert notarget_los.visible[6]
    assert notarget_los.visible[7] is False
    assert notarget_los.visible[8] is False
    assert notarget_los.visible[9]
    assert notarget_los.visible[10] is False

    assert notarget_los.horizon[0] is False
    assert notarget_los.horizon[1] is False
    assert notarget_los.horizon[2] is False
    assert notarget_los.horizon[3]
    assert notarget_los.horizon[4] is False
    assert notarget_los.horizon[5] is False
    assert notarget_los.horizon[6]
    assert notarget_los.horizon[7] is False
    assert notarget_los.horizon[8] is False
    assert notarget_los.horizon[9]
    assert notarget_los.horizon[10] is False

    assert notarget_los.is_global is False
    assert notarget_los.is_without_target

    assert notarget_los._get_global_horizon_index() == 9
    assert notarget_los.get_max_local_horizon_angle() == pytest.approx(49.394, rel=1e-2)
