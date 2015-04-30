'''
    Name:       ChoroplethHillshade

    Authors:    Jacob Wasilkowski | Esri St. Louis
                Jie Cheng | UMASS Medical School

    Notes:      Generates a hillshaded raster surface for choropleth maps.
                Inspired by:
                Stewart, James and Kennelly, Patrick J. (2010).
                "Illuminated Choropleth Maps".
                Annals of the Association of American Geographers, 100(3): 513-534.
                http://www.tandfonline.com/doi/abs/10.1080/00045608.2010.485449#.UtWdcp5dXzh

                Requires ArcGIS for Desktop 10.1 SP1 or higher.

    Created:    December 2012
    Modified:   April 2015
'''

import arcpy
import decimal
import math
import sys

arcpy.env.overwriteOutput = True


def parameter(displayName, name, datatype, parameterType='Required', direction='Input', multiValue=False):
    param = arcpy.Parameter(
        displayName = displayName,
        name = name,
        datatype = datatype,
        parameterType = parameterType,
        direction = direction,
        multiValue = multiValue)

    return param


class Toolbox(object):
    def __init__(self):
        self.label =  'Choropleth Hillshade Toolbox'
        self.canRunInBackground = False
        #list of tool classes associated with this toolbox
        self.tools = [ChoroplethHillshade]


class ChoroplethHillshade(object):
    def __init__(self):
        self.label       = 'Choropleth Hillshade'
        self.description = ('Generates a hillshaded raster surface for choropleth maps.  '
                'Inspired by:</br></br>Stewart, James and Kennelly, Patrick J. (2010).</br>'
                '"Illuminated Choropleth Maps".</br>'
                'Annals of the Association of American Geographers, 100(3): 513-534.</br>')
        self.parameters = [
            parameter('Input Polygon Features', 'inputFC', 'GPFeatureLayer'),
            parameter('Input Field', 'inputField', 'Field'),
            parameter('Raster Cell Size (decimal degrees, such as "0.1" or "0,1", depending on locale)', 'rasterCellSize', 'GPDouble'),
            parameter('Shadow Level', 'shadowLevel', 'GPLong'),
            parameter('Output Raster', 'outputRaster', 'DERasterDataset', direction='Output')
        ]


    def getParameterInfo(self):
        #additional parameter properties
        self.parameters[0].filter.list = ['Polygon']
        self.parameters[1].parameterDependencies = [self.parameters[0].name]
        self.parameters[3].filter.type = 'Range'
        self.parameters[3].filter.list = [1, 10]

        return self.parameters


    def execute(self, parameters, messages):
        inputFC =           parameters[0].valueAsText
        inputField =        parameters[1].valueAsText
        rasterCellSize =    parameters[2].valueAsText
        shadowLevel =       parameters[3].valueAsText
        outputRaster =      parameters[4].valueAsText


        '''tool-specific function definitions'''
        #Check out Spatial Analyst Extension from the License Manager.
        #If unavailable, check out 3D Analyst Extension and skip
        #Focal Statistics, which requires Spatial Analyst.
        def licenseCheck():
            spatialAnalystCheckedOut = False
            if arcpy.CheckExtension('Spatial') == 'Available':
                arcpy.CheckOutExtension('Spatial')
                spatialAnalystCheckedOut = True
            else:
                arcpy.AddMessage('WARNING: This script uses geoprocessing tools that require the Spatial '
                    'Analyst extension. It will attempt to execute with the 3D Analyst extension, but '
                    'will not visually smoothe the final results with Focal Statistics.\n')
                if arcpy.CheckExtension('3D') == 'Available':
                    arcpy.CheckOutExtension('3D')
                else:
                    arcpy.AddMessage('ERROR: At a minimum, this script requires the 3D Analyst Extension.\n')
                    sys.exit()
            return spatialAnalystCheckedOut


        #inputs should be unprojected, since zFactor calculation for hillshading computes in degrees
        def projectionCheck(inputFC):
            spatial_ref = arcpy.Describe(inputFC).SpatialReference
            #spatial_ref.Name   #name of inputFC coordinate system
            if (spatial_ref.Type != 'Geographic'):
                projectedInputFC = r'{0}/projectedInputFeatGCS'.format(arcpy.env.scratchGDB)
                outCS = arcpy.SpatialReference(4326)
                arcpy.management.Project(inputFC, projectedInputFC, outCS)
                arcpy.AddMessage('WARNING: Shadow levels cannot be estimated for projected data.\n'
                    'Input features were reprojected to a geographic coordinate system (GCS_WGS_1984).\n'
                    'Reproject the output choropleth hillshade raster.\n')
                return projectedInputFC
            else:
                return inputFC


        #zFactor calculation adapted from Matt Funk, Esri (2010)
        #http://blogs.esri.com/esri/arcgis/2010/12/15/determining-a-z-factor-for-converting-linear-elevation-units-to-approximate-geographic-coordinates/
        def zFactorEsri(rasterData):
            #get the top and bottom
            desc = arcpy.Describe(rasterData)
            extent = desc.Extent
            extent_split = [extent.XMin,extent.XMin,extent.XMax,extent.XMax]
            top = float(extent_split[3])
            bottom = float(extent_split[1])
            #find the mid-latitude of the dataset
            if top > bottom:
                height = top - bottom
                mid = (height / 2) + bottom
            elif top < bottom:  #unlikely, but just in case
                height = bottom - top
                mid = (height / 2) + top
            else:   #top == bottom # Again, unlikely but just in case
                mid = top
            #convert degrees to radians
            mid = math.radians(mid)
            #find length of degree at equator based on spheroid's semi-major axis
            spatial_reference = desc.SpatialReference
            semi_major_axis = spatial_reference.semiMajorAxis # in meters
            equatorial_length_of_degree = ((2.0 * math.pi * float(semi_major_axis)) / 360.0)
            #function:
            #Z-Factor = 1.0/(111320 * cos(mid-latitude in radians))
            decimal.getcontext().prec = 28
            decimal.getcontext().rounding = decimal.ROUND_UP
            a = decimal.Decimal('1.0')
            #b = decimal.Decimal('111320.0') # number of meters in one degree at equator (approximate using WGS84)
            b = decimal.Decimal(str(equatorial_length_of_degree))
            c = decimal.Decimal(str(math.cos(mid)))
            zFactor = math.fabs(a / (b * c))
            return zFactor


        #scale the Esri zFactor by user shadow level
        def zFactorScaling(shadow, rasterData):
            if int(shadow) <= 10:
                    zFactorFinal = (zFactorEsri(rasterData) * pow(2.5, int(shadow)))
                    return zFactorFinal
            else:   #predefined error message stating that user shadow level exceeds allowable range
                    arcpy.GetIDMessage(854)


        '''geoprocessing logic'''
        try:
            #pre-processing
            spatialAnalystCheckedOut = licenseCheck()   #Spatial or 3D Analyst required
            inputFCProjCheck = projectionCheck(inputFC) #convert inputFC to GCS if it is projected

            #create in-memory copy of input for new field calculation
            arcpy.AddMessage('Creating in-memory copy of input polygon features\n')
            inputInMemory = r'{0}/inputFeature'.format('in_memory')
            arcpy.management.CopyFeatures(inputFCProjCheck, inputInMemory)

            #create a new attribute table field and calculate 'height' values based on Stewart & Kennelley (2010) eq.3
            #   H = 0.0025 * (D/Dmax)^0.455 * Dmax
            #   where:  H is the adjusted height value,
            #           D is the original attribute value,
            #           Dmax is the maximum attribute value
            arcpy.AddMessage('Calculating adjusted attribute "height" values\n')
            height_SK = 'Height_SK'
            arcpy.management.AddField(inputInMemory, height_SK, 'FLOAT')

            #find the maximum value in the attribute field
            attrValues = set()  #initalize empty set
            with arcpy.da.SearchCursor(inputInMemory, [inputField]) as searchCursor:
                for row in searchCursor:
                    attrValues.add(row[0])      #only add unique values to set
            fieldMax = float(max(attrValues))   #identify max attribute value

            #execute field calculation of new heights
            expression = '0.0025 * pow((!{0}!/{1}), 0.455) * {1}'.format(inputField, fieldMax)
            arcpy.management.CalculateField(inputInMemory, height_SK, expression, 'PYTHON_9.3')

            #convert input polygon features to raster
            arcpy.AddMessage('Converting input polygons to raster\n')
            featToRas = r'{0}/featToRas'.format(arcpy.env.scratchGDB)
            arcpy.conversion.FeatureToRaster(inputInMemory, height_SK, featToRas, rasterCellSize)

            #copy the first raster to scaled 8-bit format to forcefully include background values
            #(the raster background extent is necessary for edge shadows)
            ## TO DO: expand the bbox extents to account for long edge shadows
            featToRasCopy = r'{0}/featToRasCopy'.format('in_memory')
            arcpy.management.CopyRaster(featToRas, featToRasCopy, pixel_type='8_BIT_UNSIGNED', scale_pixel_value='ScalePixelValue')

            #calculate the scaled zFactor for the Hillshade tool
            arcpy.AddMessage('Calculating scaled z-factor for hillshading\n')
            zFactorHillshade = zFactorScaling(shadowLevel, featToRasCopy)

            #hillshade & focal stats
            if spatialAnalystCheckedOut:    #if Spatial Analyst available, use Hillshade and Focal Stats
                arcpy.AddMessage('Creating hillshade\n')
                hillshade = arcpy.sa.Hillshade(featToRasCopy, '315', '45', 'SHADOWS', zFactorHillshade)
                hillshadeFilePath = r'{0}/hillshade'.format(arcpy.env.scratchGDB)
                hillshade.save(hillshadeFilePath)

                arcpy.AddMessage('Performing focal statistics\n')
                neighborhood = arcpy.sa.NbrRectangle(3, 3, 'CELL')
                focalStats = arcpy.sa.FocalStatistics(hillshadeFilePath, neighborhood, 'MEAN', 'DATA')
                focalStats.save(outputRaster)

            else:   #otherwise, use Hillshade and skip Focal Stats
                arcpy.AddMessage('Creating hillshade\n')
                arcpy.HillShade_3d(featToRasCopy, outputRaster, '315', '45', 'SHADOWS', zFactorHillshade)

            arcpy.management.Delete(featToRas)
            arcpy.management.Delete('in_memory')

            return


        except Exception as ex:
            arcpy.AddMessage('ERROR: {0}'.format(ex))
