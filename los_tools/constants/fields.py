from qgis.PyQt.QtCore import QVariant
from qgis.core import (QgsFields, QgsField)

from .field_names import FieldNames


class Fields:

    _field_azimuth = QgsField(FieldNames.AZIMUTH, QVariant.Double)
    _field_angle_step = QgsField(FieldNames.ANGLE_STEP, QVariant.Double)
    _field_observer_x = QgsField(FieldNames.OBSERVER_X, QVariant.Double)
    _field_observer_y = QgsField(FieldNames.OBSERVER_Y, QVariant.Double)

    _base_fields = QgsFields()
    _base_fields.append(QgsField(FieldNames.LOS_TYPE, QVariant.String))
    _base_fields.append(QgsField(FieldNames.ID_OBSERVER, QVariant.Int))
    _base_fields.append(QgsField(FieldNames.ID_TARGET, QVariant.Int))
    _base_fields.append(QgsField(FieldNames.OBSERVER_OFFSET, QVariant.Double))

    los_notarget_fields = QgsFields(_base_fields)
    los_notarget_fields.append(_field_azimuth)
    los_notarget_fields.append(_field_observer_x)
    los_notarget_fields.append(_field_observer_y)
    los_notarget_fields.append(_field_angle_step)

    los_local_fields = QgsFields(_base_fields)
    los_local_fields.append(QgsField(FieldNames.TARGET_OFFSET, QVariant.Double))

    los_global_fields = QgsFields(los_local_fields)
    los_global_fields.append(QgsField(FieldNames.TARGET_X, QVariant.Double))
    los_global_fields.append(QgsField(FieldNames.TARGET_Y, QVariant.Double))

    los_plugin_layer_fields = QgsFields(los_global_fields)
    los_plugin_layer_fields.append(_field_azimuth)
    los_plugin_layer_fields.append(_field_observer_x)
    los_plugin_layer_fields.append(_field_observer_y)
    los_plugin_layer_fields.append(_field_angle_step)
