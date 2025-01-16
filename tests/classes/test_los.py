import pytest
from qgis.core import QgsVectorLayer

from los_tools.classes.classes_los import LoSGlobal, LoSLocal, LoSWithoutTarget


def test_los_creation(los_local: QgsVectorLayer) -> None:

    feature = los_local.getFeature(1)

    los_local_object = LoSLocal.from_feature(feature, sampling_distance=1)

    assert los_local_object.points
    assert len(los_local_object.points) == 63
