import math

from qgis._3d import Qgs3DMapSettings, QgsCameraPose
from qgis.core import (
    QgsAbstractTerrainProvider,
    QgsCoordinateReferenceSystem,
    QgsCoordinateTransform,
    QgsPointXY,
    QgsProject,
    QgsVector3D,
)


def heading_angle(p1: QgsVector3D, p2: QgsVector3D):
    dx = p2.x() - p1.x()
    dy = p2.y() - p1.y()

    angle_rad = math.atan2(dx, dy)
    angle_deg = math.degrees(angle_rad)
    angle_deg = (180 - angle_deg) % 360

    return angle_deg


def vertical_angle(p1: QgsVector3D, p2: QgsVector3D) -> float:
    vert_angle = math.degrees(math.atan((p1.z() - p2.z()) / p2.distance(p1)))

    vert_angle = 90 - (vert_angle)

    return vert_angle


def set_camera_to_position_and_look(
    canvas_3d_settings: Qgs3DMapSettings,
    camera_pose: QgsCameraPose,
    elevation_provider: QgsAbstractTerrainProvider,
    canvas_crs: QgsCoordinateReferenceSystem,
    point_observer: QgsPointXY,
    point_target: QgsPointXY,
    observer_offset: float,
) -> QgsCameraPose:

    point = convert_point_from_canvas_crs_to_elevation_provider_crs(
        canvas_crs, elevation_provider.crs(), point_observer
    )
    observer_z = elevation_provider.heightAt(point.x(), point.y()) + observer_offset

    point = convert_point_from_canvas_crs_to_elevation_provider_crs(canvas_crs, elevation_provider.crs(), point_target)
    target_z = elevation_provider.heightAt(point.x(), point.y())

    look_at_point = canvas_3d_settings.mapToWorldCoordinates(QgsVector3D(point_target.x(), point_target.y(), target_z))
    look_from_point = canvas_3d_settings.mapToWorldCoordinates(
        QgsVector3D(point_observer.x(), point_observer.y(), observer_z)
    )

    camera_pose.setCenterPoint(look_at_point)
    camera_pose.setHeadingAngle(heading_angle(look_at_point, look_from_point))
    camera_pose.setDistanceFromCenterPoint(look_at_point.distance(look_from_point))
    camera_pose.setPitchAngle(vertical_angle(look_from_point, look_at_point))

    return camera_pose


def convert_point_from_canvas_crs_to_elevation_provider_crs(
    canvas_crs: QgsCoordinateReferenceSystem, terrain_provider_crs: QgsCoordinateReferenceSystem, point: QgsPointXY
) -> QgsPointXY:

    transform = QgsCoordinateTransform(canvas_crs, terrain_provider_crs, QgsProject.instance())

    return transform.transform(point)
