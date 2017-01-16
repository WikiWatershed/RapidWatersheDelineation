import os
import glob
import zipfile

files = glob.glob("Subwatershed_ALL/*")
#print (files)
nfiles=len(files)
startdir = os.getcwd()
for subdir in files:
    print subdir
    os.chdir(startdir)
    os.chdir(subdir)

    files2=glob.glob("*plen*")
    print files2
    for file in files2:
        os.remove(file)

    files2 = glob.glob("*tlen*")
    print files2
    for file in files2:
        os.remove(file)

    files2 = glob.glob("*ad8*")
    print files2
    for file in files2:
        os.remove(file)

    files2 = glob.glob("*ord*")
    print files2
    for file in files2:
        os.remove(file)

print("Done")
