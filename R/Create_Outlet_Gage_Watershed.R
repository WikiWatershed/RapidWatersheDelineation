url='http://cran.us.r-project.org'
install.packages('sp',repos = url)
library(sp)

install.packages('dismo',repos = url)
library(dismo)

install.packages('raster',repos = url
library(raster)

install.packages('rgeos',repos = url)
library(rgeos)

install.packages('maptools',repos = url)
library(maptools)

install.packages('proj4',repos = url)
library(proj4)

install.packages('rgdal',repos = url)
library(rgdal)

install.packages('shapefiles',repos = url)
library(shapefiles)

install.packages('spsurvey',repos = url)
require(spsurvey)


#see details description in this link:
#setwd("F:\\USU_Research_work_update_March_30_2014\\MMW_PROJECT\\OnFlyWatershed_GEO_Delaware\\Pre_Process_Product")

# Inputs
inshapefile="AllCatchOutlets.shp"
dist=2500
Outshapefile = 'CatchOutlets'
Outshapefolder = 'OutFolder'
## End inputs

xx <- data.frame(readShapePoints(inshapefile))

downstream_point_all=xx[which((xx[,2]==-1) & (!xx[,3]==-1)  & (!xx[,4]==-1 )),]
downstream_point=xx[which((xx[,2]==-1)),]

xx1=NA;
xx2=NA
xx3=NA
xx4=NA
get_upstream= function(LINKNO){
  
  if (length(LINKNO)<1) {
    return(LINKNO)
  }


  ID=which(xx[,1]==LINKNO)
  USLINK1=xx[ID,3]
  USLINK2=xx[ID,4]
  xx1=append(xx1,USLINK1)
  xx2=append(xx2,USLINK2)
  a1=get_upstream(USLINK1)
  b1=get_upstream(USLINK2)
  
  return(c(a1,b1,xx1,xx2))
}
  

get_downstream= function(LINKNO){
  
  if (length(LINKNO)<1) {
    return(LINKNO)
  }
  
  
  ID=which(xx[,1]==LINKNO)
  USLINK1=xx[ID,2]
 
  xx3=append(xx3,USLINK1)
  a11=get_downstream(USLINK1)

  
  return(c(a11,xx3))
}


ALL_outlets=NA
len=dim(downstream_point)[1]


for ( j in 1:len) {

print (j)

df=get_upstream(downstream_point_all[j,1]) 
#df=get_upstream(downstream_point_all[316,1]) 

df=df[!is.na(df)]
df=df[df>0]
ID2=match(df,xx[,1])
ID2=ID2[!is.na(ID2)]

ddd=xx[ID2,]

##initial screening with greater than 500 m
Int_screen=which(ddd[,15]>dist)
dd_mat=ddd[Int_screen,]
sort_dist=sort(dd_mat[,15],index.return=TRUE)
dd_mat_sort=dd_mat[sort_dist$ix,]

outlets=dd_mat_sort[1:2,1]
for ( i in 3:dim(dd_mat_sort)[1]) {

down_stream=get_downstream(dd_mat_sort[i,1])
down_stream=down_stream[!is.na(down_stream)]
down_stream=down_stream[down_stream>0]
match_downstream=match(down_stream,outlets)
outlet_ind=match(outlets[match_downstream],dd_mat_sort[,1])
outlet_ind=outlet_ind[!is.na(outlet_ind)]
if(length(outlet_ind)>0){
dist_mat=dd_mat_sort[outlet_ind,15]
get_distance=min((dd_mat_sort[i,15]-dist_mat),na.rm=TRUE)
if(get_distance>dist){
  outlet=dd_mat_sort[i,1] } else {
    outlet=NA
  }

}else { outlet=dd_mat_sort[i,1]   }





outlets=c(outlets,outlet)
outlets=outlets[!is.na(outlets)]

}

ALL_outlets=c(ALL_outlets,outlets)
rm(outlets)

}




ALL_combine=c(ALL_outlets,downstream_point[,1])
ALL_combine=ALL_combine[!is.na(ALL_combine)]
ID=match(ALL_combine,xx[,1])
dr1=xx[ID,19]
dr2=xx[ID,20]


data=cbind(dr1,dr2)
dat.sort = t(apply(data, 1, sort))
data=data[!duplicated(dat.sort),]


df2=data.frame(X=data[,1],Y=data[,2],ID=seq(1,(dim(data)[1]),1))


lots <- SpatialPointsDataFrame( coords = cbind(df2$X,df2$Y), data = df2) 
writeOGR( lots, dsn = Outshapefolder , layer = Outshapefile , driver='ESRI Shapefile',overwrite=TRUE) 





