import os
import re
import os.path
import time

import pandas as pd
import numpy as np
from shapely.geometry import Point
from fiona import collection
from osgeo import gdal, ogr
import osr
from shapely.geometry import mapping


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


def reproject_point(lat_lon, from_epsg, to_epsg):
    """
    Source: http://gis.stackexchange.com/a/78850
    """
    lat, lon = lat_lon

    lat = float(lat)
    lon = float(lon)

    point = ogr.Geometry(ogr.wkbPoint)
    point.AddPoint(lon, lat)

    inSpatialRef = osr.SpatialReference()
    inSpatialRef.ImportFromEPSG(from_epsg)

    outSpatialRef = osr.SpatialReference()
    outSpatialRef.ImportFromEPSG(to_epsg)

    coordTransform = osr.CoordinateTransformation(inSpatialRef, outSpatialRef)
    point.Transform(coordTransform)

    return float(point.GetY()), float(point.GetX())


def create_shape_from_point(lat_long_orig, lat_long_proj, file, projection):
    y, x = lat_long_proj
    point = Point(x,y)
    lat, lon = lat_long_orig
    schema = {'geometry': 'Point', 'properties': {'Lat': 'float', 'Lon': 'float', 'ID': 'int'}}
    with collection(file + ".shp", "w", "ESRI Shapefile", schema, projection) as output:
        output.write({
                'properties': {
                    'Lat': lat,
                    'Lon': lon,
                    'ID': 1,
                },
                'geometry': mapping(point)
            })


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
                    # recursive function call
                    upstream_watershed(x4)

                return up1
            else:
                up2.append(-1)
                return up2

    upstream_watershed_id = upstream_watershed(num)
    return upstream_watershed_id


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
        return pixel_val    # intval is a tuple, length=1 as we only asked for 1 pixel value


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

    # Point does not exist within raster bounds.
    if not pixel_data:
        return -1

    pixel_val = pixel_data[0, 0]    # use the 'short' format code (2 bytes) not int (4 bytes)
    return pixel_val    # intval is a tuple, length=1 as we only asked for 1 pixel value


def get_gauge_watershed_command(mph_dir, np, taudem_dir, grid_dir, grid_name, output_dir, outlet_point,
                                new_gage_watershed_name):
    commands = []
    #commands.append(os.path.join(mph_dir, "mpiexec"))
    commands.append("mpiexec")
    #commands.append("--allow-run-as-root")
    commands.append("-np")
    commands.append(str(np))
    #commands.append(os.path.join(taudem_dir, "gagewatershed"))
    commands.append("gagewatershed")
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


def generate_moveoutletstostream_command(mph_dir, np, taudem_dir, Subwatershed_dir, Grid_Name,Output_dir, Outlet_Point, Distance_thresh):
    commands = []
    #commands.append(os.path.join(mph_dir, "mpiexec"))  # These were needed to get it to work on a PC for testing.  May need to revert for linux
    commands.append("mpiexec")
    #commands.append("--allow-run-as-root")
    commands.append("-np")
    commands.append(str(np))
    commands.append("moveoutletstostreams")
    #commands.append(os.path.join(taudem_dir, "moveoutletstostrm"))
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


def purge(dir, pattern):
    for f in os.listdir(dir):
        if re.search(pattern, f):
            os.unlink(os.path.join(dir, f))


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

def get_watershed_attributes(outlet_point, point_watershed,
                             ad8_file, plen_file, tlen_file,ord_file, dir_subwatershed, out_dir):

    os.chdir(out_dir)
    ad8_file_with_path = os.path.join(dir_subwatershed, ad8_file)
    ord_file_with_path = os.path.join(dir_subwatershed, ord_file)
    plen_file_with_path = os.path.join(dir_subwatershed, plen_file)
    tlen_file_with_path = os.path.join(dir_subwatershed, tlen_file)

    ad8 = extract_value_from_raster(ad8_file_with_path, outlet_point)
    # use Spehorid.R function for calculating dxc and dyc . choose median value for dyc and dxc which is approximations
    area = -999.0  # use this to record no data for catchments that cross region boundaries where this data is not computed
    drainage_density = -999.0
    length_overland_flow = -999.0
    basin_length = -999.0
    stream_order = -999.0
    total_stream_length = -999.0

    if(ad8 > 0):  # ad8 is no data when there is edge contamination from crossing of region boundaries
        area = ad8*30*30/(1000*1000)  # square km
        basin_length = extract_value_from_raster(plen_file_with_path, outlet_point)/1000.00  # Convert to km
        stream_order = extract_value_from_raster(ord_file_with_path, outlet_point)
        total_stream_length = extract_value_from_raster(tlen_file_with_path, outlet_point)/1000.0  # convert to km
        drainage_density = total_stream_length / area   # km^-1
        length_overland_flow = 1 / (2 * drainage_density)

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
    my_at_val = [0, area, float(basin_length), stream_order, float(total_stream_length),
                 float(drainage_density), float(length_overland_flow)]
    for i in range(1, 7):
        feature.SetField(i, float(my_at_val[i]))

    layer.SetFeature(feature)
    print("writing  time %s seconds ---" % (time.time() - start_time))
    source = None
