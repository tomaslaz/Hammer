#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Wrapper for the FHI-aims shared library

@author Tomas Lazauskas, 2016
@web www.lazauskas.net/hammer
@email tomas.lazauskas[a]gmail.com
"""

import os
import sys
import copy

from mpi4py import MPI

import ctypes
from ctypes import cdll, POINTER, c_int, byref, c_bool

import numpy as np

# Loading the library

_testlib = cdll.LoadLibrary(os.path.join("/Users/Tomas/Software/fhi-aims.071914_72/lib", "libaims.071914_7.scalapack.mpi.so"))

#_testlib = cdll.LoadLibrary(os.path.join(os.path.dirname(__file__), "Library", "testLib.so"))

_testlib.aims_.argtypes = [POINTER(c_int), POINTER(c_int), POINTER(c_bool)]
_testlib.aims_.restype = None

_faimsOutExt = "fout"

def runAims(comm, data, useMpi):
  """
  
  fout_int = 6 -> Directs output into the standard output
  """
  
  fout_int = 6
  comm_int = comm.py2f()
  
  sys.stdout.flush()
  newstdout = os.dup(1)
  
  outputFile = "%s.%s" % (data.name, _faimsOutExt)
          
  # redirecting standard output
  sys.stdout.flush()
  
  so = os.open(outputFile, os.O_RDWR|os.O_CREAT)
  
  os.dup2(so, sys.stdout.fileno())
  
  _testlib.aims_(byref(c_int(comm_int)), byref(c_int(fout_int)), byref(c_bool(useMpi)))
      
  sys.stdout.flush()
  
  devnull = os.open(os.devnull, os.O_WRONLY)
  
  os.dup2(devnull, 1)
  os.close(devnull)
  
  sys.stdout = os.fdopen(newstdout, 'w')
  
if __name__ == "__main__":
  """
  Testing the routine
  
  """
  
  temp = None
  
  temp.name = "foo.txt"
  
  runAims(MPI.COMM_SELF, outputFile, True)
  