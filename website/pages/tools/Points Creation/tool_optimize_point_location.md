# Optimize Point Location

Optimizes point locations for visibility analyses using an optimization raster. The values of `InputRaster` serve as the optimization criterion, with higher values indicating better options. The result is a copy of `InputLayer` with point locations adjusted.

The optimization process is guided by two addition parameters - `Distance` and `MaskRaster`. `Distance` specifies distance around origin point to search for better values on `InputRaster` to move the point to. `MaskRaster` allows to optionally input raster that can move forbid some areas to be used as new point location. `MaskRaster` values `NoData` and `0` can be used to mark unavailable areas, other values can be used to place optimized points.

## Parameters

| Label                                  | Name          | Type                                    | Description                                                                                        |
| -------------------------------------- | ------------- | --------------------------------------- | -------------------------------------------------------------------------------------------------- |
| Location optimization raster           | `InputRaster` | [raster]                                | Raster layer used as the optimization criterion. Higher values are better.                         |
| Input point layer (points to optimize) | `InputLayer`  | [vector: point]                         | Point layer that specifies the input points.                                                       |
| Search radius                          | `Distance`    | [number] <br/><br/> Default: <br/> `30` | Distance around each point to search for a better value. Linked to the `InputRaster` parameter.    |
| Mask raster                            | `MaskRaster`  | [raster]                                | Raster specifying areas that can be used. Values `NoData` and `0` mark areas that are unavailable. |
| Output layer (optimized points)        | `OutputLayer` | [vector: point]                         | Copy of `InputLayer` with adjusted point positions.                                                |

## Outputs

| Label                           | Name          | Type            | Description                                         |
| ------------------------------- | ------------- | --------------- | --------------------------------------------------- |
| Output layer (optimized points) | `OutputLayer` | [vector: point] | Copy of `InputLayer` with adjusted point positions. |

### Fields in the output layer

The same as in `InputLayer`.

## Tool screenshot

![Optimize point location](../../images/tool_optimize_point_location.png)
	