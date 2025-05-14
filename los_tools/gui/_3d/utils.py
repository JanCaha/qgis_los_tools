import math

from qgis._3d import Qgs3DMapSettings, QgsCameraPose
from qgis.core import Qgis, QgsCoordinateReferenceSystem, QgsPointXY, QgsVector3D

from los_tools.classes.list_raster import ListOfRasters


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
    list_of_rasters: ListOfRasters,
    canvas_crs: QgsCoordinateReferenceSystem,
    point_observer: QgsPointXY,
    point_target: QgsPointXY,
    observer_offset: float,
) -> QgsCameraPose:

    observer_z = list_of_rasters.extract_interpolated_value_at_point(point_observer, canvas_crs) + observer_offset

    target_z = list_of_rasters.extract_interpolated_value_at_point(point_target, canvas_crs)

    look_at_point = canvas_3d_settings.mapToWorldCoordinates(QgsVector3D(point_target.x(), point_target.y(), target_z))
    look_from_point = canvas_3d_settings.mapToWorldCoordinates(
        QgsVector3D(point_observer.x(), point_observer.y(), observer_z)
    )

    if Qgis.versionInt() >= 34100:

        camera_pose.setCenterPoint(look_at_point)
        camera_pose.setHeadingAngle(heading_angle(look_at_point, look_from_point))
        camera_pose.setDistanceFromCenterPoint(look_at_point.distance(look_from_point))
        camera_pose.setPitchAngle(vertical_angle(look_from_point, look_at_point))

    else:

        start_point = QgsPointXY(look_at_point.x(), look_at_point.z())
        end_point = QgsPointXY(look_from_point.x(), look_from_point.z())

        angle = start_point.azimuth(end_point)

        distance = look_at_point.distance(look_from_point)

        vert_angle = math.degrees(math.atan((look_from_point.y() - look_at_point.y()) / distance))

        vert_angle = 90 - (vert_angle)

        camera_pose.setCenterPoint(look_at_point)
        camera_pose.setHeadingAngle(angle)
        camera_pose.setDistanceFromCenterPoint(distance)
        camera_pose.setPitchAngle(vert_angle)

    return camera_pose
