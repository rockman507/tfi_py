from distutils.core import setup
from distutils.extension import Extension
from Cython.Distutils import build_ext
import numpy

setup(
    cmdclass = {'build_ext': build_ext},
    ext_modules = [Extension("calc_phase_cython", ["calc_phase_cython.pyx"],include_dirs=[numpy.get_include()])]
    #ext_modules = [Extension("calc_phase", ["calc_phase.pyx"])]
    
)
