TFI_gui
=====
First time trying to use a respository.

This is a project for taking data from a Twyman-Green interferometer camera and:
* Extract phase using 9-bin bucket algorithm
* Unwrap phase via unwrap algorithms in compiled C code
* Apply a Zernike fit
  
Required Packages
* easygui (0.96)
* h5py (2.1.3-2.2.0)
* libtim(v0.1.2) https://github.com/tvwerkhoven/libtim-py
* matplotlib (1.2.1) 
* numpy (1.7.1-1.8.0b2)
* PIL (1.1.7)
* pyfits (3.1.2)<br />
Think matplotlib and pyfits were a requirement for libtim (see link)

To do
* Organize files
* Change code to follow PEP8 (at least I know a few spots I broke the 80col
    and short nondescript variable name dogmas)
* Clean out old test spots in the code
* All libraries availible in 3.3 so update code to 3.3 from 2.7
* Convert unwrap algorithms to cython to avoid a subprocess call to an .exe file
  
Issues
* Get_phase calls using Pool() from gui.py takes longer for every additional process<br />
Process=1, time=3.733974<br />
Process=4, time=3.793044<br />
Process=8, time=6.298794<br />
Process=12, time=8.576280<br />
When calling wrapped_phase.py as a standalone:<br />
Process=1, time=1.895561<br />
Process=4, time=0.682514<br />
Process=8, time=0.518194<br />
Process=12, time=0.562433<br />
see multiprocessor times.txt
  
