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

_nodesFile = "nodes.in"
_hostFile = "hammer_hosts"

def getNumberOfSlaves():
  """
  Returns the value of the environmental variable noOfSlaves
  """
  
  try:
    noOfSlaves = int(os.environ.get('OMP_NUM_THREADS'))
    
  except:
    noOfSlaves = 0
    
  return noOfSlaves
  
def log(caller, message, indent=0):
  """
  Log output to screen
  
  """
  
  now = datetime.datetime.now().strftime("%d/%m/%y, %H:%M:%S: %f")
  ind = ""
  for _ in xrange(indent):
      ind += "  "
      
  print "[%s]: %s%s >> %s" % (now, ind, caller, message)

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
  
def uniqueItems(seq):
    """
    Return list of unique items in given list.
    
    """
    # Order preserving
    seen = set()
    return [x for x in seq if x not in seen and not seen.add(x)]
