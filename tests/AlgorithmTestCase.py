import unittest

from typing import Any, Dict, List

from qgis.core import (QgsProcessingParameterDefinition,
                       QgsProcessingAlgorithm,
                       QgsVectorLayer,
                       QgsCoordinateReferenceSystem,
                       QgsProcessingFeedback,
                       QgsProcessingContext)
from qgis._core import QgsWkbTypes


class QgsProcessingAlgorithmTestCase(unittest.TestCase):

    def setUp(self) -> None:
        self.feedback = QgsProcessingFeedback()
        self.context = QgsProcessingContext()
        self.alg: QgsProcessingAlgorithm = None

    def printAlgorithmParametersDescription(self) -> None:
        if self.alg is not None:
            print("{}".format(self.alg.name()))
            print("----------------------------------")

            params = self.alg.parameterDefinitions()

            for p in params:
                print("{} - {} \n\t {} \t{}".format(p.name(),
                                                    p.type(),
                                                    p.description(),
                                                    p.asScriptCode()))

            print("----------------------------------")

            outputs = self.alg.outputDefinitions()

            for o in outputs:
                print("{} - {} \n\t {}".format(o.name(),
                                               o.type(),
                                               o.description()))

        else:
            print("----------------------------------")
            print("No algorithm provided!")
            print("----------------------------------")

    def assertQgsProcessingParameter(self,
                                     parameter: QgsProcessingParameterDefinition,
                                     parameter_type: str,
                                     default_value: Any = None,
                                     parent_parameter: str = None,
                                     data_type: int = None) -> None:

        if parameter_type != parameter.type():
            raise AssertionError("QgsProcessingParameter type error: {} != {}."
                                 .format(parameter_type, parameter.type()))

        if default_value is not None:
            if default_value != parameter.defaultValue():
                raise AssertionError("QgsProcessingParameter default value error: {} != {}."
                                     .format(default_value, parameter.defaultValue()))

        if parent_parameter is not None:
            if parent_parameter != parameter.parentLayerParameterName():
                raise AssertionError("QgsProcessingParameter parent layer error: {} != {}."
                                     .format(parent_parameter, parameter.parentLayerParameterName()))

        if data_type is not None:
            if data_type != parameter.dataType():
                raise AssertionError("QgsProcessingParameter data type error: {} != {}."
                                     .format(data_type, parameter.dataType()))

    def assertCheckParameterValuesRaisesMessage(self,
                                                parameters: Dict,
                                                message: str) -> None:

        can_run, param_check_msg = self.alg.checkParameterValues(parameters=parameters,
                                                                 context=self.context)
        if can_run:
            raise AssertionError("The `checkParameterValues` for algorithm should return `False`. "
                                 "It returns `{}` instead.".format(can_run))

        if message not in param_check_msg:
            raise AssertionError("The provided message `{}` is not part of returned message `{}`."
                                 .format(message, param_check_msg))

    def assertRunAlgorithm(self,
                           parameters: Dict,
                           message: str = "",
                           allow_none_outputs: bool = False) -> None:

        can_run, param_check_msg = self.alg.checkParameterValues(parameters=parameters,
                                                                 context=self.context)

        if not can_run:
            raise AssertionError("The `checkParameterValues` for algorithm should return `True`. "
                                 "It returns `{}` instead.".format(can_run))

        if message not in param_check_msg:
            raise AssertionError("The provided message `{}` is not part of returned message `{}`."
                                 .format(message, param_check_msg))

        result = self.alg.run(parameters=parameters,
                              context=self.context,
                              feedback=self.feedback)

        if len(result[0]) != len(self.alg.outputDefinitions()):
            raise AssertionError("Number of provided outputs of the algorithm ({}) "
                                 "does not match the number of outputs specified ({})."
                                 .format(len(result[0]), len(self.alg.outputDefinitions())))

        if not allow_none_outputs:
            for output, output_value in result[0].items():
                with self.subTest(output_name=output, output_value=output_value):
                    if output_value is None:
                        raise AssertionError("Output `{}` is `None`, which is not allowed "
                                             "(unless the `allow_none_outputs` is set to `True`)."
                                             .format(output))

    def assertFieldNamesInQgsVectorLayer(self,
                                         field_names: List[str],
                                         vector_layer: QgsVectorLayer) -> None:

        layer_field_names = vector_layer.fields().names()

        for field in field_names:
            with self.subTest(field_name=field):
                if field not in layer_field_names:
                    raise AssertionError("Field `{}` not found in fields of QgsVectorLayer [{}]."
                                         .format(field, ", ".join(layer_field_names)))

    def assertQgsVectorLayer(self,
                             layer: QgsVectorLayer,
                             geom_type: QgsWkbTypes,
                             crs: QgsCoordinateReferenceSystem) -> None:

        if not isinstance(layer, QgsVectorLayer):
            raise AssertionError("Provided `layer` is not `QgsVectorLayer`. It is: `{}`."
                                 .format(type(layer).__name__))

        if geom_type != layer.wkbType():
            raise AssertionError("Expected `geom type` id `{}` != `{}` of the `layer.wkbType()`."
                                 .format(geom_type, layer.wkbType()))

        if layer.sourceCrs().authid() != crs.authid():
            raise AssertionError("The authid for `layer` crs ({}) does not match expected `crs` ({})."
                                 .format(layer.sourceCrs().authid(), crs.authid()))
