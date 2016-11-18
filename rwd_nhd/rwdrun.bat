Rem   Handy batch file to run rapid watershed delineation

rem  to run this
rem   rwdrun -91.189921  35.019947 D:\Dropbox\Projects\MMW2_StroudWPenn\RWDWork\NHDPlusTest\RWDData
rem   rwdrun -91.456666  35.073693 D:\Dropbox\Projects\MMW2_StroudWPenn\RWDWork\NHDPlusTest\RWDData
rem   rwdrun -91.225453  35.601564 D:\Dropbox\Projects\MMW2_StroudWPenn\RWDWork\NHDPlusTest\RWDData

set x=%1
set y=%2
Set ScriptDIR=D:\Dropbox\Projects\MMW2_StroudWPenn\RWDWork\Code\RWDRepo\rwd_nhd\
set PY27="C:\Python27\python.exe"
Set WorkDir=%3  

%PY27% %ScriptDIR%NHD_Rapid_Watershed_Delineation.py %x% %y% 1 10000 %WorkDir% gwgrid.tif gwmaster 8 "C:\Program Files\TauDEM\TauDEM5Exe" "C:\Program Files\Microsoft MPI\Bin" DelineatedWatershed





