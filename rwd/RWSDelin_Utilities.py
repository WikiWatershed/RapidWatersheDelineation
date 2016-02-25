
import sys
import shapefile
from shapely.wkb import loads
import pandas as pd
import numpy as np
from shapely.geometry import Point, LineString, mapping, shape
from shapely.ops import cascaded_union
from fiona import collection
from osgeo import gdal, ogr

from shapely.geometry import shape, mapping, MultiLineString
import os
import re
import os.path
import osr
from math import *
import glob
from shapely.ops import unary_union
import fiona
import itertools


def Raster_to_Polygon(input_file, output_file):
    gdal.UseExceptions()
    src_ds = gdal.Open(input_file)
    if src_ds is None:
        # print 'Unable to open %s' % src_filename
        sys.exit(1)
    try:
        srcband = src_ds.GetRasterBand(1)
        srd = srcband.GetMaskBand()

    except RuntimeError as e:
     # for example, try GetRasterBand(10)
     # print 'Band ( %i ) not found' % band_num
     # print e
        sys.exit(1)
    dst_layername = output_file
    drv = ogr.GetDriverByName("ESRI Shapefile")
    dst_ds = drv.CreateDataSource(dst_layername + ".shp")
    dst_layer = dst_ds.CreateLayer(dst_layername, srs=None)
    gdal.Polygonize(srcband, srd, dst_layer, -1, [], callback=None)


def polygon_dissolve(input_polygon, dissolve_watershed_Name, projection):
    input_polygon1 = input_polygon + ".shp"
    output_polygon = dissolve_watershed_Name + ".shp"
    with fiona.open(input_polygon1, "r") as input:
        schema = {'geometry': 'Polygon', 'properties': {'GRIDCODE': 'str'}}
        with fiona.open(
                output_polygon, "w", "ESRI Shapefile", schema, projection) as output:
            shapes = []
            for f in input:
                shapes.append(shape(f['geometry']).buffer(.0000001))
                merged = cascaded_union(shapes)
                output.write({
                    'properties': {
                        'GRIDCODE': '1'
                    },
                    'geometry': mapping(merged)
                })


def polygon_dissolve_byfield(inputshapfile, outputshapefile):
    with fiona.open(inputshapfile) as input:
        meta = input.meta
        # print('srt')
        with fiona.open(outputshapefile, 'w', **meta) as output:
            # groupby clusters consecutive elements of an iterable which have
            # the same key so you must first sort the features by the 'STATEFP'
            # field
            e = sorted(input, key=lambda k: k['properties']['GRIDCODE'])
        # print(e)
            # group by the 'STATEFP' field
            for key, group in itertools.groupby(
                    e, key=lambda x: x['properties']['GRIDCODE']):
                properties, geom = zip(
                    *[(feature['properties'], shape(feature['geometry'])) for feature in group])
                # write the feature, computing the unary_union of the elements
                # in the group with the properties of the first element in the
                # group
                output.write({'geometry': mapping(
                    unary_union(geom)), 'properties': properties[0]})


def point_in_Polygon(dir, watershed_shapefile, point):
    os.chdir(dir)
    file = watershed_shapefile + ".shp"
    file1 = ogr.Open(file)
    point1 = point
    layer1 = file1.GetLayerByName(watershed_shapefile)

    polygon1 = layer1.GetNextFeature()
    g = len(layer1)

    while polygon1 is not None:
        geomPolygon = loads(polygon1.GetGeometryRef().ExportToWkb())
        if geomPolygon.contains(point1):
            name1 = polygon1.GetField("GRIDCODE")
            return (name1)

        polygon1 = layer1.GetNextFeature()


def createBuffer(inputfn, outputBufferfn, bufferDist):
    inputds = ogr.Open(inputfn)
    inputlyr = inputds.GetLayer()

    shpdriver = ogr.GetDriverByName('ESRI Shapefile')
    if os.path.exists(outputBufferfn):
        shpdriver.DeleteDataSource(outputBufferfn)
    outputBufferds = shpdriver.CreateDataSource(outputBufferfn)
    bufferlyr = outputBufferds.CreateLayer(
        outputBufferfn, geom_type=ogr.wkbPolygon)
    featureDefn = bufferlyr.GetLayerDefn()

    for feature in inputlyr:
        ingeom = feature.GetGeometryRef()
        geomBuffer = ingeom.Buffer(bufferDist)

        outFeature = ogr.Feature(featureDefn)
        outFeature.SetGeometry(geomBuffer)
        bufferlyr.CreateFeature(outFeature)


def createShape_from_Point(x, y, file, projection):
    point1 = Point(x, y)
    schema = {
        'geometry': 'Point',
        'properties': {
            'Lat': 'float',
            'Lon': 'float',
            'ID': 'int'}}
    with collection(file + ".shp", "w", "ESRI Shapefile", schema, projection) as output:
        output.write({
            'properties': {
                'Lat': y,
                'Lon': x,
                'ID': 1,
            },
            'geometry': mapping(point1)
        })


def define_projection(input_shapefile, Output_shapefile, projection):
    input_shapefile1 = input_shapefile + ".shp"
    output_shape = Output_shapefile + ".shp"
    with fiona.open(input_shapefile1) as source:
        # change only the geometry of the schema: LineString -> Point
        source.schema['geometry'] = "Point"
    # write the Point shapefile
        with fiona.open(output_shape, 'w', 'ESRI Shapefile', source.schema.copy(), projection) as output:
            for elem in source:
                # GeoJSON to shapely geometry
                geom = shape(elem['geometry'])
                # shapely centroid to GeoJSON
                elem['geometry'] = mapping(geom)
                output.write(elem)


def complementary_gagewatershed(gageIDfile, num):

    data = np.loadtxt(gageIDfile, skiprows=1)
    df = pd.DataFrame(data=data, columns=['gageID', 'ID_DOWN'])

    up1 = []
    up2 = []

    def upstream_watershed(num):
        if num == -1:
            up2.append(-1)
            return up2
        else:
            mask = df[['ID_DOWN']].isin([num]).all(axis=1)
            data_mask = df.ix[mask]
            length_data_mask = len(data_mask)
            data_as_matrix = np.asmatrix(data_mask)
            if(length_data_mask > 0):
                for i in range(0, length_data_mask):
                    x3 = np.asarray(data_as_matrix[i])
                    x4 = x3[0, 0]
                    up1.append(x4)
                    a1 = upstream_watershed(x4)

                return (up1)
            else:
                up2.append(-1)
                return up2

    upstream_watershed_ID = upstream_watershed(num)
    return (upstream_watershed_ID)


def upstream_gagewatershed(gageIDfile,num,dir_main):
   os.chdir(dir_main)
   data=np.loadtxt(gageIDfile, skiprows=1)
   df = pd.DataFrame(data = data, columns=['id', 'iddown'])
   up=[]
   if num == -1:
      up.append(-1)
   else:
      mask = df[['iddown']].isin([num]).all(axis=1)
      data_mask=df.ix[mask]
      id_all=data_mask['id']
      length_data_mask=len(id_all)
      data_as_matrix=np.asarray(id_all)
      up.append(data_as_matrix)

   return (data_as_matrix)




def extract_value_from_raster(rasterfile, pointshapefile):
    #src_filename = 'E:\\USU_Research_work\\MMW_PROJECT\\Point_watershed\\A1_test\\Subwatershed4\\subwatershed_4dist.tif'
    #shp_filename = 'E:\\USU_Research_work\\MMW_PROJECT\\Point_watershed\\A1_test\\Test1\\mypoint_proj.shp'
    src_filename = rasterfile
    shp_filename = pointshapefile
    src_ds = gdal.Open(src_filename)
    gt = src_ds.GetGeoTransform()
    rb = src_ds.GetRasterBand(1)

    ds = ogr.Open(shp_filename)
    lyr = ds.GetLayer()
    for feat in lyr:
        geom = feat.GetGeometryRef()
        mx, my = geom.GetX(), geom.GetY()  # coord in map units
        px = int((mx - gt[0]) / gt[1])  # x pixel
        py = int((my - gt[3]) / gt[5])  # y pixel
        # Assumes 16 bit int aka 'short'
        Pixel_Data = rb.ReadAsArray(px, py, 1, 1)
        # use the 'short' format code (2 bytes) not int (4 bytes)
        Pixel_Val = Pixel_Data[0, 0]
        return Pixel_Val  # intval is a tuple, length=1 as we only asked for 1 pixel value


def Reach_Upstream_Edge(
        New_Gage_watershed_Dissolve,
        up_ID,
        Pre_process_TauDEM_dir,
        dir_name,
        ID,
        out_dir):
    os.chdir(out_dir)
    file2=New_Gage_watershed_Dissolve+'.shp'
    file11=ogr.Open(file2)
    layer12 = file11.GetLayerByName(New_Gage_watershed_Dissolve)
    polygon2= layer12.GetNextFeature()
    geomPolygon2 = loads(polygon2.GetGeometryRef().ExportToWkb())

    subwatershed_ID=ID
    compli_ID=[]
    for i in range(0,len(up_ID)):

        subwatershed_dir=str(Pre_process_TauDEM_dir)+'/Subwatershed_ALL/'+dir_name+str(int(up_ID[i]))
        os.chdir(subwatershed_dir)
        inputfn = 'subwatershed_'+str(int(up_ID[i]))+'.shp'
        file1=ogr.Open(inputfn)
        layer1 = file1.GetLayerByName('subwatershed_'+str(int(up_ID[i])))
        polygon1= layer1.GetNextFeature()
        geomPolygon = loads(polygon1.GetGeometryRef().ExportToWkb())
        if geomPolygon.intersects(geomPolygon2):
          geomPoly=geomPolygon.difference(geomPolygon2)
          name1 = polygon1.GetField("GRIDCODE")
         # print (name1)
          if(name1!=subwatershed_ID):
            x1=round(list(geomPolygon.centroid.xy[0])[0],5)
            y1=round(list(geomPolygon.centroid.xy[1])[0],5)
            x2=round(list(geomPoly.centroid.xy[0])[0],5)
            y2=round(list(geomPoly.centroid.xy[1])[0],5)
            if((x1!=x2)|(y1!=y2)):
                compli_ID.append(name1)
                #print (name1)
            else:
                compli_ID.append(-1)
    return compli_ID


def GAUGE_WATERSHED(
        MPH_dir,
        np,
        TauDEM_dir,
        Grid_dir,
        Grid_Name,
        Output_dir,
        Outlet_Point,
        New_Gage_watershed_Name):
    commands = []
    commands.append(os.path.join(MPH_dir, "mpiexec"))
    commands.append("-np")
    commands.append(str(np))
    commands.append(os.path.join(TauDEM_dir, "gagewatershed"))
    commands.append("-p")
    commands.append(os.path.join(Grid_dir, Grid_Name + "p.tif"))
    commands.append("-o")
    commands.append(os.path.join(Output_dir, Outlet_Point))
    commands.append("-gw")
    commands.append(os.path.join(Output_dir, New_Gage_watershed_Name + ".tif"))
    commands.append("-id")
    commands.append(os.path.join(Output_dir, New_Gage_watershed_Name + ".txt"))
    fused_command = ''.join(['"%s" ' % c for c in commands])
    return fused_command


def MOVEOUTLETTOSTREAMS(
        MPH_dir,
        np,
        TauDEM_dir,
        Subwatershed_dir,
        Grid_Name,
        Output_dir,
        Outlet_Point,
        Distance_thresh):
    commands = []
    commands.append(os.path.join(MPH_dir, "mpiexec"))
    commands.append("-np")
    commands.append(str(np))
    commands.append(os.path.join(TauDEM_dir, "moveoutletstostrm"))
    commands.append("-p")
    commands.append(os.path.join(Subwatershed_dir, Grid_Name + "p.tif"))
    commands.append("-src")
    commands.append(os.path.join(Subwatershed_dir, Grid_Name + "src1.tif"))
    commands.append("-o")
    commands.append(os.path.join(Output_dir, Outlet_Point + ".shp"))
    commands.append("-om")
    commands.append(os.path.join(Output_dir, "New_Outlet.shp"))
    commands.append("-md")
    commands.append(str(Distance_thresh))
    fused_command = ''.join(['"%s" ' % c for c in commands])
    return fused_command


def remove_file_directory(dir, file):
        #pattern = "^subwatershed_buffer"
    pattern = file
    path = dir
    for root, dirs, files in os.walk(path):
        for file in filter(lambda x: re.match(pattern, x), files):
            os.remove(os.path.join(root, file))


def purge(dir, pattern):
    for f in os.listdir(dir):
        if re.search(pattern, f):
            os.unlink(os.path.join(dir, f))


def remove_file(file):
    #pattern = "^subwatershed_buffer"
    FileName = file
    driver = ogr.GetDriverByName("ESRI Shapefile")
    if os.path.exists(FileName):
        driver.DeleteDataSource(FileName)


def poly2line(input_poly, output_line):

    source_ds = ogr.Open(input_poly)
    source_layer = source_ds.GetLayer()

    # polygon2geometryCollection
    geomcol = ogr.Geometry(ogr.wkbGeometryCollection)
    for feat in source_layer:
        geom = feat.GetGeometryRef()
        ring = geom.GetGeometryRef(0)
        geomcol.AddGeometry(ring)

    # geometryCollection2shp
    shpDriver = ogr.GetDriverByName("ESRI Shapefile")
    if os.path.exists(output_line):
        shpDriver.DeleteDataSource(output_line)
    outDataSource = shpDriver.CreateDataSource(output_line)
    outLayer = outDataSource.CreateLayer(
        output_line, geom_type=ogr.wkbMultiLineString)
    featureDefn = outLayer.GetLayerDefn()
    outFeature = ogr.Feature(featureDefn)
    outFeature.SetGeometry(geomcol)
    outLayer.CreateFeature(outFeature)


def multipoly2poly(in_lyr, out_lyr):
    for in_feat in in_lyr:
        geom = in_feat.GetGeometryRef()
        if geom.GetGeometryName() == 'MULTIPOLYGON':
            for geom_part in geom:
                addPolygon(geom_part.ExportToWkb(), out_lyr)
        else:
            addPolygon(geom.ExportToWkb(), out_lyr)


def addPolygon(simplePolygon, out_lyr):
    featureDefn = out_lyr.GetLayerDefn()
    polygon = ogr.CreateGeometryFromWkb(simplePolygon)
    out_feat = ogr.Feature(featureDefn)
    out_feat.SetGeometry(polygon)
    out_lyr.CreateFeature(out_feat)


def convertMPtoPoly(multipolygon, singlepolygon):
    driver = ogr.GetDriverByName('ESRI Shapefile')
    in_ds = driver.Open(multipolygon, 0)
    in_lyr = in_ds.GetLayer()
    outputshp = singlepolygon
    if os.path.exists(outputshp):
        driver.DeleteDataSource(outputshp)
    out_ds = driver.CreateDataSource(outputshp)
    out_lyr = out_ds.CreateLayer('poly', geom_type=ogr.wkbPolygon)
    multipoly2poly(in_lyr, out_lyr)


def reproject(input, output, geom_type):

    driver = ogr.GetDriverByName('ESRI Shapefile')

    # input SpatialReference
    inSpatialRef = osr.SpatialReference()
    inSpatialRef.ImportFromEPSG(4326)

    # output SpatialReference
    outSpatialRef = osr.SpatialReference()
    outSpatialRef.ImportFromEPSG(102003)

    # create the CoordinateTransformation
    coordTrans = osr.CoordinateTransformation(inSpatialRef, outSpatialRef)

    # get the input layer
    inDataSet = driver.Open(input + '.shp')
    inLayer = inDataSet.GetLayer()

   # create the output layer
    outputShapefile = output + '.shp'
    if os.path.exists(outputShapefile):
        driver.DeleteDataSource(outputShapefile)
    outDataSet = driver.CreateDataSource(outputShapefile)
    outLayer = outDataSet.CreateLayer(output, geom_type=geom_type)

# add fields
    inLayerDefn = inLayer.GetLayerDefn()
    for i in range(0, inLayerDefn.GetFieldCount()):
        fieldDefn = inLayerDefn.GetFieldDefn(i)
        outLayer.CreateField(fieldDefn)

# get the output layer's feature definition
    outLayerDefn = outLayer.GetLayerDefn()

# loop through the input features
    inFeature = inLayer.GetNextFeature()
    while inFeature:
        # get the input geometry
        geom = inFeature.GetGeometryRef()
    # reproject the geometry
        geom.Transform(coordTrans)
    # create a new feature
        outFeature = ogr.Feature(outLayerDefn)
    # set the geometry and attribute
        outFeature.SetGeometry(geom)
        for i in range(0, outLayerDefn.GetFieldCount()):
            outFeature.SetField(
                outLayerDefn.GetFieldDefn(i).GetNameRef(),
                inFeature.GetField(i))
    # add the feature to the shapefile
        outLayer.CreateFeature(outFeature)
    # destroy the features and get the next input feature
        outFeature.Destroy()
        inFeature.Destroy()
        inFeature = inLayer.GetNextFeature()

# close the shapefiles
    inDataSet.Destroy()
    outDataSet.Destroy()


def split(line_string, point):
    coords = line_string.coords
    j = None

    for i in range(len(coords) - 1):
        if LineString(coords[i:i + 2]).intersects(point):
            j = i
            break

    assert j is not None

    # Make sure to always include the point in the first group
    if Point(coords[j + 1:j + 2]).equals(point):
        return coords[:j + 2], coords[j + 1:]
    else:
        return coords[:j + 1], coords[j:]


def Get_Watershed_Attributes(
        Outlet_Point,
        Point_Watershed,
        elev_file,
        Max_elev_file,
        Ad8_weigthed_file,
        Ad8_file,
        plen_file,
        tlen_file,
        gord_file,
        dir_subwatershed,
        out_dir):

    os.chdir(out_dir)
    elev_file_with_path=os.path.join(dir_subwatershed,elev_file)
    Max_elev_file_with_path=os.path.join(dir_subwatershed,Max_elev_file)
    Ad8_weigthed_file_with_path=os.path.join(dir_subwatershed,Ad8_weigthed_file)
    Ad8_file_with_path=os.path.join(dir_subwatershed,Ad8_file)
    gord_file_with_path=os.path.join(dir_subwatershed,gord_file)
    plen_file_with_path=os.path.join(dir_subwatershed,plen_file)
    tlen_file_with_path=os.path.join(dir_subwatershed,tlen_file)

    Basin_length=extract_value_from_raster(plen_file_with_path,Outlet_Point)
    Stream_Order=extract_value_from_raster(gord_file_with_path,Outlet_Point)
    Total_stream_length= extract_value_from_raster(tlen_file_with_path,Outlet_Point)
    Max_elev=extract_value_from_raster(Max_elev_file_with_path,Outlet_Point)
    outlet_elev=extract_value_from_raster(elev_file_with_path,Outlet_Point)
    Ad8_weighted=extract_value_from_raster(Ad8_weigthed_file_with_path,Outlet_Point)
    Ad8=extract_value_from_raster(Ad8_file_with_path,Outlet_Point)
    Area=Ad8*10.3*7.85/(1000*1000) ## use Spehorid.R function for calculating dxc and dyc . choose median value for dyc and dxc which is approximations
    Basin_Relief= Max_elev-outlet_elev
    Relief_Ratio=Basin_Relief/Basin_length
    Avg_slope=Ad8_weighted/Ad8
    Drainage_Density=Total_stream_length/(Area*1000)
    Length_Overland_flow=1/(2*Drainage_Density)
    source = ogr.Open(Point_Watershed+".shp", 1)
    layer = source.GetLayer()
    layer_defn = layer.GetLayerDefn()
    new_field = ogr.FieldDefn('Area', ogr.OFTReal)
    layer.CreateField(new_field)
    new_field = ogr.FieldDefn('BasinLen', ogr.OFTReal)
    layer.CreateField(new_field)
    new_field = ogr.FieldDefn('Strord', ogr.OFTReal)
    layer.CreateField(new_field)
    new_field = ogr.FieldDefn('StrLen', ogr.OFTReal)
    layer.CreateField(new_field)
    new_field = ogr.FieldDefn('DrnDen',ogr.OFTReal)
    layer.CreateField(new_field)
    new_field = ogr.FieldDefn('AvgOLF', ogr.OFTReal)
    layer.CreateField(new_field)
    new_field = ogr.FieldDefn('BR',ogr.OFTReal)
    layer.CreateField(new_field)
    new_field = ogr.FieldDefn('RR', ogr.OFTReal)
    layer.CreateField(new_field)
    new_field = ogr.FieldDefn('Avgslp', ogr.OFTReal)
    layer.CreateField(new_field)
    feature = layer.GetFeature(0)
    my_at_val=[0,Area,float(Basin_length)/1000.00,Stream_Order, float(Total_stream_length/1000.0),float(Drainage_Density),float(Length_Overland_flow),float(Basin_Relief),float(Relief_Ratio), float(Avg_slope) ]
    for i in range(1, 10):

        feature.SetField( i, float(my_at_val[i]))

    layer.SetFeature(feature)

    source = None
