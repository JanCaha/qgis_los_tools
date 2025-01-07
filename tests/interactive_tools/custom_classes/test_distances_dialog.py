# pylint: disable=protected-access

from qgis.PyQt.QtWidgets import QWidget

from los_tools.gui.custom_classes import DistancesDialog


def test_distances_dialog(
    qgis_parent: QWidget,
) -> None:

    dialog = DistancesDialog(parent=qgis_parent)

    assert not dialog.distances()

    dialog.add_distance(1.0)

    assert dialog.distances() == [1.0]

    dialog.add_distance(50.0)

    assert dialog.distances() == [1.0, 50.0]

    dialog.add_distance(100.0)

    assert dialog.distances() == [1.0, 50.0, 100]

    item = dialog._distances_tree_widget.topLevelItem(1)
    dialog._distances_tree_widget.setCurrentItem(item)
    dialog._remove_distance()

    assert dialog.distances() == [1.0, 100]


def test_distances_dialog_with_distances(
    qgis_parent: QWidget,
) -> None:

    dialog = DistancesDialog([50, 10, 200], parent=qgis_parent)

    assert dialog.distances()
    assert dialog.distances() == [10.0, 50.0, 200.0]

    dialog = DistancesDialog(parent=qgis_parent)
    assert not dialog.distances()

    dialog.add_distances([50, 10, 500, 100])
    assert dialog.distances()
    assert dialog.distances() == [10.0, 50.0, 100.0, 500.0]
