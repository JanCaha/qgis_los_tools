import pytest
from qgis.core import Qgis, QgsVectorLayer

from los_tools.constants.field_names import FieldNames
from los_tools.processing.analyse_los.tool_extract_los_visibility_polygons import ExtractLoSVisibilityPolygonsAlgorithm
from tests.custom_assertions import (
    assert_algorithm,
    assert_check_parameter_values,
    assert_field_names_exist,
    assert_layer,
    assert_parameter,
    assert_run,
)
from tests.utils import result_filename


def test_parameters() -> None:
    alg = ExtractLoSVisibilityPolygonsAlgorithm()
    alg.initAlgorithm()

    assert_parameter(alg.parameterDefinition("LoSLayer"), parameter_type="source")
    assert_parameter(alg.parameterDefinition("OutputLayer"), parameter_type="sink")
    assert_parameter(alg.parameterDefinition("CurvatureCorrections"), parameter_type="boolean", default_value=True)
    assert_parameter(alg.parameterDefinition("RefractionCoefficient"), parameter_type="number", default_value=0.13)


def test_alg_settings() -> None:
    alg = ExtractLoSVisibilityPolygonsAlgorithm()
    alg.initAlgorithm()

    assert_algorithm(alg)


def test_check_wrong_params(los_no_target_wrong: QgsVectorLayer) -> None:
    alg = ExtractLoSVisibilityPolygonsAlgorithm()
    alg.initAlgorithm()

    # use layer that is not correctly constructed LoS layer
    params = {"LoSLayer": los_no_target_wrong}

    with pytest.raises(AssertionError, match="Fields specific for LoS not found in current layer"):
        assert_check_parameter_values(alg, parameters=params)


def test_run_alg(los_no_target: QgsVectorLayer) -> None:
    alg = ExtractLoSVisibilityPolygonsAlgorithm()
    alg.initAlgorithm()

    output_path = result_filename("los_parts.gpkg")

    params = {
        "LoSLayer": los_no_target,
        "OutputLayer": output_path,
        "CurvatureCorrections": True,
        "RefractionCoefficient": 0.13,
    }

    assert_run(alg, parameters=params)

    los_parts = QgsVectorLayer(output_path)

    assert_layer(los_parts, geom_type=Qgis.WkbType.MultiPolygon, crs=los_no_target.sourceCrs())

    assert_field_names_exist([FieldNames.ID_OBSERVER, FieldNames.ID_TARGET, FieldNames.VISIBLE], los_parts)

    assert los_parts.featureCount() == los_no_target.featureCount() * 2
