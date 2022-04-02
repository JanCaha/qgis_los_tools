# Calculate Object Detection Angle

Determines object's angular size based on object size (horizontal) and distance from observer.


## Parameters

| Label                                            | Name          | Type                                     | Description                                                            |
| ------------------------------------------------ | ------------- | ---------------------------------------- | ---------------------------------------------------------------------- |
| Size of the object (in meters)                   | `Size`        | [number]<br/><br/> Default: <br/> `1.0`  | Size of the object in meters..                                         |
| Distance of the object from observer (in meters) | `Distance`    | [number]<br/><br/> Default: <br/> `1000` | Distance of the object from observer in meters.                        |  |
| Angle size (in degrees) of object                | `OutputAngle` | [number]                                 | Object size in degrees for object of given size at the given distance. |


## Outputs

| Label                             | Name          | Type     | Description                                                            |
| --------------------------------- | ------------- | -------- | ---------------------------------------------------------------------- |
| Angle size (in degrees) of object | `OutputAngle` | [number] | Object size in degrees for object of given size at the given distance. |


## Tool screenshot

![Calculate Object Detection Angle](../../images/tool_angle_at_distance_for_size.png)
