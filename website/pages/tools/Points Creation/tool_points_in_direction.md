# Create Points in Direction

Create set of points at given distance from points from input layer that span given angle offset from main direction layer.

The default value produces range of values [-20;20] by one angle from azimuth of point in main direction layer.

## Parameters

| Label                                | Name             | Type                                    | Description                                                                                                                                                                                |
| ------------------------------------ | ---------------- | --------------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------ |
| Input point layer                    | `InputLayer`     | [vector: point]                         | Point layer around which the new points will be created.                                                                                                                                   |
| Main direction point layer           | `DirectionLayer` | [vector: point]                         | Point layer (containing only one point) that specifies main direction.                                                                                                                     |
| ID field to assign to output         | `IdField`        | [tablefield: numeric]                   | Field value to assign to `id_original_point` for new layer.                                                                                                                                |
| Angle offset from the main direction | `AngleOffset`    | [number] <br/><br/> Default: <br/> `20` | Offset from main direction, the whole range is [main azimuth - angleOffset;main azimuth + angleOffset].                                                                                    |
| Angle step                           | `AngleStep`      | [number] <br/><br/> Default: <br/> `1`  | Determines density of point placement between `Minimal angle` and `Maximal angle`. Angular distance of points. Number of points will be (`Maximal angle` - `Minimal angle`) / `AngleStep`. |
| Distance                             | `Distance`       | [number] <br/><br/> Default: <br/> `10` | How far from the original point the new points should be created.                                                                                                                          |
| Output layer                         | `OutputLayer`    | [vector: point]                         | Output layer containing points.                                                                                                                                                            |

## Outputs

| Label        | Name          | Type            | Description                     |
| ------------ | ------------- | --------------- | ------------------------------- |
| Output layer | `OutputLayer` | [vector: point] | Output layer containing points. |

### Fields in the output layer

* __id_original_point__ - integer - value from field specified in `ID field to assign to output`
* __azimuth__ - double - azimuth from point in Input point layer to point in Main direction point layer
* __id_point__ - integer - unique id value for the point
* __difference_to_main_azimuth__ - double - difference of main point azimuth to this point's azimuth
* __angle_step_between_points__ - double - azimuth step between individual points
* 
## Tool screenshot

![Create points in direction](../../images/tool_points_in_direction.png)
	