import sys

import qgis.utils


def test_plugin_can_be_loaded():
    """Test if the plugin loads successfully."""

    plugin_name = "los_tools"

    load = qgis.utils.loadPlugin(plugin_name)

    assert load, f"Plugin '{plugin_name}' failed to load."

    assert plugin_name in qgis.utils.available_plugins
    assert plugin_name in sys.modules

    started = qgis.utils.startPlugin(plugin_name)

    assert started, f"Plugin '{plugin_name}' failed to start."

    loaded = qgis.utils.isPluginLoaded(plugin_name)

    assert loaded, f"Plugin '{plugin_name}' metadata not found."
