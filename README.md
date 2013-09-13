cgui1
=====
First time trying to use a respository.

This is a project for taking data from a Twyman-Green interferometer camera and:

  *Extract phase using 9-bin bucket algorithm
  
  *Unwrap phase via unwrap algorithms in compiled C code
  
  *Apply a Zernike fit
  


To do

  *Organize files
  
  *Change code to follow PEP8 (at least I know a few spots I broke the 80col
    and short nondescript variable name dogmas
    
  *Clean out old test spots in the code
  
  *All libraries availible in 3.3 so update code to 3.3 from 2.7
  
  *Convert unwrap algorithms to cython to avoid a subprocess call to an .exe file
  
Issues

  *Get_phase calls using Pool() from gui.py takes longer for every additional process
  
      Process=1, time=3.733974
      Process=4, time=3.793044
      Process=8, time=6.298794
      Process=12, time=8.576280
    When calling wrapped_phase.py as a standalone:
    
      Process=1, time=1.895561
      Process=4, time=0.682514
      Process=8, time=0.518194
      Process=12, time=0.562433
      
    see multiprocessor times.txt
  
