# Changelog

## version 2.0.0

- rework GUI tools, they now work differently provide more informative messages when something is going on

- `Sampling distance matrix` and `List of Rasters` needed to crate LoS with GUI tools are now stored in the plugin itself

- interactive tools `Create LoS` and `Create LoS No Target Tool` now visualize and can also add LoS to the plugin layer

- introduce **Rasters XML** (**.rastersxml**) file format to store raster list

## version 1.2.1

- fix bad use of numpy to avoid exception

## version 1.2.0

- new tool to extract horizon lines at specific distance

- minor fixes to gui tools (based on tests written for them)

## version 1.1.2

- fix issue with interactive tools not opening properly after closing

## version 1.1.1

- simplify inner working of GUI tools

- fix `Set Camera` GUI tool

## version 1.1 

- update some internals including test

- style python using black and isort

- avoid some warnings in QGIS 3.38

- remove older version of `No Target LoS Tool`

## version 1.0

- addition of all the interactive tools - see websize menu **Interactive tools**

- bugfixes of some issues from 0.7

## version 0.7

- add tools: Create no Target LoS V2, Calculate Object Distances, Calculate Object Sizes, Calculate Parameters Settings, Extract Visible/Invisible Lines from LoS, Extract Visible/Invisible Polygons from LoS

- fixes for tools that work with angles, now round angles to sensible values

- fix both raster editing tools, previously those sometimes shifted the cells of raster, causing it not exactly match the input data

- text updates and changes to tools

- minor fixes all around

- fixes to website (zoomable images)

- internal changes to handling tests  

## version 0.5

- add plugin icon

- add ExtractAsM parameter to Extract Horizon Lines

- changes to underlying LoS classes and minor bug fixes

- ExtractPointsLoSAlgorithm allows to calculate ExtendedAttributes

- doc fixes

- add tag to git to allow searching changes from version

## version 0.4

- change exports to CSV to export to tables (vector data without geometry) to allow loading into QGIS

- add pages to website

- various minor fixes all around

## version 0.2

- update website

- all tools have links (help) to website description

## version 0.1

- first version of the plugin