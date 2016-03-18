"""
A module to do miscellaneous tasks

@author Tomas Lazauskas, 2016
@web www.lazauskas.net/hammer
@email tomas.lazauskas[a]gmail.com
"""

import collections
import datetime
import os
import sys

import System

_nodesFile = "nodes.in"
_hostFile = "hammer_hosts"

def getFileFullName(filePath):
  """
  Returns a filename from a path
  
  """
  
  return os.path.basename(filePath)

def getFileName(filePath):
  """
  Returns a filename from a path
  
  """

  return os.path.splitext(os.path.basename(filePath))[0]

def getNumberOfSlaves():
  """
  Returns the value of the environmental variable noOfSlaves
  """
  
  try:
    noOfSlaves = int(os.environ.get('OMP_NUM_THREADS'))
    
  except:
    noOfSlaves = 0
    
  return noOfSlaves
  
def getStructuresFileList(dirPath=None):
  """
  Get the list of files
  
  """
  
  extList=['xyz']
  
  if dirPath is not None:
    cwd = os.getcwd()
    os.chdir(dirPath)
  
  filesList = []
  
  for root, _, files in os.walk("./"):
    for fileName in files:
      
      for ext in extList:
      
        if fileName.endswith(ext):
          
          filesList.append(os.path.join(dirPath, fileName))

  if dirPath is not None:
    os.chdir(cwd)
    
  return filesList

def log(caller, message, indent=0):
  """
  Log output to screen
  
  """
  
  now = datetime.datetime.now().strftime("%d/%m/%y, %H:%M:%S: %f")
  ind = ""
  for _ in xrange(indent):
      ind += "  "
      
  print "[%s]: %s%s >> %s" % (now, ind, caller, message)

def readInStructures(inputDirectory):
  """
  Read in the structures to be data mined
  
  """
  success = True
  error = ""
  
  systemsList = []
  filesCnt = 0
  systemsCnt = 0
      
  # look for structures in the input directory
  filesList = getStructuresFileList(inputDirectory)
  filesCnt = len(filesList)
  
  log(__name__, "Server   | Found %d files to be read in" % (filesCnt), 0)
  
  if filesCnt < 1:
    success = False
    error = __name__ + ": could not find structures to read in!"
    
    return success, error, systemsList
  
  log(__name__, "Server   | Reading in initial systems ", 0)
  
  for file in filesList:
    log(__name__, "Server   | Reading in %s" % (file), 0)

    read, readError, system = readSystemFromFileXYZ(file)
    
    if read:
      systemsList.append(system)
    else:
      log(__name__, "Server   | Error while reading file %s: %s" % (file, readError), 0)
  
  # counting the number of read-in systems
  if success:
    noOfSystems = len(systemsList)
      
  return success, error, systemsList, noOfSystems

def prepareHostFile(slavenp=1):
  """
  Read nodes file and prepares a host file
     
  """
    
  if not os.path.exists(_nodesFile):
    sys.exit(__name__+": ERROR: nodes file does not exist: " + _nodesFile)
   
  log(__name__, "Reading nodes file: %s" % (_nodesFile), 0)
   
  # first read the nodes.IN file
  f = open(_nodesFile)
   
  count = 0
  nodeList = []

  for line in f:
    line = line.strip()
     
    if not len(line):
      continue
     
    node = line
    nodeList.append(node)
        
  f.close()
   
  # and get a list of the unique nodes
  uniqueNodes = uniqueItems(nodeList)
  uniqueNodesNWorkers = collections.Counter(nodeList)
  
  # checking if number of workers on nodes are scalable
  for node in uniqueNodes:  
    NWorkers = uniqueNodesNWorkers[node]
    
    if NWorkers % slavenp != 0:
      sys.exit(__name__ + " node: " + node + " dedicated " + str(NWorkers) + 
        " workers which is not scalable by " + str(slavenp))    
          
  NNodes = len(nodeList)
  NUniqueNodes = len(uniqueNodes)
   
  log(__name__, "%d unique nodes (%d clients)" % (NUniqueNodes, NNodes), 0)
  for node in uniqueNodes:
    log(__name__, "Unique node %s (%d clients)" % (node, uniqueNodesNWorkers[node]), 0)
  
  try:
    fout = open(_hostFile, "w")
  except:
    success = False
    error = __name__ + ": Cannot open: " + _hostFile
  
  procCnt = 0
  
  for node in uniqueNodes:
    NWorkers = uniqueNodesNWorkers[node]
    
    hostsCnt = int(NWorkers / slavenp)
    procCnt += hostsCnt
    
    for _ in range(hostsCnt):
      fout.write("%s\n" % node)
  
  fout.close()
  
  return procCnt
  
def readSystemFromFileXYZ(fileName):
  """
  Reads in the structure of a system from a XYZ file.
  
  """
  
  success = False
  error = ""
  system = None
  
  if not os.path.isfile(fileName):
    error = __name__ +  "File [%s] doesn't exist." % (fileName)
    return success, error, system
  
  try:
    f = open(fileName)
  except:
    error = __name__ +  "Cannot read file [%s]" % (fileName)
    return success, error, system
  
  line = f.readline().strip()
  
  NAtoms = int(line)
      
  system = System.System(NAtoms)
  
  # additional info
  line = f.readline().strip()
  
  array = line.split()

  # atoms and their positions
  i = 0
  for line in f:
      array = line.strip().split()

      sym = array[0].strip()
      
      if sym not in system.specieList:
          system.addSpecie(sym)
      
      specInd = system.specieIndex(sym)
      
      system.specieCount[specInd] += 1
      
      system.specie[i] = specInd
      
      for j in range(3):
          system.pos[i*3 + j] = float(array[j+1])
      
      try:
          system.charge[i] = array[4]
      except:
          system.charge[i] = 0.0
      
      i += 1
      
      if i == NAtoms:
        break
  
  f.close()
  
  system.name = getFileName(fileName)
  system.fileName = getFileFullName(fileName)
  
  success = True
  
  return success, error, system

def uniqueItems(seq):
    """
    Return list of unique items in given list.
    
    """
    # Order preserving
    seen = set()
    return [x for x in seq if x not in seen and not seen.add(x)]
