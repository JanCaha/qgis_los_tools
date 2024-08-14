# Calculate Object Distances

This tool calculates the distances at which objects of specified sizes (provided in the table) have a given horizontal angular size.

For example, it calculates the distances at which objects of sizes 1, 5, and 10 meters have an angular size of 0.1 degrees.    

To be usable in other plugin tools, there is a necessary parameter to be set maximal distance. It special row into the output table so that it can be later correctly processed.

## Parameters

| Label                                                                         | Name              | Type                                    | Description                                                                                                                                                                                                                 |
| ----------------------------------------------------------------------------- | ----------------- | --------------------------------------- | --------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| Angle size of object (in degrees)                                             | `Angle`           | [number]<br/><br/> Default: <br/> `0.1` | Horizontal angular size that the objects should have (in degrees).                                                                                                                                                          |
| Sizes of object to calculate (in meters)                                      | `Size`            | [matrix]                                | Sizes of the objects in meters (table).                                                                                                                                                                                     |  |
| Add maximal distance value (with sampling equal to maximal sampling distance) | `MaximalDistance` | [boolean]<br/><br/>Default: `True`      | Add a special row to the output used in other tools. The row has the size of the object equal to the maximum size in the input table and a distance of -1. This is used to indicate the maximum possible length of the LoS. |
| Output table                                                                  | `OutputTable`     | [table]                                 | Output table containing information about angular size, object sizes, and relevant distances.                                                                                                                               |

## Outputs

| Label        | Name          | Type    | Description                                                                                   |
| ------------ | ------------- | ------- | --------------------------------------------------------------------------------------------- |
| Output table | `OutputTable` | [table] | Output table containing information about angular size, object sizes, and relevant distances. |

### Fields in the output layer

* __Object size (angle)__ - integer - value from expected field (`PointLayerID`) in `PointLayer`
* __Distance (meters)__ - integer - value from expected field (`ObjectLayerID`) in `ObjectLayerID`
* __Size of objects (meters)__ - double - azimuth from given point to the centroid of given line/polygon

## Tool screenshot

![Calculate Object Distances](../../images/tool_distances_for_sizes.png)
