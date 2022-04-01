# Calculate Object Sizes

The tool calculates sizes of objects at specific distances (specified in the table) that have given horizontal angular size.

I.e. what sizes of objects have given horizontal angular size at distances specified in the table.

To be usable in other plugin tools, there are two necessary parameter to be set: default sampling size, used before first distance from the table is used, and maximal distance. Both adds special row into the output table so that it can be later correctly processed.
	

## Parameters

| Label                                                                         | Name                      | Type                                    | Description                                                                                                                                                                                         |
| ----------------------------------------------------------------------------- | ------------------------- | --------------------------------------- | --------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| Angle size of object (in degrees)                                             | `Angle`                   | [number]<br/><br/> Default: <br/> `0.1` | Horizontal angular size that the objects should have (in degrees).                                                                                                                                  |
| Distances to calculate object size (in meters)                                | `Distance`                | [matrix]                                | Distances of the objects in meters (table).                                                                                                                                                         |
| Default sampling size (in meters)                                             | `DefaultSamplingDistance` | [number]<br/><br/> Default: <br/> `1.0` | Sampling distance to used, in tools that work with this table, for values smaller then smallest distance.                                                                                           |
| Add maximal distance value (with sampling equal to maximal sampling distance) | `MaximalDistance`         | [boolean]<br/><br/>Default: `True`      | Add special row to the output used in other tools. The row has size of the object equal to maximum size in the input table and distance -1. This is used to indicate maximal possible legth of LoS. |
| Output table                                                                  | `OutputTable`             | [table]                                 | Output table containing information about angle size, size of objects and relevant distances (without geometry).                                                                                    |

## Outputs

| Label        | Name          | Type    | Description                                                                                                     |
| ------------ | ------------- | ------- | --------------------------------------------------------------------------------------------------------------- |
| Output table | `OutputTable` | [table] | Output table containing information about angle size, size of objects and relevant distances (without geometry) |


### Fields in the output layer

* __Object size (angle)__ - integer - value from expected field (`PointLayerID`) in `PointLayer`
* __Distance (meters)__ - integer - value from expected field (`ObjectLayerID`) in `ObjectLayerID`
* __Size of objects (meters)__ - double - azimuth from given point to the centroid of given line/polygon

## Tool screenshot

![Calculate Object Sizes](../../images/tool_sizes_at_distances.png)
