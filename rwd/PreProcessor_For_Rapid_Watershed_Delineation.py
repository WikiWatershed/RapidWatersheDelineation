__author__ = 'shams'

import shutil
import os
import sys
from RWSDelin_Utilities import *
import shapefile
def PreProcess_TauDEM_for_On_Fly_WatershedDelineation(input_dir_name,watershed_file,watershed_id_file,watershed_coast,p_file,gw_file,src_file,src_file_coast,dist_file):
    input_dir1=input_dir_name+"/Main_Watershed"
    infile = input_dir1+"/"+watershed_file
    coast_file=input_dir1+"/"+watershed_coast
    complimentary_subwatershed_file=input_dir_name+"/Subwatershed/Full_watershed"
    output_dir1=input_dir_name+"/Subwatershed"
    if not os.path.exists(input_dir1):
       os.makedirs(input_dir1)
    if not os.path.exists(output_dir1):
       os.makedirs(output_dir1)
    output_dir2=input_dir_name+"/Subwatershed_ALL"
    if not os.path.exists(output_dir2):
       os.makedirs(output_dir2)
    os.chdir(input_dir1)
    dataset=gdal.Open(gw_file)
    geotransform=dataset.GetGeoTransform()
    pixel_depth=geotransform[1]
    Buffer_distance=3*pixel_depth
    watershed_id_file_dir=os.path.join(input_dir1,watershed_id_file)
    shutil.copy2(watershed_id_file_dir,output_dir1)
    with fiona.open(infile) as source:
        meta = source.meta
        for f in source:
            dest = output_dir1
            outfile = os.path.join(dest, "subwatershed_%s.shp" % f['properties']['GRIDCODE'])
            with fiona.open(outfile, 'w', **meta) as sink:
                sink.write(f)

    ##for coastal watershed
    if os.path.isfile(coast_file):
      with fiona.open(coast_file) as source:
        meta = source.meta
        for f in source:
            dest = output_dir1
            outfile = os.path.join(dest, "subwatershed_coast_%s.shp" % f['properties']['GRIDCODE'])
            with fiona.open(outfile, 'w', **meta) as sink:
                sink.write(f)




#
# # create complimentary watershed ( if exists)  for each subwatershed
    with fiona.open(infile) as source:

      infile_crs = source.crs
      for f in source:
        ID_complimentary=np.asarray(complementary_gagewatershed(watershed_id_file,int(f['properties']['GRIDCODE'])))
        Real_Index_Complimentary=ID_complimentary>0
        Real_ID_Complimentary=ID_complimentary[Real_Index_Complimentary]
        Number_contribute_subwatershed=len(Real_ID_Complimentary)
        files=[]
        if(Number_contribute_subwatershed==0):
            source_dir=output_dir1
            os.chdir(source_dir)
            inputfile=os.path.join(source_dir,"subwatershed_"+str(f['properties']['GRIDCODE'])+".shp")
            outputfile='Full_watershed'+str(f['properties']['GRIDCODE'])+'.shp'
            with collection(inputfile, "r") as input:
                schema = input.schema.copy()
                with collection(
                        outputfile, "w", "ESRI Shapefile",schema, infile_crs) as output:
                    shapes = []
                    for f in input:
                        shapes.append( shape(f['geometry']).buffer(.000000001))
                    merged = cascaded_union(shapes)
                    output.write({
                        'properties': {
                            'GRIDCODE': '1'
                        },
                        'geometry': mapping(merged)
                    })


            print "No Complimentary watershed Exists"

        else :
            for i in range(0,Number_contribute_subwatershed):
                source_dir=output_dir1 ### copying complimetary shapefile to new folder """
                os.chdir(source_dir)
                file = os.path.join(source_dir,"subwatershed_"+str(int(Real_ID_Complimentary[i]))+".shp")
                files.append(file)
            outputfile_WD=complimentary_subwatershed_file+str(f['properties']['GRIDCODE'])+'WD'
            sub_water_file= os.path.join(source_dir,"subwatershed_"+str(f['properties']['GRIDCODE'])+".shp")
            files.append(sub_water_file)
            w = shapefile.Writer()
            for ff in files:
                r = shapefile.Reader(ff)
                w._shapes.extend(r.shapes())
                w.records.extend(r.records()) ## make DSI as integer value other wise it will not work
            w.fields = list(r.fields)
            w.save(outputfile_WD)
            inputfile='Full_watershed'+str(f['properties']['GRIDCODE'])+'WD'+'.shp'
            outputfile='Full_watershed'+str(f['properties']['GRIDCODE'])+'.shp'
            with collection(inputfile, "r") as input:
                schema = input.schema.copy()
                with collection(
                        outputfile, "w", "ESRI Shapefile",schema, infile_crs) as output:
                    shapes = []
                    for f in input:
                        shapes.append( shape(f['geometry']).buffer(.000000001))
                    merged = cascaded_union(shapes)
                    output.write({
                        'properties': {
                            'GRIDCODE': '1'
                        },
                        'geometry': mapping(merged)
                    })




#
# # make directory for each of the subwatershed and then extract and keep subwatershed, complimentary watershed shapefile
    with fiona.open(infile) as source:
      source_dir=output_dir1
      os.chdir(source_dir)
      for f in source:
        dest = output_dir2+"/Subwatershed"+str(f['properties']['GRIDCODE'])
        os.mkdir(dest)
        sub=os.path.join(source_dir,"subwatershed_"+str(f['properties']['GRIDCODE'])+".*")
        com=os.path.join(source_dir,"Full_watershed"+str(f['properties']['GRIDCODE'])+".*")
        files_sub=glob.glob(sub)
        files_com=glob.glob(com)
        for file1 in files_sub:
            if os.path.isfile(file1):
                shutil.copy2(file1, dest)
        for file2 in files_com:
            if os.path.isfile(file2):
                shutil.copy2(file2, dest)

    if os.path.isfile(coast_file):
      with fiona.open(coast_file) as source:
       source_dir=output_dir1
       os.chdir(source_dir)
       for f in source:
        dest = output_dir2+"/Subwatershed_coast"+str(f['properties']['GRIDCODE'])
        os.mkdir(dest)
        sub=os.path.join(source_dir,"subwatershed_coast_"+str(f['properties']['GRIDCODE'])+".*")
        files_sub=glob.glob(sub)
        for file1 in files_sub:
            if os.path.isfile(file1):
                shutil.copy2(file1, dest)


#
# # extract streamraster,flow direction, watershed grid for each of the subwateshed and store in the subwatershed directory
    with fiona.open(infile) as source:
       for f in source:
            dir=output_dir2+"/Subwatershed"+str(f['properties']['GRIDCODE'])
            os.chdir(dir)
            inputfn = 'subwatershed_'+str(f['properties']['GRIDCODE'])+'.shp'                ##input file name
            complimentary_subwatershed_file='Full_watershed'+str(f['properties']['GRIDCODE'])+'.shp'
            outputBufferfn ='subwatershed_buffer'+str(f['properties']['GRIDCODE'])+'.shp'      ##input file buffer shapefile name
            bufferDist = Buffer_distance                                     ##buffer distance
            createBuffer(inputfn, outputBufferfn, bufferDist)       ## creating buffer shape file
            print('buffer created')
            main_dir=input_dir1; flow_file=p_file;subwshed_file=gw_file;stream_file=src_file;D8distance_file=dist_file
            flowdir=os.path.join(main_dir,flow_file);flow_out_file=os.path.join(dir,'subwatershed_'+str(f['properties']['GRIDCODE'])+"p.tif")
            subwaterdir=os.path.join(main_dir,subwshed_file);subwater_out_file=os.path.join(dir,'subwatershed_'+str(f['properties']['GRIDCODE'])+"w.tif")
            streamdir=os.path.join(main_dir,stream_file);stream_out_file=os.path.join(dir,'subwatershed_'+str(f['properties']['GRIDCODE'])+"src1.tif")
            distancedir=os.path.join(main_dir,D8distance_file);distance_out_file=os.path.join(dir,'subwatershed_'+str(f['properties']['GRIDCODE'])+"dist.tif")


            input = fiona.open(outputBufferfn, 'r')
            xmin=str(input.bounds[0])
            ymin=str(input.bounds[1])
            xmax=str(input.bounds[2])
            ymax=str(input.bounds[3])
            layer_name=os.path.splitext(outputBufferfn)[0]

            command_flow="gdalwarp -te " + xmin + " " + ymin + " " + xmax + " " + ymax + " -dstnodata -32768 -cutline " + outputBufferfn + " -cl "+ layer_name + " " + flowdir + " " + flow_out_file
            command_subw="gdalwarp -te " + xmin + " " + ymin + " " + xmax + " " + ymax + " -dstnodata -32768 -cutline " + outputBufferfn + " -cl "+ layer_name + " " +  subwaterdir + " " + subwater_out_file
            command_stream="gdalwarp -te " + xmin + " " + ymin + " " + xmax + " " + ymax + " -dstnodata -32768 -cutline " + outputBufferfn + " -cl "+ layer_name + " " + streamdir + " " + stream_out_file
            command_distance="gdalwarp -te " + xmin + " " + ymin + " " + xmax + " " + ymax + " -dstnodata -32768.00 -cutline " + outputBufferfn + " -cl "+ layer_name + " " + distancedir + " " + distance_out_file


            os.system(command_flow)
            os.system(command_subw)
            os.system(command_stream)
            os.system(command_distance)
            input.close()



    if os.path.isfile(coast_file):
      with fiona.open(coast_file) as source:
       for f in source:
            dir=output_dir2+"/Subwatershed_coast"+str(f['properties']['GRIDCODE'])
            os.chdir(dir)
            inputfn = 'subwatershed_coast_'+str(f['properties']['GRIDCODE'])+'.shp'
            outputBufferfn ='subwatershed_coast_buffer'+str(f['properties']['GRIDCODE'])+'.shp'      ##input file buffer shapefile name
            bufferDist = Buffer_distance                                     ##buffer distance
            createBuffer(inputfn, outputBufferfn, bufferDist)       ## creating buffer shape file

            main_dir=input_dir1; flow_file=p_file;stream_file=src_file_coast
            flowdir=os.path.join(main_dir,flow_file);flow_out_file=os.path.join(dir,'subwatershed_coast_'+str(f['properties']['GRIDCODE'])+"p.tif")
            streamdir=os.path.join(main_dir,stream_file);stream_out_file=os.path.join(dir,'subwatershed_coast_'+str(f['properties']['GRIDCODE'])+"src1.tif")
            input = fiona.open(outputBufferfn, 'r')
            xmin=str(input.bounds[0])
            ymin=str(input.bounds[1])
            xmax=str(input.bounds[2])
            ymax=str(input.bounds[3])
            layer_name=os.path.splitext(outputBufferfn)[0]
            command_flow="gdalwarp -te " + xmin + " " + ymin + " " + xmax + " " + ymax + " -dstnodata -32768 -cutline " +  outputBufferfn + " -cl "+ layer_name + " " + flowdir + " " + flow_out_file
            command_stream="gdalwarp -te " + xmin + " " + ymin + " " + xmax + " " + ymax + " -dstnodata -32768 -cutline " +  outputBufferfn + " -cl "+ layer_name + " " + streamdir + " " + stream_out_file

            os.system(command_flow)
            os.system(command_stream)

            input.close()
# #
# # #Remove subwatershed directory which we dont need
    with fiona.open(infile) as source:
      for f in source:
        dest_dir=output_dir1
        shutil.rmtree(dest_dir,ignore_errors=True)

    with fiona.open(infile) as source:
       for f in source:
        dir=output_dir2+"/Subwatershed"+str(f['properties']['GRIDCODE'])
        os.chdir(dir)
        buffer_watershed=os.path.join(dir,"subwatershed_buffer"+str(f['properties']['GRIDCODE'])+".*")

        files_sub=glob.glob(buffer_watershed)

        for file1 in files_sub:
            if os.path.isfile(file1):

                os.remove(file1)



    if os.path.isfile(coast_file):
      with fiona.open(coast_file) as source:
       for f in source:
        dir=output_dir2+"/Subwatershed"+str(f['properties']['GRIDCODE'])
        os.chdir(dir)
        buffer_watershed=os.path.join(dir,"subwatershed_coast_buffer"+str(f['properties']['GRIDCODE'])+".*")

        files_sub=glob.glob(buffer_watershed)

        for file1 in files_sub:
            if os.path.isfile(file1):

                os.remove(file1)

if __name__ == '__main__':
    # Map command line arguments to function arguments.
    PreProcess_TauDEM_for_On_Fly_WatershedDelineation(*sys.argv[1:])
