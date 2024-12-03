# STL_Mold_Maker
 
Creates a negative space mold based on a given STL input file.

Default Usage:

>python3 ./makeMold.py myfile.stl

Will output 2 files, myfile_bottom.stl and myfile_top.stl

Will generate keys and recesses; as well as the pour spout.

The default usage sets the wall thickness around the negative space to 10.0mm.  If you use the --wall_thickness switch you can change the thickness to meet your needs.  For example:

>python3 ./makeMold.py myFile.stl --wall_thickness 20.0

This will set a wall thickness of 20mm.
