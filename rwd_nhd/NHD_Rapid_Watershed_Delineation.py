import sys
import os
import time
import subprocess

import gdal
import fiona

from NHD_RWD_Utilities import generate_moveoutletstostream_command, create_shape_from_point, \
    extract_value_from_raster_point, extract_value_from_raster, get_gauge_watershed_command, get_watershed_attributes, \
    purge, reproject_point


def Point_Watershed_Function(
        longitude,
        latitude,
        snapping,
        maximum_snap_distance,
        pre_process_dir,
        gage_watershed_raster,
        gage_watershed_shapefile,
        np,
        taudem_dir,
        mpi_dir,
        output_dir):

    overall_start_time = time.time()
    start_time = overall_start_time

    dir_main = os.path.join(str(pre_process_dir), 'Main_Watershed')
    main_watershed = gage_watershed_shapefile

    output_dir=os.path.join(dir_main,output_dir)

    if not os.path.exists(output_dir):
        os.makedirs(output_dir)

    os.chdir(dir_main)
    infile_crs = []
    with fiona.open(main_watershed + '.shp') as source:
        projection = source.crs
        infile_crs.append(projection)
    os.chdir(output_dir)
    log=open("log.txt","w")
    log.write("Latitude: %s, Longitude %s\n" % (latitude,longitude) )

    albers_y, albers_x = reproject_point(
        (latitude, longitude),
        # WGS 84 Latlong
        from_epsg=4326,
        # NAD83 / Conus Albers
        to_epsg=5070)

    # Create shape later when distance to stream is available
    # create_shape_from_point((latitude, longitude), (albers_y, albers_x), "mypoint", infile_crs[0])

    gage_watershed_rasterfile = os.path.join(dir_main, gage_watershed_raster)

    # extract ID from gage watershed raster saves significant amount of time, that is polygon searching takes long
    # amount of time however extract raster value from raster does not takes
    fg = int(extract_value_from_raster_point(
        gage_watershed_rasterfile, albers_x, albers_y))
    ID = fg
    print(ID)
    internaldrain=False
    if ID is None or ID < 1:
        # This internal drain logic relies on the following data
        #  regions.tif file in Main_watershed folder that has an ID in it for the NHDPlus grid processing region
        #  RegionsID folders in Subwatershed_ALL that has the corresponding region flow direction file named region_IDp.tif
        #  The strategy is to use the regions.tif file to identify the region the point falls within, then delineate the watershed using the full tiff file for that region.
        #  There is no joining of upstream watersheds as this is applied only for points not handled by the preprocessed gage watersheds and these points do not have upstream watersheds
        regionsfile = os.path.join(dir_main, "regions.tif")
        ID = int(extract_value_from_raster_point(
            regionsfile, albers_x, albers_y))
        if ID is None or ID < 1:
            raise Exception('Point located outside the watershed.')
        internaldrain=True

    if(internaldrain):
        print("Using internally draining function.\nRegion " + str(ID))
        dir_name = 'Region'
        sub_file_name = "Region_"
        subwatershed_dir = os.path.join(str(pre_process_dir), 'Subwatershed_ALL', dir_name + str(ID))
        distance_stream = 0
    else:
        dir_name = 'Subwatershed'
        sub_file_name = "subwatershed_"
        subwatershed_dir = os.path.join(str(pre_process_dir), 'Subwatershed_ALL', dir_name + str(ID))
        dist_file = sub_file_name + str(ID) + "dist.tif"
        dist_filename = os.path.join(subwatershed_dir, dist_file)
        #shp_filename = os.path.join(output_dir, "mypoint.shp")
        distance_stream = float(extract_value_from_raster_point(dist_filename, albers_x, albers_y))

    create_shape_from_point((latitude, longitude), (albers_y, albers_x), "mypoint", infile_crs[0], distance_stream )

    grid_name = sub_file_name + str(ID)
    # add file name for attributes
    ad8_file = grid_name + "ad8.tif"
    ord_file = grid_name + "ord.tif"
    plen_file = grid_name + "plen.tif"
    tlen_file = grid_name + "tlen.tif"

    grid_dir = subwatershed_dir
    outlet_point = "mypoint"
    new_gage_watershed_name = "local_subwatershed"
    snaptostream = snapping


    log.write("Identify subwatershed %s seconds \n" % (time.time() - start_time))
    start_time = time.time()

    if(not internaldrain):
        if snaptostream == "1":
            if ID > 0 and (distance_stream < float(maximum_snap_distance)):
                distance_thresh=int(float(maximum_snap_distance)/30+10)  # This is an integer number of grid cells to move and assumes 30 m cells.  dist/30 is max number of cells and +10 adds a buffer to make sure we move to the stream regardless
            else:
                distance_thresh = 0
        else:
            distance_thresh = 0

        cmd = generate_moveoutletstostream_command(
            mpi_dir,
            np,
            taudem_dir,
            grid_dir,
            grid_name,
            output_dir,
            outlet_point,
            distance_thresh)
        #print(cmd)
        os.system(cmd)   # This was giving an input line is too long error in PC testing
        #subprocess.check_call(cmd)

    else:
        # just recreate the New_Outlet file at the original location
        create_shape_from_point((latitude, longitude), (albers_y, albers_x), "New_Outlet", infile_crs[0], distance_stream)
        # To speed up internally drainin watershed delineation subset a region 11 km on either side of the point, rather than the whole fdr grid
        #  gdal_translate -projwin ulx uly lrx lry inraster.tif outraster.tif
        #  From http://www.gdal.org/gdal_translate.html
        # "Note: in GDAL 2.1.0 and 2.1.1, using -projwin with coordinates not aligned with pixels will result in a sub-pixel shift. This has been corrected in later versions."
        #  If this subpixel shift is a concern then need to upgrade.
        infile= os.path.join(grid_dir,grid_name+"p.tif")
        outfile="localp.tif"
        ulx= str(albers_x - 11000.0)
        lrx=str(albers_x + 11000.0)
        uly=str(albers_y + 11000.0)
        lry=str(albers_y - 11000.0)
        cmd="gdal_translate -projwin " + ulx + " " +  uly + " " + lrx + " " +  lry + ' "' + infile + '" ' + outfile
        # subprocess.check_call(cmd)
        os.system(cmd)  


    os.chdir(output_dir)
    outlet_moved_file = os.path.join(output_dir, "New_Outlet.shp")

    cmd = get_gauge_watershed_command(
        mpi_dir,
        np,
        taudem_dir,
        grid_dir,
        grid_name,
        output_dir,
        outlet_moved_file,
        new_gage_watershed_name,
        internaldrain)
    print(cmd)
    #subprocess.check_call(cmd)
    os.system(cmd)

    cmd = 'gdal_polygonize.py -8 local_subwatershed.tif -b 1' \
          ' -f "ESRI Shapefile"' \
          ' local_subwatershed.shp local_subwatershed GRIDCODE'
    # The lines below are needed for testing on some PC's where paths conflict.
    # cmd= 'C:\Python27\python "C:\Program Files\GDAL\gdal_polygonize.py" -8 local_subwatershed.tif -b 1' \
    #       ' -f "ESRI Shapefile"' \
    #       ' local_subwatershed.shp local_subwatershed GRIDCODE'
    #print(cmd)
    os.system(cmd)

    cmd = 'ogr2ogr local_subwatershed_dissolve.shp local_subwatershed.shp' \
          ' -dialect sqlite' \
          ' -sql "SELECT GRIDCODE, ST_Union(geometry) as geometry' \
          ' FROM local_subwatershed GROUP BY GRIDCODE"' \
          ' -nln results -overwrite'
    #print(cmd)
    os.system(cmd)

    log.write("Extract subwatershed %s seconds \n" % (time.time() - start_time))
    start_time = time.time()

    new_gage_watershed_dissolve = new_gage_watershed_name + "_dissolve"
    myid = []
    subid = []
    src_ds = gdal.Open(gage_watershed_rasterfile)
    gt = src_ds.GetGeoTransform()
    rb = src_ds.GetRasterBand(1)
    if(internaldrain):
        num_lines=0
    else:
        num_lines = sum(1 for line in open('upwacoor.txt'))
        if num_lines > 1:
            with open("upwacoor.txt", "rt") as f:
                for line in f:
                    x = float(line.split(',')[0])
                    y = float(line.split(',')[1])
                    mx = x
                    my = y

                    # using this approach is the fastest than others such as using gdallocation info or extract raster
                    px = int((mx - gt[0]) / gt[1])  # x pixel
                    py = int((my - gt[3]) / gt[5])  # y pixel
                    pixel_data = rb.ReadAsArray(px, py, 1, 1)  # Assumes 16 bit int aka 'short'
                    pixel_val = pixel_data[0, 0]  # use the 'short' format code (2 bytes) not int (4 bytes)
                    myid.append(int(pixel_val))
            subid = list(set(myid))

    log.write("Identify upstream watersheds %s seconds \n" % (time.time() - start_time))
    start_time = time.time()

    # compli_watershed_IDs = []  # was subid's > 0  DGT 11/13/16 adds requirement that must be in upcatchids.txt
    # if ID > 0 and num_lines > 1:
    #     compli_watershed_IDs = [i for i in subid if i > 0]
    #     len_comp = len(subid)
    # else:
    #     len_comp = -1
    # DGT replaced the above with the below
    if(internaldrain):
        len_comp=0
    else:
        with open(os.path.join(grid_dir, "upcatchids.txt"), 'r') as f:
            lines = f.read().splitlines()
        upcatchids = [int(x) for x in lines]
        compli_watershed_IDs=[val for val in subid if val in upcatchids]
        len_comp=len(compli_watershed_IDs)

    if len_comp > 0:
        print ("Up stream edge was reached")
        sub_water_file = []
        lc_watershed = os.path.join(output_dir, new_gage_watershed_dissolve + '.shp')
        sub_water_file.append(lc_watershed)

        for i in compli_watershed_IDs:
            subwater_dir = os.path.join(str(pre_process_dir), 'Subwatershed_ALL', 'Subwatershed' + str(i))
            com_watershed = "Simple_watershed" + str(i)
            com_file=os.path.join(subwater_dir, com_watershed + '.shp')

            if os.path.isfile(com_file):
                sub_water_file.append(com_file)

        os.chdir(output_dir)
        for x in range(1, len(sub_water_file)):
            cmd = 'ogr2ogr -update -append' + " "+sub_water_file[0] + " " + sub_water_file[x]
            #print(cmd)
            os.system(cmd)

        cmd = 'ogr2ogr New_Point_Watershed.shp local_subwatershed_dissolve.shp' \
              ' -dialect sqlite' \
              ' -sql "SELECT GRIDCODE, ST_Union(geometry) as geometry' \
              ' FROM local_subwatershed_dissolve"'
        #print(cmd)
        os.system(cmd)
    else:
        print ("Up stream edge was Not reached")
        os.chdir(output_dir)

        cmd = 'ogr2ogr New_Point_Watershed.shp local_subwatershed_dissolve.shp' \
              ' -dialect sqlite ' \
              ' -sql "SELECT GRIDCODE, ST_Union(geometry) as geometry' \
              ' FROM local_subwatershed_dissolve GROUP BY GRIDCODE"'
        #print(cmd)
        os.system(cmd)
    log.write("Join upstream watersheds %s seconds \n" % (time.time() - start_time))
    start_time = time.time()
    get_watershed_attributes(
        'New_Outlet.shp',
        'New_Point_Watershed.shp',
        ad8_file,
        plen_file,
        tlen_file,
        ord_file,
        subwatershed_dir,
        output_dir)

    log.write("Calculate watershed attributes time %s seconds \n" % (time.time() - start_time))
    start_time = time.time()
    # cleanup the output directory
    pattern = "^local"
    path = output_dir
    purge(path, pattern)
    os.remove('upwacoor.txt')
    log.write("Clean up time %s seconds \n" % (time.time() - start_time))
    log.write("Overall time %s seconds \n" % (time.time() - overall_start_time))
    log.close()

if __name__ == '__main__':
    Point_Watershed_Function(*sys.argv[1:])
