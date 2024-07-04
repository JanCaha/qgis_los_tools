from qgis.core import QgsField, QgsFields
from qgis.PyQt.QtCore import QMetaType

from .field_names import FieldNames


class Fields:

    _field_azimuth = QgsField(FieldNames.AZIMUTH, QMetaType.Type.Double)
    _field_angle_step = QgsField(FieldNames.ANGLE_STEP, QMetaType.Type.Double)
    _field_observer_x = QgsField(FieldNames.OBSERVER_X, QMetaType.Type.Double)
    _field_observer_y = QgsField(FieldNames.OBSERVER_Y, QMetaType.Type.Double)

    _base_fields = QgsFields()
    _base_fields.append(QgsField(FieldNames.LOS_TYPE, QMetaType.Type.QString))
    _base_fields.append(QgsField(FieldNames.ID_OBSERVER, QMetaType.Type.Int))
    _base_fields.append(QgsField(FieldNames.ID_TARGET, QMetaType.Type.Int))
    _base_fields.append(QgsField(FieldNames.OBSERVER_OFFSET, QMetaType.Type.Double))

    los_notarget_fields = QgsFields(_base_fields)
    los_notarget_fields.append(_field_azimuth)
    los_notarget_fields.append(_field_observer_x)
    los_notarget_fields.append(_field_observer_y)
    los_notarget_fields.append(_field_angle_step)

    los_local_fields = QgsFields(_base_fields)
    los_local_fields.append(QgsField(FieldNames.TARGET_OFFSET, QMetaType.Type.Double))

    los_global_fields = QgsFields(los_local_fields)
    los_global_fields.append(QgsField(FieldNames.TARGET_X, QMetaType.Type.Double))
    los_global_fields.append(QgsField(FieldNames.TARGET_Y, QMetaType.Type.Double))

    los_plugin_layer_fields = QgsFields(los_global_fields)
    los_plugin_layer_fields.append(_field_azimuth)
    los_plugin_layer_fields.append(_field_observer_x)
    los_plugin_layer_fields.append(_field_observer_y)
    los_plugin_layer_fields.append(_field_angle_step)
