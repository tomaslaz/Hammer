"""
HAMMER - an MPI based python package to run client/server model on a machine

@author Tomas Lazauskas, 2016
@web www.lazauskas.net/hammer
@email tomas.lazauskas[a]gmail.com
"""

import sys
from optparse import OptionParser

import source.Version as Version
import source.Server as Server
import source.Utilities as Utilities

def commandLineArgs(name, version):
  """
  Reads in command line arguments
  
  """
  
  usage = "usage: %s" % (name)
  versionStr = "%prog v." + version
  
  parser = OptionParser(usage=usage, version=versionStr)
      
  parser.disable_interspersed_args()

  (options, args) = parser.parse_args()
  
  # make sure there are the correct number of arguments
  if (len(args) != 0):
    parser.error("incorrect number of arguments")
              
  return options, args

def main():
  """
  The main routine
  
  """
  
  # printing the version and author
  version, _ = Version.getVersion()
  Version.printVersionAuthor()
  
  # command line arguments
  options, args = commandLineArgs(Version.getName(), version)
  
  numberOfSlaves = Utilities.getNumberOfSlaves()
  
  if numberOfSlaves == 0:
    Utilities.log(__name__, ": WARNING: OMP_NUM_THREADS is not set! Using a default value: 1.", 0)
    numberOfSlaves = 1
    
  else:
    Utilities.log(__name__, "OMP_NUM_THREADS is set to %d" % (numberOfSlaves), 0)

  # preparing the hosts according to nodes.in file
  numberOfProc = Utilities.prepareHostFile(slavenp=numberOfSlaves)
  
  # running the server and executing the jobs
  Server.main(numberOfProc)
  
if __name__ == "__main__":
  
  main()