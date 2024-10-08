# Extract Visible/Invisible Points from LoS

Extracts individual points from lines-of-sight. It is possible to extract only visible points and also to calculate extended attributes for these points.

## Parameters

| Label                         | Name                    | Type                                      | Description                                                    |
| ----------------------------- | ----------------------- | ----------------------------------------- | -------------------------------------------------------------- |
| LoS layer                     | `LoSLayer`              | [vector: line]                            | LoS layer to extract points from.                              |
| Use curvature corrections?    | `CurvatureCorrections`  | [boolean]<br/><br/>Default: `True`        | Should curvature and refraction corrections be applied?        |
| Refraction coefficient value  | `RefractionCoefficient` | [number] <br/><br/> Default: <br/> `0.13` | Value of the refraction coefficient.                           |
| Export only visible points    | `OnlyVisiblePoints`     | [boolean]<br/><br/>Default: `False`       | Export only visible points on LoS or export all points on LoS. |
| Calculate extended attributes | `ExtendedAttributes`    | [boolean]<br/><br/>Default: `False`       | Calculate extended attributes for points.                      |
| Output layer                  | `OutputLayer`           | [vector: point]                           | Output layer containing points.                                |

## Outputs

| Label        | Name          | Type            | Description                     |
| ------------ | ------------- | --------------- | ------------------------------- |
| Output layer | `OutputLayer` | [vector: point] | Output layer containing points. |

### Fields in the output layer

* __id_observer__ - integer - value from expected field (`id_observer`) in `LoSLayer`
* __id_target__ - integer - value from expected field (`id_target`) in `LoSLayer`
* __visible__ - boolean - is the point visible

### Additional fields if `Calculate extended attributes` is `True`

Calculation of these attributes can potentially significantly slow down the calculation.  

For all types of LoS:

* __angle_difference_local_horizon__ - double
* __elevation_difference_local_horizon__ - double

For Global and NoTarget LoS additionally:

* __angle_difference_global_horizon__ - double
* __elevation_difference_global_horizon__ - double

## Tool screenshot

![Extract Visible/Invisible Points from LoS](../../images/tool_extract_points_los.png)
	