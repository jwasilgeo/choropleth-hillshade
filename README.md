#Choropleth Hillshade
###A Python Geoprocessing Toolbox for ArcGIS

[![No Maintenance Intended](http://unmaintained.tech/badge.svg)](http://unmaintained.tech/)

Generates a hillshaded raster surface for choropleth maps.  But why?
* Show off your within-class variability!
* Enable thematic maps to have more than _just_ 2 dimensions.
* Experiment with displaying bivariate data.
* Skip the colours altogether, if you can handle it.

For input, this geoprocessing tool only requires a polygon feature class (or shapefile) with attributes appropriate for choropleth mapping, such as densities or percentages.

An illuminated/shaded relief raster based on the attribute of choice (e.g. population density per county) is the output of this tool (*left*), which can be overlayed with the original feature class (*right*).

![ChoroSample](docs/ChoroSample.png)

**Raster cell size** and overall **shadow length** are set as tool parameters.  Compare the different polygon "heights" and the shadows they can cast below:

![Shadow4](docs/Shadow4.png)

![Shadow5](docs/Shadow5.png)

![Shadow6](docs/Shadow6.png)

#### Other info:
* Software: This PYT requires ArcGIS for Desktop (ArcMap) 10.1 SP1 or higher, with access to either the Spatial Analyst or 3D Analyst extension.
* **Important ArcMap environment options:**
  * Navigate to: _ArcMap --> Geoprocessing menu --> Geoprocessing Options... -->_
  * Check ON "Overwrite the outputs..."
  * Check OFF "Background Processing"
* **Raster Cell Size** tool option: numeric values with units of degrees lat/long; for example, try `0.1` or `0,1` depending on your locale, and then continue to experiment with smaller values.

#### Inspiration:
* Stewart, James and Kennelly, Patrick J. (2010).
["Illuminated Choropleth Maps"](http://www.tandfonline.com/doi/abs/10.1080/00045608.2010.485449#.UtWdcp5dXzh).
*Annals of the Association of American Geographers*, 100(3): 513-534.

#### Authors:
* Jacob Wasilkowski | Esri St. Louis
* Jie Cheng | UMASS Medical School

#### Contributing:
* Find something wrong or have an idea for a new feature? We welcome submitting new issues and requests.
* License: MIT. More info [here](LICENSE).
