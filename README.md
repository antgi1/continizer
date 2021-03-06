# CONTINIZER

This is a python graphical interface for the inverse Laplace transform program called Contin by Provencher.
In particular, this interface was made for the purpose of analyzing dynamic light scattering (DLS) / photon correlation spectroscopy (PCS) data.
This is not a reimplementation of Contin but will improve your workflow and can be handy for quick visualization of your data.

You will require a working Contin executable.
The Fortran source code for Contin is freely available together with documentation at:
http://s-provencher.com/contin.shtml

A compiled version is provided in this reposity that might work for you if you have a Windows system.

![](https://raw.githubusercontent.com/antgi1/continizer/master/screen.png "Continizer screenshot.")

## Functionality

Drag and drop of files. Choose alpha value. Visualize input and output. Apply Siegert's relationship. Export result. Read values from screen.

## Supported data files

Formats currently supported include data from:
 * LSI 3dDLS
 * ALV setups (ascii and binary)
 * Correlator.com
 * Two column files with no header. (tau and correlation)
 
## Setting your F-star

To correctly go from intensity auto-corelation function to field auto-correlation function (through Siegert's relationship) you will need to set the proper F-star value on the FSTAR.in file according to your optical setup. 

## CONTIN.IN 

Contin accepts input parameters through a file usually named contin.in. Tuning of the paremeters affects the output and can be done for example to use contin on data from different nature. 
The default parameters used by the continizer are in the file parameters.in. These are specific to DLS and set by professionals in the field.

## Disclaimer

I apologize if currently the code is dirty and poorly commented. This was one of my first projects and could do with improvement.
Some options might be OS specific and could break the code. 
