# Create local LoS

Create line-of-sight between each point from observers layer and targets layer. Each line-of-sight starts at observer and ends at target.

## Parameters

| Label | Name | Type | Description |
| --- | --- | --- | --- |
| Raster Layer DEM | `DemRaster` | [raster] | Raster DEM on which the LoS is calculated. |
| Observers point layer | `ObserverPoints` | [vector: point] | Point layer representing the observers. |
| Observer ID field | `ObserverIdField` | [tablefield: numeric] | Field containing ID for observer points. |
| Observer offset field | `ObserverOffset` | [tablefield: numeric] | Field containing offset above DEM for observer points. |
| Targets point layer | `TargetPoints` | [vector: point] | Point layer representing the targets. |
| Target ID field | `TargetIdField` | [tablefield: numeric] | Field containing ID for target points. |
| Target offset field | `TargetOffset` | [tablefield: numeric] | Field containing offset above DEM for target points. |
| LoS sampling distance | `LineDensity` | [distance] <br/><br/> Default: <br/> `1` | The distance by which the LoS is segmentized. |
| Output layer | `OutputLayer` | [vector: line] | Output layer containing LoS. |

## Outputs

| Label | Name | Type | Description |
| --- | --- | --- | --- |
| Output layer | `OutputLayer` | [vector: line] | Output layer containing LoS. |

### Fields in the output layer

* __los_type__ - string - for this tool the values is always `local`
* __id_observer__ - integer - value from field specified in `Observer ID field`
* __id_target__ - integer - value from field specified in `Target ID field`
* __observer_offset__ - double - value from the field specified in `Observer offset field`
* __target_offset__ - double - value from the field specified in `Target offset field`


## Tool screenshot

![Create local LoS](../../images/tool_create_local_los.png)
	