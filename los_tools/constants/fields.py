from qgis.core import QgsField, QgsFields

from los_tools.constants.field_names import FieldNames
from los_tools.utils import COLUMN_TYPE, COLUMN_TYPE_STRING


class Fields:

    _field_azimuth = QgsField(FieldNames.AZIMUTH, COLUMN_TYPE.Double)
    _field_angle_step = QgsField(FieldNames.ANGLE_STEP, COLUMN_TYPE.Double)
    _field_observer_x = QgsField(FieldNames.OBSERVER_X, COLUMN_TYPE.Double)
    _field_observer_y = QgsField(FieldNames.OBSERVER_Y, COLUMN_TYPE.Double)

    _base_fields = QgsFields()
    _base_fields.append(QgsField(FieldNames.LOS_TYPE, COLUMN_TYPE_STRING))
    _base_fields.append(QgsField(FieldNames.ID_OBSERVER, COLUMN_TYPE.Int))
    _base_fields.append(QgsField(FieldNames.ID_TARGET, COLUMN_TYPE.Int))
    _base_fields.append(QgsField(FieldNames.OBSERVER_OFFSET, COLUMN_TYPE.Double))

    los_notarget_fields = QgsFields(_base_fields)
    los_notarget_fields.append(_field_azimuth)
    los_notarget_fields.append(_field_observer_x)
    los_notarget_fields.append(_field_observer_y)
    los_notarget_fields.append(_field_angle_step)

    los_local_fields = QgsFields(_base_fields)

    los_local_fields.append(QgsField(FieldNames.TARGET_OFFSET, COLUMN_TYPE.Double))

    los_global_fields = QgsFields(los_local_fields)
    los_global_fields.append(QgsField(FieldNames.TARGET_X, COLUMN_TYPE.Double))
    los_global_fields.append(QgsField(FieldNames.TARGET_Y, COLUMN_TYPE.Double))

    los_plugin_layer_fields = QgsFields(los_global_fields)
    los_plugin_layer_fields.append(_field_azimuth)
    los_plugin_layer_fields.append(_field_observer_x)
    los_plugin_layer_fields.append(_field_observer_y)
    los_plugin_layer_fields.append(_field_angle_step)
