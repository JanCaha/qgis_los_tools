# Replace Raster Values by Constant Value

Replaces raster values within specified polygons with a constant value.

## Parameters

| Label                    | Name           | Type              | Description                                                                    |
| ------------------------ | -------------- | ----------------- | ------------------------------------------------------------------------------ |
| Raster Layer             | `RasterLayer`  | [raster]          | Raster layer to use as the base.                                               |
| Vector Layer             | `VectorLayer`  | [vector: polygon] | Vector layer specifying the areas of the raster where values will be replaced. |
| Raster value for polygon | `RasterValue`  | [number]          | Constant value to use as the replacement.                                      |
| Output Raster            | `OutputRaster` | [raster]          | Output raster with the new values.                                             |

## Outputs

| Label         | Name           | Type     | Description                        |
| ------------- | -------------- | -------- | ---------------------------------- |
| Output Raster | `OutputRaster` | [raster] | Output raster with the new values. |

## Tool screenshot

![Replace Raster Values by Constant Value](../../images/tool_replace_raster_values_by_constant.png)
