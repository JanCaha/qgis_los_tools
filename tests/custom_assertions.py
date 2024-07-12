from typing import Any, Dict, List, Optional

from qgis.core import (
    QgsCoordinateReferenceSystem,
    QgsProcessingAlgorithm,
    QgsProcessingContext,
    QgsProcessingFeedback,
    QgsProcessingParameterDefinition,
    QgsVectorLayer,
    QgsWkbTypes,
)


def assert_algorithm(algorithm: QgsProcessingAlgorithm) -> None:
    assert isinstance(algorithm.group(), (str, type(None)))
    assert isinstance(algorithm.groupId(), (str, type(None)))
    assert isinstance(algorithm.displayName(), str)
    assert isinstance(algorithm.name(), str)
    assert isinstance(algorithm.createInstance(), type(algorithm))
    assert isinstance(algorithm.helpUrl(), (str, type(None)))
    assert isinstance(algorithm.shortHelpString(), (str, type(None)))


def assert_parameter(
    parameter: QgsProcessingParameterDefinition,
    parameter_type: str,
    default_value: Optional[Any] = None,
    parent_parameter: Optional[str] = None,
    data_type: Optional[int] = None,
) -> None:
    if parameter_type != parameter.type():
        raise AssertionError(f"QgsProcessingParameter type error: {parameter_type} != {parameter.type()}.")

    if default_value is not None:
        if default_value != parameter.defaultValue():
            raise AssertionError(
                f"QgsProcessingParameter default value error: {default_value} != {parameter.defaultValue()}."
            )

    if parent_parameter is not None:
        if parent_parameter != parameter.parentLayerParameterName():
            raise AssertionError(
                f"QgsProcessingParameter parent layer error: {parent_parameter} != {parameter.parentLayerParameterName()}."
            )

    if data_type is not None:
        if data_type != parameter.dataType():
            raise AssertionError(f"QgsProcessingParameter data type error: {data_type} != {parameter.dataType()}.")


def assert_check_parameter_values(alg: QgsProcessingAlgorithm, parameters: Dict) -> None:
    can_run, param_check_msg = alg.checkParameterValues(parameters=parameters, context=QgsProcessingContext())

    if not can_run:
        raise AssertionError(param_check_msg)


def assert_run(algorithm: QgsProcessingAlgorithm, parameters: Dict, allow_none_outputs: bool = False) -> None:
    can_run, param_check_msg = algorithm.checkParameterValues(parameters=parameters, context=QgsProcessingContext())

    if not can_run:
        raise AssertionError(param_check_msg)

    assert can_run

    result = algorithm.run(parameters=parameters, context=QgsProcessingContext(), feedback=QgsProcessingFeedback())

    if len(result[0]) != len(algorithm.outputDefinitions()):
        raise AssertionError(
            f"Number of provided outputs of the algorithm ({len(result[0])}) "
            f"does not match the number of outputs specified ({len(algorithm.outputDefinitions())}). Result: {result}"
        )

    if not allow_none_outputs:
        for output, output_value in result[0].items():
            if output_value is None:
                raise AssertionError(
                    f"Output `{output}` is `None`, which is not allowed "
                    f"(unless the `allow_none_outputs` is set to `True`)."
                )


def assert_field_names_exist(field_names: List[str], vector_layer: QgsVectorLayer) -> None:
    layer_field_names = vector_layer.fields().names()

    for field in field_names:
        if field not in layer_field_names:
            raise AssertionError(
                f"Field `{field}` not found in fields of QgsVectorLayer [{', '.join(layer_field_names)}]."
            )


def assert_layer(
    layer: QgsVectorLayer,
    geom_type: Optional[QgsWkbTypes] = None,
    crs: QgsCoordinateReferenceSystem = None,
) -> None:
    if not isinstance(layer, QgsVectorLayer):
        raise AssertionError(f"Provided `layer` is not `QgsVectorLayer`. It is: `{type(layer).__name__}`.")

    if geom_type:
        if geom_type != layer.wkbType():
            raise AssertionError(
                f"Expected `geom type` id `{geom_type}` != `{layer.wkbType()}` of the `layer.wkbType()`."
            )

    if crs:
        if layer.sourceCrs().authid() != crs.authid():
            raise AssertionError(
                f"The authid for `layer` crs ({layer.sourceCrs().authid()}) does not match expected `crs` ({crs.authid()})."
            )
