import os
import re
import os.path
import time
import itertools

import pandas as pd
import numpy as np
from shapely.geometry import Point
from fiona import collection
from osgeo import gdal, ogr
import osr

from shapely.geometry import (mapping,
                              shape,
                              Polygon,
                              MultiPolygon,)
from shapely.ops import cascaded_union


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


def create_shape_from_point(lat_long_orig, lat_long_proj, file, projection, distance_stream):
    y, x = lat_long_proj
    point = Point(x,y)
    lat, lon = lat_long_orig
    # Per http://toblerity.org/fiona/manual.html#writing-new-files the property items are given as a list to retain the order
    schema = {'geometry': 'Point', 'properties': [('ID', 'int'), ('Lat', 'float'), ('Lon', 'float'), ('DistStr_m', 'float')]}
    with collection(file + ".shp", "w", "ESRI Shapefile", schema, projection) as output:
        output.write({
                'properties': {
                    'ID': 1,
                    'Lat': lat,
                    'Lon': lon,
                    'DistStr_m': float(distance_stream)
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


def extract_value_from_raster_point(rasterfile, x, y,log):
    try:
        src_ds = gdal.Open(rasterfile)
        gt = src_ds.GetGeoTransform()
        rb = src_ds.GetRasterBand(1)

        mx = float(x)
        my = float(y)

        px = int((mx - gt[0]) / gt[1])  # x pixel
        py = int((my - gt[3]) / gt[5])  # y pixel
        pixel_data = rb.ReadAsArray(px, py, 1, 1)

        # Point does not exist within raster bounds.
        if pixel_data is None :
            return -1

        pixel_val = pixel_data[0, 0]
        src_ds = None # Close the dataset
    except:
        log.write("Exception in extract value from raster\n")
        log.write("Rasterfile: " + rasterfile + "\n")
        log.write("x: %s y: %s\n" % (x,y))
        log.write("mx: %d my: %d\n" % (mx, my))
        log.write("px: %d py: %d\n" % (px, py))
        log.write("pixel_val: %d\n" % pixel_val)

    return pixel_val


def get_gauge_watershed_command(mph_dir, np, taudem_dir, grid_dir, grid_name, output_dir, outlet_point,
                                new_gage_watershed_name,internaldrain):
    commands = []
    commands.append(os.path.join(mph_dir, "mpiexec"))
    #commands.append("mpiexec")  # For PC Testing
    commands.append("--allow-run-as-root")
    commands.append("-np")
    commands.append(str(np))
    commands.append(os.path.join(taudem_dir, "gagewatershed"))
    #commands.append("gagewatershed")  # For PC testing
    commands.append("-p")
    if(internaldrain):
	# May need different path setup when not on PC
        commands.append("localp.tif")  # Use the local fdr file
    else:
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
    commands.append(os.path.join(mph_dir, "mpiexec"))  # For linux
    # commands.append("mpiexec")  # For PC Testing
    commands.append("--allow-run-as-root")
    commands.append("-np")
    commands.append(str(np))
    # commands.append("moveoutletstostreams")  # For PC Testing
    commands.append(os.path.join(taudem_dir, "moveoutletstostrm"))  # For linux
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

    # ad8_file_with_path = os.path.join(dir_subwatershed, ad8_file)
    # ord_file_with_path = os.path.join(dir_subwatershed, ord_file)
    # plen_file_with_path = os.path.join(dir_subwatershed, plen_file)
    # tlen_file_with_path = os.path.join(dir_subwatershed, tlen_file)

    # ad8 = extract_value_from_raster(ad8_file_with_path, outlet_point)
    # use Spehorid.R function for calculating dxc and dyc . choose median value for dyc and dxc which is approximations
    # area = -999.0  # use this to record no data for catchments that cross region boundaries where this data is not computed
    # drainage_density = -999.0
    # length_overland_flow = -999.0
    # basin_length = -999.0
    # stream_order = -999.0
    # total_stream_length = -999.0

   # if(ad8 > 0):  # ad8 is no data when there is edge contamination from crossing of region boundaries
       # area = ad8*30*30/(1000*1000)  # square km
        #basin_length = extract_value_from_raster(plen_file_with_path, outlet_point)/1000.00  # Convert to km
        #stream_order = extract_value_from_raster(ord_file_with_path, outlet_point)
        #if(stream_order < 0):  # This occurs when the point is not on a stream due to either not snapping to stream or being in an internally draining region where there is not a stream downslope to snap to
        #     stream_order=0   # Note that here stream order and stream length receive 0 values that differ from the above no data (-999) initializations that persist when ad8 is unknown due to not computing across region boundaries
        #     total_stream_length=0
        #     drainage_density = -999.0  # Drainage density and overland flow length are still reported as no data as they can not be evaluated without a stream
        #     length_overland_flow = -999.0
        # else:
        #     total_stream_length = extract_value_from_raster(tlen_file_with_path, outlet_point)/1000.0  # convert to km
        #     drainage_density = total_stream_length / area   # km^-1
        #     length_overland_flow = 1 / (2 * drainage_density)

    source = ogr.Open(point_watershed, 1)
    layer = source.GetLayer()
    new_field = ogr.FieldDefn('Area_km2', ogr.OFTReal)  # Changed field names to indicate units
    layer.CreateField(new_field)
    #new_field = ogr.FieldDefn('BasinL_km', ogr.OFTReal)
    #layer.CreateField(new_field)
    #new_field = ogr.FieldDefn('Strord', ogr.OFTReal)
    #layer.CreateField(new_field)
    #new_field = ogr.FieldDefn('StrLen_km', ogr.OFTReal)
    #layer.CreateField(new_field)
    #new_field = ogr.FieldDefn('DrnDen_kmi', ogr.OFTReal)  # kmi is the best I could do for inverse km given only 10 char.
    #layer.CreateField(new_field)
    #new_field = ogr.FieldDefn('AvgOLF_km', ogr.OFTReal)
    #layer.CreateField(new_field)
    feature = layer.GetFeature(0)
    start_time = time.time()
    geom = feature.GetGeometryRef()
    area = geom.GetArea()/1000000  # convert to km2
    my_at_val = [0, area]
    # my_at_val = [0, area, float(basin_length), stream_order, float(total_stream_length),
    #              float(drainage_density), float(length_overland_flow)]
    for i in range(1, len(my_at_val)):
        feature.SetField(i, float(my_at_val[i]))

    layer.SetFeature(feature)
    print("Area time %s seconds ---" % (time.time() - start_time))
    source = None

def dissolve(input_filename, output_filename, groupby_gridcode=True):
    with collection(input_filename, 'r') as input:
        driver = input.driver
        crs = input.crs
        schema = input.schema.copy()
        with collection(output_filename,
                        'w',
                        driver=driver,
                        crs=crs,
                        schema=schema) as output:
            def exterior_ring(polygon):
                return Polygon(polygon.exterior)

            def dissolve_features(features, gridcode=None):
                shapes = [shape(f['geometry']) for f in features]
                merged_shape = cascaded_union(shapes)
                holefree_shape = MultiPolygon([exterior_ring(poly) for poly in merged_shape.geoms]) \
                                 if merged_shape.geom_type is 'MultiPolygon' \
                                 else exterior_ring(merged_shape)

                output.write({
                    'GRIDCODE': gridcode,
                    'properties': { 'GRIDCODE': gridcode },
                    'geometry': mapping(holefree_shape)
                })

            if groupby_gridcode:
                sorted_features = sorted(input, key=lambda x: x['properties']['GRIDCODE'])
                for gridcode, gridcode_features in itertools.groupby(sorted_features, key=lambda x: x['properties']['GRIDCODE']):
                    dissolve_features(gridcode_features, gridcode=gridcode)
            else:
                dissolve_features(input)
