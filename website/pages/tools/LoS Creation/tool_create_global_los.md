# Create Global LoS

Creates a line-of-sight from each point in the observers layer through each point in the targets layer. Each line-of-sight starts at the observer and ends at the edge of the DEM raster behind the target.

## Parameters

| Label                 | Name              | Type                                     | Description                                                |
| --------------------- | ----------------- | ---------------------------------------- | ---------------------------------------------------------- |
| Raster Layer DEM      | `DemRasters`      | [raster][list]                           | Raster DEMs on which the LoS is calculated.                |
| Observers point layer | `ObserverPoints`  | [vector: point]                          | Point layer representing the observers.                    |
| Observer ID field     | `ObserverIdField` | [tablefield: numeric]                    | Field containing IDs for observer points.                  |
| Observer offset field | `ObserverOffset`  | [tablefield: numeric]                    | Field containing the offset above DEM for observer points. |
| Targets point layer   | `TargetPoints`    | [vector: point]                          | Point layer representing the targets.                      |
| Target ID field       | `TargetIdField`   | [tablefield: numeric]                    | Field containing IDs for target points.                    |
| Target offset field   | `TargetOffset`    | [tablefield: numeric]                    | Field containing the offset above DEM for target points.   |
| LoS sampling distance | `LineDensity`     | [distance] <br/><br/> Default: <br/> `1` | The distance by which the LoS is segmented.                |
| Output layer          | `OutputLayer`     | [vector: line]                           | Output layer containing the LoS.                           |

## Outputs

| Label        | Name          | Type           | Description                      |
| ------------ | ------------- | -------------- | -------------------------------- |
| Output layer | `OutputLayer` | [vector: line] | Output layer containing the LoS. |

### Fields in the output layer

* __los_type__ - string - for this tool the values is always `global`
* __id_observer__ - integer - value from field specified in `Observer ID field`
* __id_target__ - integer - value from field specified in `Target ID field`
* __observer_offset__ - double - value from the field specified in `Observer offset field`
* __target_offset__ - double - value from the field specified in `Target offset field`
* __target_x__ - double - X coordinate of point in `Targets point layer`, used later in analyses
* __target_y__ - double - Y coordinate of point in `Targets point layer`, used later in analyses


## Tool screenshot

![Create global LoS](../../images/tool_create_global_los.png)
