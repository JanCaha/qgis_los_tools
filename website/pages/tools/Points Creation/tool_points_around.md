# Create Points Around

Creates points at a specified distance from points in the input layer, spanning from a minimal to a maximal angle with a specified angle step.

The default values create points from angle 0 (north) to angle 359 (almost north) by one 1 degree, which means 360 points (one point per degree).

## Parameters

| Label                        | Name          | Type                                     | Description                                                                                                                                                                                  |
| ---------------------------- | ------------- | ---------------------------------------- | -------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| Input point layer            | `InputLayer`  | [vector: point]                          | Point layer around which the new points will be created.                                                                                                                                     |
| ID field to assign to output | `IdField`     | [tablefield: numeric]                    | Field value to assign to `id_original_point` for the new layer.                                                                                                                              |
| Minimal angle                | `AngleStart`  | [number] <br/><br/> Default: <br/> `0`   | Angle (azimuth) at which the generation of points should start.                                                                                                                              |
| Maximal angle                | `AngleEnd`    | [number] <br/><br/> Default: <br/> `359` | Angle (azimuth) at which the generation of points should end.                                                                                                                                |
| Angle step                   | `AngleStep`   | [number] <br/><br/> Default: <br/> `1`   | DDetermines the density of point placement between `AngleStart` and `AngleEnd`. The angular distance between points. The number of points will be (`AngleEnd` - `AngleStart`) / `AngleStep`. |
| Distance                     | `Distance`    | [number] <br/><br/> Default: <br/> `10`  | Distance from the original point at which the new points should be created.                                                                                                                  |
| Output layer                 | `OutputLayer` | [vector: point]                          | Output layer containing the new points.                                                                                                                                                      |

## Outputs

| Label        | Name          | Type            | Description                             |
| ------------ | ------------- | --------------- | --------------------------------------- |
| Output layer | `OutputLayer` | [vector: point] | Output layer containing the new points. |

### Fields in the output layer

* __id_original_point__ - integer - value from field specified in `ID field to assign to output`
* __azimuth__ - double - azimuth from original point to the given output point
* __angle_step_between_points__ - double - azimuth step between individual points

## Tool screenshot

![Create points around](../../images/tool_points_around.png)
