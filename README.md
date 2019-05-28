# CONTINIZER

This is a python graphical interface for the popular inverse Laplace transform program called Contin by Provencher.
In particular, this interface was made for the purpose of analyzing dynamic light scattering (DLS) data.
This is not a reimplementation of Contin but will improve your workflow and can be handy for quick visualization of your data.

You will require a working Contin executable.
The Fortran source code for Contin is freely available together with documentation at:
http://s-provencher.com/contin.shtml

A compiled version is provided in this reposity that might work for you if you have a Windows system.


## Supported data files

Formats currently supported include data from:
 * LSI 3dDLS
 * ALV setups (ascii and binary)
 * Correlator.com
 * Two column files with no header. (tau anc correlation)

## Disclaimer

I apologize if currently the code is dirty and poorly commented. This was one of my first projects and could do with some improvement.
