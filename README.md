cgui1
=====
First time trying to use a respository.

This is a project for taking data from a Twyman-Green interferometer camera and:
* Extract phase using 9-bin bucket algorithm<br />
* Unwrap phase via unwrap algorithms in compiled C code<br />
* Apply a Zernike fit<br />
  


To do
* Organize files
* Change code to follow PEP8 (at least I know a few spots I broke the 80col<br />
    and short nondescript variable name dogmas
* Clean out old test spots in the code<br />
* All libraries availible in 3.3 so update code to 3.3 from 2.7<br />
* Convert unwrap algorithms to cython to avoid a subprocess call to an .exe file<br />
  
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
  
