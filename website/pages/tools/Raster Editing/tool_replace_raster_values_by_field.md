# Replace Raster Values by Field Values

Tool to replace raster values within polygons based on a specified field value (`ValueField`).

## Parameters

| Label                        | Name           | Type                  | Description                                                                    |
| ---------------------------- | -------------- | --------------------- | ------------------------------------------------------------------------------ |
| Raster Layer                 | `RasterLayer`  | [raster]              | Base raster layer.                                                             |
| Vector Layer                 | `VectorLayer`  | [vector: polygon]     | Vector layer defining areas where raster values will be replaced.              |
| Field specifying replacement | `ValueField`   | [tablefield: numeric] | Field from the vector layer specifying the values to use in the output raster. |
| Output Raster                | `OutputRaster` | [raster]              | Output raster with updated values.                                             |

## Outputs

| Label         | Name           | Type     | Description                        |
| ------------- | -------------- | -------- | ---------------------------------- |
| Output Raster | `OutputRaster` | [raster] | Output raster with updated values. |

## Tool screenshot

![Replace Raster Values by Field Values](../../images/tool_replace_raster_values_by_field.png)
