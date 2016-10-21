import shutil
import os
import sys
import subprocess
import glob

import fiona
from fiona import collection
import shapefile
from shapely.ops import cascaded_union
from shapely.geometry import shape, mapping
import numpy as np

from NHD_RWD_Utilities import complementary_gagewatershed, create_buffer


def main(input_dir_name, watershed_id_file, p_file, src_file, dist_file, ad8_file, plen_file,
         tlen_file, gord_file):
    input_dir = os.path.join(input_dir_name, "Main_Watershed")
    infile = os.path.join(input_dir, "watershed_file")
    complimentary_subwatershed_file = os.path.join(input_dir_name, "Subwatershed", "Full_watershed")
    output_dir1 = os.path.join(input_dir_name, "Subwatershed")
    if not os.path.exists(input_dir):
        os.makedirs(input_dir)
    if not os.path.exists(output_dir1):
        os.makedirs(output_dir1)
    output_dir2 = os.path.join(input_dir_name, "Subwatershed_ALL")
    if not os.path.exists(output_dir2):
        os.makedirs(output_dir2)
    os.chdir(input_dir)
    buffer_distance = 900   # used 30 cells 30*30 for NHD data
    watershed_id_file_dir = os.path.join(input_dir, watershed_id_file)
    shutil.copy2(watershed_id_file_dir, output_dir1)
    with fiona.open(infile) as source:
        meta = source.meta
        dest = output_dir1
        for f in source:
            outfile = os.path.join(dest, "subwatershed_%s.shp" % int(f['properties']['GRIDCODE']))
            with fiona.open(outfile, 'w', **meta) as sink:
                sink.write(f)

    # create complimentary watershed ( if exists)  for each subwatershed
    with fiona.open(infile) as source:
        infile_crs = source.crs
        for f in source:
            ID_complimentary = np.asarray(complementary_gagewatershed(
                watershed_id_file, int(f['properties']['GRIDCODE'])))
            real_index_complimentary = ID_complimentary > 0
            real_ID_complimentary = ID_complimentary[real_index_complimentary]
            print(str(real_ID_complimentary))
            number_of_contribute_subwatershed = len(real_ID_complimentary)
            files = []
            if number_of_contribute_subwatershed == 0:
                # TODO: (Pabitra) Why source_dir to be set inside the loop?
                source_dir = output_dir1
                # TODO: (Pabitra) Why we need to change the directory?
                os.chdir(source_dir)
                inputfile = os.path.join(source_dir, "subwatershed_" + str(int(f['properties']['GRIDCODE'])) + ".shp")
                outputfile = 'Full_watershed' + str(int(f['properties']['GRIDCODE'])) + '.shp'
                with collection(inputfile, "r") as input:
                    schema = input.schema.copy()
                    with collection(outputfile, "w", "ESRI Shapefile", schema, infile_crs) as output:
                        shapes = []
                        for f in input:
                            shapes.append(shape(f['geometry']).buffer(1))
                        merged = cascaded_union(shapes)
                        output.write({
                            'properties': {
                                'GRIDCODE': '1'
                            },
                            'geometry': mapping(merged)
                        })

                print ("No Complimentary watershed Exists")

            else:
                for i in range(0, number_of_contribute_subwatershed):
                    # copying complimetary shapefile to new folder
                    # TODO: (Pabitra) Why source_dir to be set inside the loop?
                    source_dir = output_dir1
                    # TODO: (Pabitra) Why we need to change the directory?
                    os.chdir(source_dir)
                    file = os.path.join(source_dir, "subwatershed_" + str(int(real_ID_complimentary[i])) + ".shp")
                    files.append(file)

                outputfile_WD = complimentary_subwatershed_file + str(int(f['properties']['GRIDCODE'])) + 'WD'
                sub_water_file = os.path.join(source_dir, "subwatershed_" + str(int(f['properties']['GRIDCODE'])) +
                                              ".shp")
                files.append(sub_water_file)
                w = shapefile.Writer()
                for ff in files:
                    r = shapefile.Reader(ff)
                    w._shapes.extend(r.shapes())
                    w.records.extend(r.records())   # make DSI as integer value otherwise it will not work

                w.fields = list(r.fields)
                w.save(outputfile_WD)
                inputfile = 'Full_watershed' + str(int(f['properties']['GRIDCODE'])) + 'WD' + '.shp'
                outputfile = 'Full_watershed' + str(int(f['properties']['GRIDCODE'])) + '.shp'
                with collection(inputfile, "r") as input_file_obj:
                    schema = input_file_obj.schema.copy()
                    with collection(outputfile, "w", "ESRI Shapefile", schema, infile_crs) as output:
                        shapes = []
                        for f in input_file_obj:
                            shapes.append(shape(f['geometry']).buffer(1))
                        merged = cascaded_union(shapes)
                        output.write({
                            'properties': {
                                'GRIDCODE': '1'
                            },
                            'geometry': mapping(merged)
                        })

    # make directory for each of the subwatershed and then extract and keep subwatershed, complimentary
    # watershed shapefile
    with fiona.open(infile) as source:
        source_dir = output_dir1
        # TODO: (Pabitra) Why we need to change the directory?
        os.chdir(source_dir)
        for f in source:
            dest = os.path.join(output_dir2,  "Subwatershed" + str(int(f['properties']['GRIDCODE'])))
            os.mkdir(dest)
            sub = os.path.join(source_dir, "subwatershed_" + str(int(f['properties']['GRIDCODE'])) + ".*")
            com = os.path.join(source_dir, "Full_watershed" + str(int(f['properties']['GRIDCODE'])) + ".*")
            files_sub = glob.glob(sub)
            files_com = glob.glob(com)
            for fl in files_sub:
                if os.path.isfile(fl):
                    shutil.copy2(fl, dest)
            for fl in files_com:
                if os.path.isfile(fl):
                    shutil.copy2(fl, dest)

    # extract streamraster, flow direction, watershed grid for each of the subwateshed and store in the
    # subwatershed directory
    with fiona.open(infile) as source:
        for f in source:
            dir = os.path.join(output_dir2, "Subwatershed" + str(int(f['properties']['GRIDCODE'])))
            # TODO: (Pabitra) Why we need to change the directory?
            os.chdir(dir)
            # input file name
            inputfn = 'subwatershed_' + str(int(f['properties']['GRIDCODE'])) + '.shp'
            # input file buffer shapefile name
            output_buffer_fn = 'subwatershed_buffer' + str(int(f['properties']['GRIDCODE'])) + '.shp'

            # creating buffer shape file
            create_buffer(inputfn, output_buffer_fn, buffer_distance)

            main_dir = input_dir
            flow_file = p_file
            stream_file = src_file
            d8_distance_file = dist_file
            flowdir = os.path.join(main_dir, flow_file)
            flow_out_file = os.path.join(dir, 'subwatershed_' + str(int(f['properties']['GRIDCODE'])) + "p.tif")
            streamdir = os.path.join(main_dir, stream_file)
            stream_out_file = os.path.join(dir, 'subwatershed_' + str(int(f['properties']['GRIDCODE'])) + "src1.tif")
            distancedir = os.path.join(main_dir, d8_distance_file)
            distance_out_file = os.path.join(dir, 'subwatershed_' + str(int(f['properties']['GRIDCODE'])) + "dist.tif")

            # for getting watershed attributes
            ad8dir = os.path.join(main_dir, ad8_file)
            ad8_out_file = os.path.join(dir, 'subwatershed_' + str(int(f['properties']['GRIDCODE'])) + "ad8.tif")
            plendir = os.path.join(main_dir, plen_file)
            plen_out_file = os.path.join(dir, 'subwatershed_' + str(int(f['properties']['GRIDCODE'])) + "plen.tif")
            tlendir = os.path.join(main_dir, tlen_file)
            tlen_out_file = os.path.join(dir, 'subwatershed_' + str(int(f['properties']['GRIDCODE'])) + "tlen.tif")
            gorddir = os.path.join(main_dir, gord_file)
            gord_out_file = os.path.join(dir, 'subwatershed_' + str(int(f['properties']['GRIDCODE'])) + "gord.tif")

            input = fiona.open(output_buffer_fn, 'r')
            xmin = str(input.bounds[0])
            ymin = str(input.bounds[1])
            xmax = str(input.bounds[2])
            ymax = str(input.bounds[3])
            layer_name = os.path.splitext(output_buffer_fn)[0]

            command_flow = "gdalwarp -te " + xmin + " " + ymin + " " + xmax + " " + ymax + \
                           " -dstnodata -32768 -cutline " + output_buffer_fn + " -cl " + layer_name + " " + \
                           flowdir + " " + flow_out_file
            command_stream = "gdalwarp -te " + xmin + " " + ymin + " " + xmax + " " + ymax + \
                             " -dstnodata -32768 -cutline " + output_buffer_fn + " -cl " + layer_name + " " + \
                             streamdir + " " + stream_out_file
            command_distance = "gdalwarp -te " + xmin + " " + ymin + " " + xmax + " " + ymax + \
                               " -dstnodata -32768.00 -cutline " + output_buffer_fn + " -cl " + layer_name + " " + \
                               distancedir + " " + distance_out_file

            command_ad8 = "gdalwarp -te " + xmin + " " + ymin + " " + xmax + " " + ymax + \
                          " -dstnodata -32768 -cutline " + output_buffer_fn + " -cl " + layer_name + " " + \
                          ad8dir + " " + ad8_out_file
            command_plen = "gdalwarp -te " + xmin + " " + ymin + " " + xmax + " " + ymax + \
                           " -dstnodata -32768 -cutline " + output_buffer_fn + " -cl " + layer_name + " " + \
                           plendir + " " + plen_out_file
            command_tlen = "gdalwarp -te " + xmin + " " + ymin + " " + xmax + " " + ymax + \
                           " -dstnodata -32768 -cutline " + output_buffer_fn + " -cl " + layer_name + " " + \
                           tlendir + " " + tlen_out_file
            command_gord = "gdalwarp -te " + xmin + " " + ymin + " " + xmax + " " + ymax + \
                           " -dstnodata -32768 -cutline " + output_buffer_fn + " -cl " + layer_name + " " + \
                           gorddir + " " + gord_out_file

            subprocess.check_call(command_flow)
            subprocess.check_call(command_stream)
            subprocess.check_call(command_distance)

            subprocess.check_call(command_ad8)
            subprocess.check_call(command_plen)
            subprocess.check_call(command_tlen)
            subprocess.check_call(command_gord)

            input.close()

    # remove subwatershed directory which we don't need
    with fiona.open(infile) as source:
        dest_dir = output_dir1
        for f in source:
            shutil.rmtree(dest_dir, ignore_errors=True)

    with fiona.open(infile) as source:
        for f in source:
            dir = os.path.join(output_dir2, "Subwatershed" + str(int(f['properties']['GRIDCODE'])))
            # TODO: (Pabitra) Why we need to change the directory?
            os.chdir(dir)
            buffer_watershed = os.path.join(dir, "subwatershed_buffer" + str(int(f['properties']['GRIDCODE']))+".*")
            files_sub = glob.glob(buffer_watershed)

            for fl in files_sub:
                if os.path.isfile(fl):
                    os.remove(fl)

if __name__ == '__main__':
    main(*sys.argv[1:])



