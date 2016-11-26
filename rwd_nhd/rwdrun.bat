Rem   Handy batch file to run rapid watershed delineation

rem  to run this
rem   rwdrun -91.189921  35.019947 D:\Dropbox\Projects\MMW2_StroudWPenn\RWDWork\NHDPlusTest\RWDData
rem   rwdrun -91.456666  35.073693 D:\Dropbox\Projects\MMW2_StroudWPenn\RWDWork\NHDPlusTest\RWDData
rem   rwdrun -91.225453  35.601564 D:\Dropbox\Projects\MMW2_StroudWPenn\RWDWork\NHDPlusTest\RWDData
rem   rwdrun -91.174346  35.348277 D:\Scratch\RWD\NHDPlusTest\RWDData

rem   rwdrun -97.008557  34.911545 C:\Users\dtarb\NHDPlus\RWDData  Canadian River Reg 11b
rem rwdrun -103.397504  35.926497 C:\Users\dtarb\NHDPlus\RWDData  Internal drain reg 11b
rem rwdrun -103.396947  35.926677 C:\Users\dtarb\NHDPlus\RWDData  Internal drain reg 11b
rem rwdrun -103.397694  35.926916 C:\Users\dtarb\NHDPlus\RWDData  Internal drain reg 11b
rem rwdrun -103.578959  35.922686 C:\Users\dtarb\NHDPlus\RWDData  Snap test reg 11b

rem rwdrun -103.579370  35.917488  C:\Users\dtarb\NHDPlus\RWDData  Snap test reg 11b
rem rwdrun -103.637710  35.858201  C:\Users\dtarb\NHDPlus\RWDData  Already on stream reg 11b


set x=%1
set y=%2
Set ScriptDIR=D:\Dropbox\Projects\MMW2_StroudWPenn\RWDWork\Code\RWDRepo\rwd_nhd\
set PY27="C:\Python27\python.exe"
Set WorkDir=%3  

%PY27% %ScriptDIR%NHD_Rapid_Watershed_Delineation.py %x% %y% 1 10000 %WorkDir% gwgrid.tif gwmaster 8 "C:\Program Files\TauDEM\TauDEM5Exe" "C:\Program Files\Microsoft MPI\Bin" DelineatedWatershed





