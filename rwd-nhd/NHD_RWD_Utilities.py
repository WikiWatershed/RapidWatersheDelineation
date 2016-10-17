
import shapely
import numpy as np
import fiona

from shapely.wkb import loads
import pandas as pd
import numpy as np
from shapely.geometry import Point, LineString
from shapely.ops import cascaded_union
from fiona import collection
from osgeo import gdal,ogr
from shapely.geometry import shape, mapping
import os, re, os.path
import osr
from math import *
import time
from shapely.ops import unary_union
import fiona
import itertools


# TODO: Seems this function is not needed - Delete it
def Raster_to_Polygon(input_file, output_file):
    gdal.UseExceptions()
    src_ds = gdal.Open(input_file)
    if src_ds is None:
        print ('Unable to open %s' % input_file)
        sys.exit(1)
    try:
        srcband = src_ds.GetRasterBand(1)
        srd=srcband.GetMaskBand()

    except RuntimeError as e:
        print (e.message)
        sys.exit(1)

    dst_layername = output_file
    drv = ogr.GetDriverByName("ESRI Shapefile")
    dst_ds = drv.CreateDataSource(dst_layername + ".shp")
    dst_layer = dst_ds.CreateLayer(dst_layername, srs=None )
    gdal.Polygonize( srcband,srd, dst_layer, -1, [], callback=None)


# TODO: Seems this function is not needed - Delete it
def polygon_dissolve(input_polygon, dissolve_watershed_name, projection):
    input_polygon1 = input_polygon + ".shp"
    output_polygon = dissolve_watershed_name + ".shp"
    with fiona.open(input_polygon1, "r") as input:
        schema = { 'geometry': 'Polygon', 'properties': {'GRIDCODE': 'str'}}
        with fiona.open(output_polygon, "w", "ESRI Shapefile", schema, projection) as output:
            shapes = []
            for f in input:
                shapes.append( shape(f['geometry']).buffer(1))
                merged = cascaded_union(shapes)
                output.write({
                      'properties': {
                      'GRIDCODE': '1'
                            },
                      'geometry': mapping(merged)
                    })


# TODO: Seems this function is not needed - Delete it
def polygon_dissolve_byfield(inputshapfile, outputshapefile):
    with fiona.open(inputshapfile) as input:
        meta = input.meta
        with fiona.open(outputshapefile, 'w',**meta) as output:
            # groupby clusters consecutive elements of an iterable which have the same key so you must first
            # sort the features by the 'STATEFP' field
            e = sorted(input, key=lambda k: k['properties']['GRIDCODE'])

        for key, group in itertools.groupby(e, key=lambda x: x['properties']['GRIDCODE']):
            properties, geom = zip(*[(feature['properties'], shape(feature['geometry'])) for feature in group])
            # write the feature, computing the unary_union of the elements in the group with the properties of the
            # first element in the group
            output.write({'geometry': mapping(unary_union(geom)), 'properties': properties[0]})


# TODO: Seems this function is not needed - Delete it
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
            return name1

        polygon1 = layer1.GetNextFeature()


def create_buffer(inputfn, outputBufferfn, bufferDist):
    inputds = ogr.Open(inputfn)
    inputlyr = inputds.GetLayer()

    shpdriver = ogr.GetDriverByName('ESRI Shapefile')
    if os.path.exists(outputBufferfn):
        shpdriver.DeleteDataSource(outputBufferfn)
    outputBufferds = shpdriver.CreateDataSource(outputBufferfn)
    bufferlyr = outputBufferds.CreateLayer(outputBufferfn, geom_type=ogr.wkbPolygon)
    featureDefn = bufferlyr.GetLayerDefn()

    for feature in inputlyr:
        ingeom = feature.GetGeometryRef()
        geomBuffer = ingeom.Buffer(bufferDist)
        outFeature = ogr.Feature(featureDefn)
        outFeature.SetGeometry(geomBuffer)
        bufferlyr.CreateFeature(outFeature)


def create_shape_from_point(x, y, file, projection):
    point = Point(x,y)
    schema = {'geometry': 'Point', 'properties': {'Lat': 'float', 'Lon': 'float', 'ID': 'int'}}
    with collection(file + ".shp", "w", "ESRI Shapefile", schema, projection) as output:
        output.write({
                'properties': {
                    'Lat': y,
                    'Lon': x,
                    'ID': 1,
                },
                'geometry': mapping(point)
            })


# TODO: Seems this function is not needed - Delete it
def define_projection(input_shapefile, output_shapefile, projection):
    input_shapefile1 = input_shapefile + ".shp"
    output_shape = output_shapefile + ".shp"
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


# TODO: Seems this function is not needed - Delete it
def complementary_gagewatershed_NHD(gageIDfile, num1, dir_main):
    os.chdir(dir_main)
    data=np.loadtxt(gageIDfile, skiprows=1)
    df = pd.DataFrame(data=data, columns=['id', 'iddown'])
    orgid=num1
    up1=[]
    up2=[]

    def upstream_watershed(num):
        if num == -1:
            up2.append(-1)

        else:
            mask = df[['iddown']].isin([num]).all(axis=1)
            data_mask = df.ix[mask]
            id_all = data_mask['id']
            length_data_mask = len(id_all)
            data_as_array = np.asarray(id_all)
            if length_data_mask > 0:
                for i in range(0, length_data_mask):
                    x3 = data_as_array[i]

                    up2.append(x3)
                    if x3 != num1:
                        upstream_watershed(x3)

            else:
                up2.append(-1)
        return up2

    print(num1)
    upstream_watershed_ID = upstream_watershed(num1)
    print("done")
    return upstream_watershed_ID


def complementary_gagewatershed(gageIDfile, num):
    data = np.loadtxt(gageIDfile, skiprows=1)
    df = pd.DataFrame(data=data, columns=['id', 'iddown'])

    up1 = []
    up2 = []

    def upstream_watershed(num):
        if num == -1:
            up2.append(-1)
            return up2
        else:
            mask = df[['iddown']].isin([num]).all(axis=1)
            data_mask = df.ix[mask]
            length_data_mask = len(data_mask)
            data_as_matrix = np.asmatrix(data_mask)
            if length_data_mask > 0:
                for i in range(0, length_data_mask):
                    x3 = np.asarray(data_as_matrix[i])
                    x4 = x3[0, 0]
                    up1.append(x4)
                    # TODO: Seems the following statement can be deleted
                    a1 = upstream_watershed(x4)

                return up1
            else:
                up2.append(-1)
                return up2

    upstream_watershed_id = upstream_watershed(num)
    return upstream_watershed_id


# TODO: Seems this function is not needed - Delete it
def upstream_gagewatershed(gageIDfile, num, dir_main):
    os.chdir(dir_main)
    data = np.loadtxt(gageIDfile, skiprows=1)
    df = pd.DataFrame(data = data, columns=['id', 'iddown'])
    up = []
    if num == -1:
        up.append(-1)
    else:
        mask = df[['iddown']].isin([num]).all(axis=1)
        data_mask = df.ix[mask]
        id_all=data_mask['id']
        length_data_mask = len(id_all)
        data_as_matrix = np.asarray(id_all)
        up.append(data_as_matrix)

    return data_as_matrix


def extract_value_from_raster(rasterfile, pointshapefile):
    src_filename = rasterfile
    shp_filename = pointshapefile
    src_ds = gdal.Open(src_filename)
    gt = src_ds.GetGeoTransform()
    rb = src_ds.GetRasterBand(1)

    ds = ogr.Open(shp_filename)
    lyr = ds.GetLayer()
    for feat in lyr:
        geom = feat.GetGeometryRef()
        mx, my = geom.GetX(), geom.GetY()   # coord in map units
        px = int((mx - gt[0]) / gt[1])  # x pixel
        py = int((my - gt[3]) / gt[5])  # y pixel
        pixel_data = rb.ReadAsArray(px, py, 1, 1)  # Assumes 16 bit int aka 'short'
        pixel_val = pixel_data[0, 0]    # use the 'short' format code (2 bytes) not int (4 bytes)
        return pixel_val    #intval is a tuple, length=1 as we only asked for 1 pixel value


def extract_value_from_raster_point(rasterfile, x, y):
    src_filename = rasterfile
    src_ds = gdal.Open(src_filename)
    gt = src_ds.GetGeoTransform()
    rb = src_ds.GetRasterBand(1)

    mx = float(x)
    my = float(y)

    px = int((mx - gt[0]) / gt[1])  # x pixel
    py = int((my - gt[3]) / gt[5])  # y pixel
    pixel_data = rb.ReadAsArray(px, py, 1, 1)     # Assumes 16 bit int aka 'short'
    pixel_val = pixel_data[0, 0]    # use the 'short' format code (2 bytes) not int (4 bytes)
    return pixel_val    # intval is a tuple, length=1 as we only asked for 1 pixel value


# TODO: Seems this function is not needed - Delete it
def Reach_Upstream_Edge(New_Gage_watershed_Dissolve,up_ID,Pre_process_TauDEM_dir,dir_name,ID,out_dir):

    os.chdir(out_dir)
    file2=New_Gage_watershed_Dissolve+'.shp'
    file11=ogr.Open(file2)
    layer12 = file11.GetLayerByName(New_Gage_watershed_Dissolve)
    polygon2= layer12.GetNextFeature()
    geomPolygon2 = loads(polygon2.GetGeometryRef().ExportToWkb())
    print(up_ID)
    subwatershed_ID=ID
    compli_ID=[]

    for i in range(0,len(up_ID)):
        subwatershed_dir=str(Pre_process_TauDEM_dir)+'\\Subwatershed_ALL\\'+dir_name+str(int(up_ID[i]))
        os.chdir(subwatershed_dir)
        inputfn = 'subwatershed_'+str(int(up_ID[i]))+'.shp'
        file1=ogr.Open(inputfn)
        layer1 = file1.GetLayerByName('subwatershed_'+str(int(up_ID[i])))
        polygon1= layer1.GetNextFeature()
        geomPolygon = loads(polygon1.GetGeometryRef().ExportToWkb())

        if geomPolygon.intersects(geomPolygon2):
          geomPoly=geomPolygon.difference(geomPolygon2)
          name1 = polygon1.GetField("GRIDCODE")

          if(name1!=subwatershed_ID):
            x1=round(list(geomPolygon.centroid.xy[0])[0],5)
            y1=round(list(geomPolygon.centroid.xy[1])[0],5)
            x2=round(list(geomPoly.centroid.xy[0])[0],5)
            y2=round(list(geomPoly.centroid.xy[1])[0],5)
            if((x1!=x2)|(y1!=y2)):
                print(x1,y1)
                print(x2,y2)
                compli_ID.append(name1)
                print (name1)
            else:
                compli_ID.append(-1)
    return compli_ID


def get_gauge_watershed_command(mph_dir, np, taudem_dir, grid_dir, grid_name, output_dir, outlet_point,
                                new_gage_watershed_name):
    commands = []
    commands.append(os.path.join(mph_dir, "mpiexec"))
    commands.append("-n")
    commands.append(str(np))
    commands.append(os.path.join(taudem_dir, "GageWatershed"))
    commands.append("-p")
    commands.append(os.path.join(grid_dir, grid_name + "p.tif"))
    commands.append("-o")
    commands.append(os.path.join(output_dir, outlet_point))
    commands.append("-gw")
    commands.append(os.path.join(output_dir, new_gage_watershed_name + ".tif"))
    commands.append("-id")
    commands.append(os.path.join(output_dir, new_gage_watershed_name + ".txt"))
    commands.append("-upid")
    commands.append(os.path.join(output_dir, "upwacoor.txt"))
    fused_command = ''.join(['"%s" ' % c for c in commands])
    return fused_command


def generate_moveoutletstostream_command(np, Subwatershed_dir, Grid_Name,Output_dir, Outlet_Point, Distance_thresh):
    commands = []
    commands.append("mpiexec")
    commands.append("-n")
    commands.append(str(np))
    commands.append("moveoutletstostreams")
    commands.append("-p")
    commands.append(os.path.join(Subwatershed_dir,Grid_Name + "p.tif"))
    commands.append("-src")
    commands.append(os.path.join(Subwatershed_dir, Grid_Name + "src1.tif"))
    commands.append("-o")
    commands.append(os.path.join(Output_dir, Outlet_Point + ".shp"))
    commands.append("-om")
    commands.append(os.path.join(Output_dir, "New_Outlet.shp"))
    commands.append("-md")
    commands.append(str(Distance_thresh))
    fused_command = ' '.join(['"%s" ' % c for c in commands])
    return fused_command


# TODO: Seems this function is not needed - Delete it
def remove_file_directory(dir,file):
    pattern = file
    path = dir
    for root, dirs, files in os.walk(path):
        for file in filter(lambda x: re.match(pattern, x), files):
            os.remove(os.path.join(root, file))


def purge(dir, pattern):
    for f in os.listdir(dir):
        if re.search(pattern, f):
    	    os.unlink(os.path.join(dir, f))


# TODO: Seems this function is not needed - Delete it
def remove_file(file):
    FileName = file
    driver = ogr.GetDriverByName("ESRI Shapefile")
    if os.path.exists(FileName):
        driver.DeleteDataSource(FileName)


# TODO: Seems this function is not needed - Delete it
def poly2line(input_poly,output_line):
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
    outLayer = outDataSource.CreateLayer(output_line, geom_type=ogr.wkbMultiLineString)
    featureDefn = outLayer.GetLayerDefn()
    outFeature = ogr.Feature(featureDefn)
    outFeature.SetGeometry(geomcol)
    outLayer.CreateFeature(outFeature)


def multipoly2poly(in_lyr, out_lyr):
    for in_feat in in_lyr:
        geom = in_feat.GetGeometryRef()
        if geom.GetGeometryName() == 'MULTIPOLYGON':
            for geom_part in geom:
                add_polygon(geom_part.ExportToWkb(), out_lyr)
        else:
            add_polygon(geom.ExportToWkb(), out_lyr)


def add_polygon(simplePolygon, out_lyr):
    featureDefn = out_lyr.GetLayerDefn()
    polygon = ogr.CreateGeometryFromWkb(simplePolygon)
    out_feat = ogr.Feature(featureDefn)
    out_feat.SetGeometry(polygon)
    out_lyr.CreateFeature(out_feat)


# TODO: Seems this function is not needed - Delete it
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


# TODO: Seems this function is not needed - Delete it
def reproject(input,output,geom_type):
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
    inDataSet = driver.Open(input+'.shp')
    inLayer = inDataSet.GetLayer()

    # create the output layer
    outputShapefile = output+'.shp'
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
            outFeature.SetField(outLayerDefn.GetFieldDefn(i).GetNameRef(), inFeature.GetField(i))
        # add the feature to the shapefile
        outLayer.CreateFeature(outFeature)
        # destroy the features and get the next input feature
        outFeature.Destroy()
        inFeature.Destroy()
        inFeature = inLayer.GetNextFeature()

    # close the shapefiles
    inDataSet.Destroy()
    outDataSet.Destroy()


# TODO: Seems this function is not needed - Delete it
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


def get_watershed_attributes(outlet_point, point_watershed,
                             ad8_file, plen_file, tlen_file, gord_file, dir_subwatershed, out_dir):

    os.chdir(out_dir)
    ad8_file_with_path = os.path.join(dir_subwatershed, ad8_file)
    gord_file_with_path = os.path.join(dir_subwatershed, gord_file)
    plen_file_with_path = os.path.join(dir_subwatershed, plen_file)
    tlen_file_with_path = os.path.join(dir_subwatershed, tlen_file)

    basin_length = extract_value_from_raster(plen_file_with_path, outlet_point)
    stream_order = extract_value_from_raster(gord_file_with_path, outlet_point)
    total_stream_length = extract_value_from_raster(tlen_file_with_path, outlet_point)
    ad8 = extract_value_from_raster(ad8_file_with_path, outlet_point)
    # use Spehorid.R function for calculating dxc and dyc . choose median value for dyc and dxc which is approximations
    area = ad8*30*30/(1000*1000)
    drainage_density = total_stream_length/(area*1000)
    length_overland_flow = 1/(2*drainage_density)
    source = ogr.Open(point_watershed, 1)
    layer = source.GetLayer()
    new_field = ogr.FieldDefn('Area', ogr.OFTReal)
    layer.CreateField(new_field)
    new_field = ogr.FieldDefn('BasinLen', ogr.OFTReal)
    layer.CreateField(new_field)
    new_field = ogr.FieldDefn('Strord', ogr.OFTReal)
    layer.CreateField(new_field)
    new_field = ogr.FieldDefn('StrLen', ogr.OFTReal)
    layer.CreateField(new_field)
    new_field = ogr.FieldDefn('DrnDen', ogr.OFTReal)
    layer.CreateField(new_field)
    new_field = ogr.FieldDefn('AvgOLF', ogr.OFTReal)
    layer.CreateField(new_field)
    feature = layer.GetFeature(0)
    start_time = time.time()
    my_at_val = [0, area, float(basin_length)/1000.00, stream_order, float(total_stream_length/1000.0),
                 float(drainage_density), float(length_overland_flow)]
    for i in range(1, 7):
        feature.SetField(i, float(my_at_val[i]))

    layer.SetFeature(feature)
    print("writing  time %s seconds ---" % (time.time() - start_time))
    source = None
