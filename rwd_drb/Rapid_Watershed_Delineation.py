__author__ = 'shams'


from RWSDelin_Utilities import *
import shapefile
import time
import sys
import os
start_time = time.time()


def Point_Watershed_Function(
        longitude,
        latitude,
        snapping,
        maximum_snap_distance,
        Pre_process_TauDEM_dir,
        Ocean_stream_file,
        gage_watershed_file,
        gage_watershed_ID_file,
        coast_watershed_file,
        np,
        TauDEM_dir,
        MPI_dir,
        Output_dir):

    X = float(longitude)
    Y = float(latitude)
    point1 = Point(X, Y)
    dir_main = str(Pre_process_TauDEM_dir) + '/Main_Watershed'
    Main_watershed = gage_watershed_file
    Coast_watershed = coast_watershed_file
    Ocean_Stream = Ocean_stream_file
    if not os.path.exists(Output_dir):
        os.makedirs(Output_dir)

    os.chdir(dir_main)
    infile_crs = []
    with fiona.open(Main_watershed + '.shp') as source:
        projection = source.crs
        infile_crs.append(projection)
    os.chdir(Output_dir)

    createShape_from_Point(X, Y, "mypoint", infile_crs[0])
    if os.path.isfile(os.path.join(dir_main, Ocean_Stream + '.shp')):
        ID_Ocean_Stream = point_in_Polygon(dir_main, Ocean_Stream, point1)
        if (ID_Ocean_Stream > 0):
            raise Exception('Point located inside the ocean.')

    ID_C = []
    fg = point_in_Polygon(dir_main, Main_watershed, point1)
    ID = fg
    print(ID)
    if (ID is None):
        ID = -1
    if(ID < 0):
        if os.path.isfile(os.path.join(dir_main, Coast_watershed + '.shp')):
            cg = point_in_Polygon(dir_main, Coast_watershed, point1)
            ID_C.append(cg)
    else:
        ID_C.append(-1)
    # if (ID is None)&(ID_C[0] is None):
        #sys.exit("POINT LOCATED OUT SIDE THE WATERSHED!")
    if ((ID < 0) & (ID_C[0] < 0)):
        raise Exception('Point located outside the watershed.')

    if(ID > 0):
        dir_name = 'Subwatershed'
        sub_file_name = "subwatershed_"
        subwatershed_dir = str(Pre_process_TauDEM_dir) + \
            '/Subwatershed_ALL/' + dir_name + str(int(ID))
        dist_file = sub_file_name + str(int(ID)) + "dist.tif"
        src_filename = os.path.join(subwatershed_dir, dist_file)
        shp_filename = os.path.join(Output_dir, "mypoint.shp")
        distance_stream = extract_value_from_raster(src_filename, shp_filename)
        Grid_Name = sub_file_name + str(int(ID))
        ## add file name for attributes
        elev_file=sub_file_name+str(int(ID))+"dm.tif"
        max_elev_file=sub_file_name+str(int(ID))+"mxdm.tif"
        Ad8_weighted_file=sub_file_name+str(int(ID))+"ad8wg.tif"
        Ad8_file=sub_file_name+str(int(ID))+"ad8.tif"
        gord_file=sub_file_name+str(int(ID))+"gord.tif"
        plen_file=sub_file_name+str(int(ID))+"plen.tif"
        tlen_file=sub_file_name+str(int(ID))+"tlen.tif"

    if(ID_C[0] > 0):
        dir_name = 'Subwatershed_coast'
        sub_file_name = "subwatershed_coast_"
        subwatershed_dir = str(Pre_process_TauDEM_dir) + \
            '/Subwatershed_ALL/' + dir_name + str(int(ID_C[0]))
        Grid_Name = sub_file_name + str(int(ID_C[0]))
        distance_stream = -1
        ## add file for attributes
        elev_file=sub_file_name+str(int(ID_C[0]))+"dm.tif"
        max_elev_file=sub_file_name+str(int(ID_C[0]))+"mxdm.tif"
        Ad8_weighted_file=sub_file_name+str(int(ID_C[0]))+"ad8wg.tif"
        Ad8_file=sub_file_name+str(int(ID_C[0]))+"ad8.tif"
        gord_file=sub_file_name+str(int(ID_C[0]))+"gord.tif"
        plen_file=sub_file_name+str(int(ID_C[0]))+"plen.tif"
        tlen_file=sub_file_name+str(int(ID_C[0]))+"tlen.tif"

    MPH_dir = MPI_dir
    TauDEM_dir = TauDEM_dir
    np = np
    Grid_dir = subwatershed_dir
    Outlet_Point = "mypoint"
    Distance_thresh = float(str(maximum_snap_distance))
    New_Gage_watershed_Name = "local_subwatershed"
    snaptostream = int(snapping)
    print(snaptostream)
    if(snaptostream == 1):
        if((ID > 0 & (distance_stream < Distance_thresh)) | (ID_C[0] > 0)):
            # os.system(MOVEOUTLETTOSTREAMS(MPH_dir,np,TauDEM_dir,Grid_dir,Grid_Name,Output_dir,Outlet_Point,Distance_thresh))
            cmd = MOVEOUTLETTOSTREAMS(
                MPH_dir,
                np,
                TauDEM_dir,
                Grid_dir,
                Grid_Name,
                Output_dir,
                Outlet_Point,
                Distance_thresh)
            print(cmd)
            os.system(cmd)
            os.chdir(Output_dir)
            outlet_moved_file = os.path.join(Output_dir, "New_Outlet.shp")
        else:
            os.chdir(Output_dir)
            define_projection('mypoint', 'New_Outlet', infile_crs[0])
            outlet_moved_file = os.path.join(Output_dir, "New_Outlet.shp")
    else:
        os.chdir(Output_dir)
        define_projection('mypoint', 'New_Outlet', infile_crs[0])
        outlet_moved_file = os.path.join(Output_dir, "New_Outlet.shp")

    os.system(
        GAUGE_WATERSHED(
            MPH_dir,
            np,
            TauDEM_dir,
            Grid_dir,
            Grid_Name,
            Output_dir,
            outlet_moved_file,
            New_Gage_watershed_Name))
    # raster to ploygon using ogr2ogr command line
    os.chdir(Output_dir)
    raster_polygon='gdal_polygonize.py local_subwatershed.tif -b 1 -f "ESRI Shapefile" local_subwatershed.shp local_subwatershed GRIDCODE'
    os.system(raster_polygon)
    # dissolve polygon using ogr2ogr
    poly_dissolv='ogr2ogr local_subwatershed_dissolve.shp local_subwatershed.shp -dialect sqlite -sql'+ " "+ ' "SELECT GRIDCODE, ST_Union(geometry) as geometry FROM '+" "+" 'local_subwatershed' " + " " +' GROUP BY GRIDCODE" '+ '  -nln results -overwrite'
    print(poly_dissolv)
    os.system(poly_dissolv)
    New_Gage_watershed_Dissolve=New_Gage_watershed_Name+ "_dissolve"
    if(ID > 0):
        up_ID=upstream_gagewatershed(gage_watershed_ID_file,ID,dir_main)
        complimentary_res = Reach_Upstream_Edge(
            New_Gage_watershed_Dissolve,up_ID,Pre_process_TauDEM_dir,dir_name,ID,Output_dir)
        compli_watershed_ID = [i for i in complimentary_res if i > 0]
        len_comp = len(compli_watershed_ID)
    else:
        len_comp = -1
    if(len_comp > 0):
        flag = "Up stream edge was reached"
        print flag
        number_compli_watershed = len(compli_watershed_ID)
        merged_watershed = os.path.join(Output_dir, "point_watershed")
        sub_water_file = []
        lc_watershed = os.path.join(
            Output_dir, New_Gage_watershed_Dissolve + '.shp')
        sub_water_file.append(lc_watershed)
        for i in compli_watershed_ID:
            subwater_dir = str(Pre_process_TauDEM_dir) + \
                '/Subwatershed_ALL/Subwatershed' + str(int(i))
            com_watershed = "Full_watershed" + str(int(i))
            com_file = os.path.join(subwater_dir, com_watershed + '.shp')
            if os.path.isfile(com_file):
                sub_water_file.append(com_file)

        os.chdir(Output_dir)
        for x in range(1, len(sub_water_file)):
          merge_watrshed='ogr2ogr -update -append'+ " "+sub_water_file[0]+ " " + sub_water_file[x]
          os.system(merge_watrshed)
        ## dissolve watersheds using ogr2ogr command line
        dissolve_cmd='ogr2ogr New_Point_Watershed.shp local_subwatershed_dissolve.shp -dialect sqlite -sql'+ " "+ ' "SELECT GRIDCODE ,ST_Union(geometry) as geometry FROM '+" "+" 'local_subwatershed_dissolve' " + " " +' GROUP BY GRIDCODE" '
        print(dissolve_cmd)  
        os.system(dissolve_cmd)

    else:
        flag = "Up stream edge was Not reached"
        print flag
        # lc_watershed=os.path.join(Output_dir,New_Gage_watershed_Dissolve+'.shp')
        # polygon_dissolve(New_Gage_watershed_Dissolve,'point_watershed1',projection)
        os.chdir(Output_dir)
        dissolve_cmd='ogr2ogr New_Point_Watershed.shp local_subwatershed_dissolve.shp -dialect sqlite -sql'+ " "+ ' "SELECT GRIDCODE ,ST_Union(geometry) as geometry FROM '+" "+" 'local_subwatershed_dissolve' " + " " +' GROUP BY GRIDCODE" '
        print(dissolve_cmd)
        os.system(dissolve_cmd)


    Get_Watershed_Attributes(
        'New_Outlet.shp',
        'New_Point_Watershed',
        elev_file,
        max_elev_file,
        Ad8_weighted_file,
        Ad8_file,
        plen_file,
        tlen_file,
        gord_file,
        subwatershed_dir,
        Output_dir)
    pattern = "^mypoint"
    path = Output_dir
    remove_file_directory(path, pattern)
    pattern = "^Outlets"
    path = Output_dir
    purge(path, pattern)

    remove_file('mypoint.shp')
    remove_file('Outlets.shp')
    remove_file('Outlets_moved.shp')
    remove_file('local_subwatershed.shp')
    remove_file('local_subwatershed_dissolve.shp')
    remove_file('point_watershed.shp')
    remove_file('point_watershed1.shp')
    os.remove('local_subwatershed.txt')
    pattern = "^point_watershed"
    path = Output_dir
    purge(path, pattern)
    pattern = "^local"
    path = Output_dir
    remove_file_directory(path, pattern)

    filelist = glob.glob("temp_*")
    for f in filelist:
        os.remove(f)

    print("--- %s seconds ---" % (time.time() - start_time))

if __name__ == '__main__':
        # Map command line arguments to function arguments.
    Point_Watershed_Function(*sys.argv[1:])
