from qgis.gui import (QgsUserInputWidget, QgsFloatingWidget, QgsMapCanvas)
from qgis.PyQt.QtWidgets import QWidget


def prepare_user_input_widget(canvas: QgsMapCanvas, widget_to_add: QWidget = None):
    user_input_widget = QgsUserInputWidget(canvas)
    user_input_widget.setObjectName('UserInputDockWidget')
    user_input_widget.setAnchorWidget(canvas)
    user_input_widget.setAnchorWidgetPoint(QgsFloatingWidget.TopRight)
    user_input_widget.setAnchorPoint(QgsFloatingWidget.TopRight)
    if widget_to_add:
        user_input_widget.addUserInputWidget(widget_to_add)
    user_input_widget.hide()
    return user_input_widget
