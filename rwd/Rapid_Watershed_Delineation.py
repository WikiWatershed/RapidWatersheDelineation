__author__ = 'shams'


from RWSDelin_Utilities import *
import shapefile
import time
import sys
import os
start_time = time.time()




def Point_Watershed_Function(longitude,latitude,snapping,maximum_snap_distance,Pre_process_TauDEM_dir,Ocean_stream_file,gage_watershed_file,coast_watershed_file,elev_file,Max_elev_file,
                             Ad8_weigthed_file,Ad8_file,
                             plen_file,tlen_file,gord_file,np,TauDEM_dir, MPI_dir):

   X=float(longitude)
   Y=float(latitude)
   point1 = Point(X,Y)
   dir_main=str(Pre_process_TauDEM_dir)+'/Main_Watershed'
   elev_file_with_path=os.path.join(dir_main,elev_file)
   Max_elev_file_with_path=os.path.join(dir_main,Max_elev_file)
   Ad8_weigthed_file_with_path=os.path.join(dir_main,Ad8_weigthed_file)
   Ad8_file_with_path=os.path.join(dir_main,Ad8_file)
   gord_file_with_path=os.path.join(dir_main,gord_file)
   plen_file_with_path=os.path.join(dir_main,plen_file)
   tlen_file_with_path=os.path.join(dir_main,tlen_file)
   Main_watershed=gage_watershed_file
   Coast_watershed=coast_watershed_file
   Ocean_Stream=Ocean_stream_file
   Output_dir=str(Pre_process_TauDEM_dir)+'/Test1'
   if not os.path.exists(Output_dir):
       os.makedirs(Output_dir)

   os.chdir(dir_main)
   infile_crs=[]
   with fiona.open(Main_watershed+'.shp') as source:
      projection = source.crs
      infile_crs.append(projection)
   os.chdir(Output_dir)

   createShape_from_Point(X,Y,"mypoint",infile_crs[0])
   if os.path.isfile(os.path.join(dir_main,Ocean_Stream+'.shp')):
       ID_Ocean_Stream=point_in_Polygon(dir_main,Ocean_Stream,point1)
       if (ID_Ocean_Stream>0):
          sys.exit("POINT LOCATED IN SIDE THE OCEAN!")

   ID_C=[]
   fg=point_in_Polygon(dir_main,Main_watershed,point1)
   ID=fg
   print(ID)
   if (ID is None):
       ID=-1
   if(ID<0):
       if os.path.isfile(os.path.join(dir_main,Coast_watershed+'.shp')):
         cg=point_in_Polygon(dir_main,Coast_watershed,point1)
         ID_C.append(cg)
   else:
       ID_C.append(-1)
   #if (ID is None)&(ID_C[0] is None):
      #sys.exit("POINT LOCATED OUT SIDE THE WATERSHED!")
   if ((ID<0) & (ID_C[0]<0)):
      sys.exit("POINT LOCATED OUT SIDE THE WATERSHED!")

   if(ID>0):
      dir_name='Subwatershed'
      sub_file_name="subwatershed_"
      subwatershed_dir=str(Pre_process_TauDEM_dir)+'/Subwatershed_ALL/'+dir_name+str(int(ID))
      dist_file=sub_file_name+str(int(ID))+"dist.tif"
      network_file=sub_file_name+str(int(ID))+"network.shp"
      complimentary_Network_file="Complimentary_watershed"+str(int(ID))+"network.shp"
      #src_filename =os.path.join(dir1,"subwatershed_4dist.tif")
      src_filename =os.path.join(subwatershed_dir,dist_file)
      shp_filename = os.path.join(Output_dir,"mypoint.shp")
      distance_stream=extract_value_from_raster(src_filename,shp_filename)
      Grid_Name=sub_file_name+str(int(ID))
   if(ID_C[0]>0):
      dir_name='Subwatershed_coast'
      sub_file_name="subwatershed_coast_"
      subwatershed_dir=str(Pre_process_TauDEM_dir)+'/Subwatershed_ALL/'+dir_name+str(int(ID_C[0]))
      Grid_Name=sub_file_name+str(int(ID_C[0]))
      distance_stream=-1

   MPH_dir=MPI_dir
   TauDEM_dir=TauDEM_dir
   np=np
   Grid_dir=subwatershed_dir
   Outlet_Point="mypoint"
   Distance_thresh=float(str(maximum_snap_distance))
   New_Gage_watershed_Name="local_subwatershed"
   snaptostream=int(snapping)
   print(snaptostream) 
   if(snaptostream==1):
     if((ID>0&(distance_stream<Distance_thresh))|(ID_C[0]>0)):
        #os.system(MOVEOUTLETTOSTREAMS(MPH_dir,np,TauDEM_dir,Grid_dir,Grid_Name,Output_dir,Outlet_Point,Distance_thresh))
        cmd=MOVEOUTLETTOSTREAMS(MPH_dir,np,TauDEM_dir,Grid_dir,Grid_Name,Output_dir,Outlet_Point,Distance_thresh)
        print(cmd);
        os.system(cmd)
        os.chdir(Output_dir)
        define_projection('Outlets_moved','New_Outlet',infile_crs[0])
        outlet_moved_file=os.path.join(Output_dir,"New_Outlet.shp")
     else:
         define_projection('mypoint','New_Outlet',infile_crs[0])
         outlet_moved_file=os.path.join(Output_dir,"New_Outlet.shp")
   else:
     define_projection('mypoint','New_Outlet',infile_crs[0])
     outlet_moved_file=os.path.join(Output_dir,"New_Outlet.shp")

   os.system(GAUGE_WATERSHED(MPH_dir,np,TauDEM_dir,Grid_dir,Grid_Name,Output_dir,outlet_moved_file,New_Gage_watershed_Name))
   new_watershed_raster=os.path.join(Output_dir,New_Gage_watershed_Name+".tif")
   Raster_to_Polygon(new_watershed_raster,New_Gage_watershed_Name) ## polygonize watershedraster to shapefile
   New_Gage_watershed_Dissolve="local_subwatershed_dissolve"
   polygon_dissolve(New_Gage_watershed_Name,New_Gage_watershed_Dissolve,infile_crs[0])
    #new_watershed_shape=os.path.join(dir2,New_Gage_watershed_Name+".shp")
   #print("--- %s seconds ---" % (time.time() - start_time))
   #start_time = time.time()
   New_Gage_watershed_Dissolve=New_Gage_watershed_Name+ "_dissolve"
   if(ID>0):
    complimentary_res=Reach_Upstream_Edge(New_Gage_watershed_Dissolve,Main_watershed,ID,dir_main,Output_dir)
    compli_watershed_ID= [i for i in complimentary_res if i >0]
    len_comp=len(compli_watershed_ID)
   else:
     len_comp=-1
   if(len_comp>0):
      flag="Up stream edge was reached"
      print flag
      number_compli_watershed=len(compli_watershed_ID)
      merged_watershed=os.path.join(Output_dir,"point_watershed")
      sub_water_file=[]
      lc_watershed=os.path.join(Output_dir,New_Gage_watershed_Dissolve+'.shp')
      sub_water_file.append(lc_watershed)
      w = shapefile.Writer()
      for i in compli_watershed_ID:
          subwater_dir=str(Pre_process_TauDEM_dir)+'/Subwatershed_ALL/Subwatershed'+str(int(i))
          com_watershed="Full_watershed"+str(int(i))
          com_file=os.path.join(subwater_dir, com_watershed+'.shp')
          if os.path.isfile(com_file):
            sub_water_file.append(com_file)

      #input_watersheds=sub_water_file
      for f in sub_water_file:
          r = shapefile.Reader(f)
          w._shapes.extend(r.shapes())
          w.records.extend(r.records())
      w.fields = list(r.fields)
      w.save(merged_watershed)
      print("--- %s seconds ---" % (time.time() - start_time))
      #start_time = time.time()
      #polygon_dissolve('point_watershed','point_watershed1',projection)
      polygon_dissolve_byfield('point_watershed.shp','point_watershed1.shp')
      #print("--- %s seconds ---" % (time.time() - start_time))


   else:
      flag="Up stream edge was Not reached"
      print flag
      #lc_watershed=os.path.join(Output_dir,New_Gage_watershed_Dissolve+'.shp')
      #polygon_dissolve(New_Gage_watershed_Dissolve,'point_watershed1',projection)
      polygon_dissolve_byfield(New_Gage_watershed_Dissolve+'.shp','point_watershed1.shp')

   #print("--- %s seconds ---" % (time.time() - start_time))
  # start_time = time.time()
   Get_Watershed_Attributes('New_Outlet.shp','point_watershed1',projection,elev_file_with_path,Max_elev_file_with_path,
                             Ad8_weigthed_file_with_path,Ad8_file_with_path,
                             plen_file_with_path,tlen_file_with_path,gord_file_with_path)
   pattern = "^mypoint"
   path=Output_dir
   remove_file_directory(path,pattern)
   pattern = "^Outlets"
   path=Output_dir
   purge(path,pattern)
   
  
   remove_file('mypoint.shp')
   remove_file('Outlets.shp')
   remove_file('Outlets_moved.shp')
   remove_file('local_subwatershed.shp')
   remove_file('local_subwatershed_dissolve.shp')
   remove_file('point_watershed.shp')
   remove_file('point_watershed1.shp')
   os.remove('local_subwatershed.txt')
   pattern = "^point_watershed"
   path=Output_dir
   purge(path,pattern)
   pattern = "^local"
   path=Output_dir
   remove_file_directory(path,pattern)


   filelist = glob.glob("temp_*")
   for f in filelist:
        os.remove(f)



   print("--- %s seconds ---" % (time.time() - start_time))

if __name__ == '__main__':
    # Map command line arguments to function arguments.
    Point_Watershed_Function(*sys.argv[1:])















