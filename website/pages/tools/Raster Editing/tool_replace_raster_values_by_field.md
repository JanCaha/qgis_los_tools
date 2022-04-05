# Replace Raster Values by Field Values

Tool to replace raster values in polygons with field value (defined by `ValueField`). 

## Parameters

| Label                         | Name           | Type                  | Description                                                                       |
| ----------------------------- | -------------- | --------------------- | --------------------------------------------------------------------------------- |
| Raster Layer                  | `RasterLayer`  | [vector: line]        | Raster layer to use as base.                                                      |
| Vector Layer                  | `VectorLayer`  | [vector: polygon]     | Vector layer that specifies areas of raster to replace the values.                |
| Field specifying the addition | `ValueField`   | [tablefield: numeric] | Field from vector layer that defines values that should be used in output raster. |
| Output Raster                 | `OutputRaster` | [raster]              | Output raster with new values.                                                    |

## Outputs

| Label         | Name           | Type     | Description                    |
| ------------- | -------------- | -------- | ------------------------------ |
| Output Raster | `OutputRaster` | [raster] | Output raster with new values. |

## Tool screenshot

![Replace Raster Values by Field Values](../../images/tool_replace_raster_values_by_field.png)
	