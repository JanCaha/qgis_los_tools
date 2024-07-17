from qgis.core import Qgis, QgsField, QgsFields
from qgis.PyQt.QtCore import QMetaType, QVariant

from .field_names import FieldNames


class Fields:

    if Qgis.versionInt() >= 33800:
        source_type = QMetaType.Type
        source_type_string = source_type.QString
    else:
        source_type = QVariant.Type
        source_type_string = source_type.String

    _field_azimuth = QgsField(FieldNames.AZIMUTH, source_type.Double)
    _field_angle_step = QgsField(FieldNames.ANGLE_STEP, source_type.Double)
    _field_observer_x = QgsField(FieldNames.OBSERVER_X, source_type.Double)
    _field_observer_y = QgsField(FieldNames.OBSERVER_Y, source_type.Double)

    _base_fields = QgsFields()
    _base_fields.append(QgsField(FieldNames.LOS_TYPE, source_type_string))
    _base_fields.append(QgsField(FieldNames.ID_OBSERVER, source_type.Int))
    _base_fields.append(QgsField(FieldNames.ID_TARGET, source_type.Int))
    _base_fields.append(QgsField(FieldNames.OBSERVER_OFFSET, source_type.Double))

    los_notarget_fields = QgsFields(_base_fields)
    los_notarget_fields.append(_field_azimuth)
    los_notarget_fields.append(_field_observer_x)
    los_notarget_fields.append(_field_observer_y)
    los_notarget_fields.append(_field_angle_step)

    los_local_fields = QgsFields(_base_fields)

    los_local_fields.append(QgsField(FieldNames.TARGET_OFFSET, source_type.Double))

    los_global_fields = QgsFields(los_local_fields)
    los_global_fields.append(QgsField(FieldNames.TARGET_X, source_type.Double))
    los_global_fields.append(QgsField(FieldNames.TARGET_Y, source_type.Double))

    los_plugin_layer_fields = QgsFields(los_global_fields)
    los_plugin_layer_fields.append(_field_azimuth)
    los_plugin_layer_fields.append(_field_observer_x)
    los_plugin_layer_fields.append(_field_observer_y)
    los_plugin_layer_fields.append(_field_angle_step)
