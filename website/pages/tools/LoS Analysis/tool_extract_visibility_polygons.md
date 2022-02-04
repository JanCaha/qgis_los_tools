# Extract Visible/Invisible Polygons from LoS

Extract individual parts from lines-of-sight as polygons. Works for LoS without target. The line is divided into visible and invisible segments and extended to polygon by knowing angle step between individual LoS.

## Parameters

| Label                        | Name                    | Type                                      | Description                                              |
| ---------------------------- | ----------------------- | ----------------------------------------- | -------------------------------------------------------- |
| LoS layer                    | `LoSLayer`              | [vector: line]                            | LoS layer to extract polygons from.                      |
| Use curvature corrections?   | `CurvatureCorrections`  | [boolean]<br/><br/>Default: `True`        | Should the curvature and refraction corrections be used? |
| Refraction coefficient value | `RefractionCoefficient` | [number] <br/><br/> Default: <br/> `0.13` | Value of refraction coefficient.                         |
| Output layer                 | `OutputLayer`           | [vector: point]                           | Output layer containing points.                          |

## Outputs

| Label        | Name          | Type            | Description                     |
| ------------ | ------------- | --------------- | ------------------------------- |
| Output layer | `OutputLayer` | [vector: point] | Output layer containing points. |

### Fields in the output layer

* __id_observer__ - integer - value from expected field (`id_observer`) in `LoSLayer`
* __id_target__ - integer - value from expected field (`id_target`) in `LoSLayer`
* __visible__ - boolean - is the point visible

## Tool screenshot

![Extract Visible/Invisible Polygons from LoS](../../images/tool_extract_visibility_polygons.png)
	