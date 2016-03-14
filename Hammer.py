#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
MPI based Cient-Server Task manager to run FHI-aims.

@author Tomas Lazauskas, 2016
"""

import datetime
import glob
import os
import sys
import subprocess
import time

from mpi4py import MPI


import Config
import System

######################################################
np = 2

class Server(object):
  """
  The MPI Server class.
  
  """
  
  def __init__(self):
    """
    Constructor
    
    """
    
    self.initialised = False
    self.np = np
    
    self.comm = None
    self.outputDir = None

    self.tmpLocation = None
    self.workSpace = None
    
    # Getting the source directory
    self.srcDir = os.path.dirname(__file__)
    (_, self.srcDirName) = os.path.split(self.srcDir)
    
    self.workSpace = os.getcwd()
    self.outputDir = os.getcwd()
        
    self.startTimeStamp = datetime.datetime.now().strftime("%y%m%d-%H%M%S")
  
  def initiate(self):
    """
    Initiates the server
     
    """
    
    self._startClients()
    
    self.initialised = True
    
  def finalise(self):
    """
    Shutdown the server
     
    """
    
    self._terminateClients()
    
    self.initialised = False
  
  def getResult(self):
    
    """
    Get a result from the result queue.
     
    """
    
    result = self.comm.recv(source = MPI.ANY_SOURCE, tag = Config._MPITagClient)
    
    if (result[Config._MPISignalDataTag] == Config._MPISignalFinished):
      empty = 0
      
    else:
      empty = 1
    
    return result, empty
    
  def sendDataToClient(self, clientRank, data, tag=Config._MPITagServer):
    """
    Sends data to an MPI client
    
    """
                   
    log(__name__, "Server   | Sending data to client %d" % (clientRank), 0)
    
    dataPackage = {Config._MPISignalDataTag:Config._MPISignalData, Config._MPIDataTag:data}
    
    self.comm.send(dataPackage, dest=clientRank, tag=tag)
  
  def sendWorkerToClient(self, clientRank, worker, tag=Config._MPITagServer):
    """
    Sends worker object to an MPI client
    
    """
    
    log(__name__, "Server   | Sending worker object to client %d" % (clientRank), 0)
    
    dataPackage = {Config._MPISignalDataTag:Config._MPISignalWorker, Config._MPIWorkerTag:worker}
    
    self.comm.send(dataPackage, dest=clientRank, tag=tag)
  
  def sendStopSignalToClient(self, clientRank, tag=Config._MPITagServer):
    """
    Sends STOP signal to an MPI client
    
    """
    
    log(__name__, "Server   | Sending a STOP signal to client %d" % (clientRank), 0)
    
    dataPackage = {Config._MPISignalDataTag:Config._MPISignalStop}
    
    self.comm.send(dataPackage, dest=clientRank, tag=tag)
  
  def sendStopSignalToAll(self, tag=Config._MPITagServer):
    """
    Sends STOP signal to all MPI clients
    
    """
    
    log(__name__, "Server   | Sending STOP SIGNALS", 0)
    
    for i in range(self.np):
      
      self.sendStopSignalToClient(i, tag=tag)
  
  def _startClients(self):
    """
    Start MPI clients.
     
    """
    
    log(__name__, "Server   | Starting MPI clients: %d" % (self.np), 0)
    
    self.comm = MPI.COMM_SELF.Spawn(sys.executable, 
      args=[os.path.join(self.srcDir, 'Nail.py'), self.workSpace, self.outputDir], maxprocs=self.np)
        
    self.rank = self.comm.Get_rank()
  
  def _terminateClients(self):
    """
    Stop MPI Client.
     
    """
    
    # terminating clients
    self.sendStopSignalToAll(tag=Config._MPITagServer)
    
    recvCnt = 0
    while True:
      
      clientData = self.comm.recv(source = MPI.ANY_SOURCE, tag = Config._MPITagClient)
      
      #print "Package No: %d, Got this from a client: " % (recvCnt), clientData
      
      if (clientData[Config._MPISignalDataTag] == Config._MPISignalQuit):
        recvCnt += 1
      
      if (recvCnt == self.np):
        break
      
    log(__name__, "Server   | MPI clients stopped", 0)
    
    self.comm.Disconnect()

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
  
def log(caller, message, indent=0):
  """
  Log output to screen
  
  """
  
  now = datetime.datetime.now().strftime("%d/%m/%y, %H:%M:%S: %f")
  ind = ""
  for _ in xrange(indent):
      ind += "  "
      
  print "[%s]: %s%s >> %s" % (now, ind, caller, message)

def main():
  """
  
  
  """
  
  results = []
  
  # reading the structures
  success, error, systemsList, systemsCnt = readInStructures(os.getcwd())
  
  if not success:
    sys.exit("ERROR: %s" % (error))
  
  server = Server()
  
  # initiating the server
  server.initiate()
  
  # sending the initial data
  serverStartTime = time.time()
  
  for clientRank in range(min(np, systemsCnt)):
    server.sendDataToClient(clientRank, systemsList.pop(), Config._MPITagServer)
  
  recvCnt = 0
  
  while True:
  
    clientData, empty = server.getResult()
    
    log(__name__, "Server   | Received message [%s] from client %d " % (clientData[Config._MPISignalDataTag], 
                                                                        clientData[Config._MPIRankTag]), 0)
    
    if ((clientData[Config._MPISignalDataTag] == Config._MPISignalFinished) or 
        (clientData[Config._MPISignalDataTag] == Config._MPISignalFailed)):
        
      results.append(clientData)
      
      recvCnt += 1  
          
    elif (clientData[Config._MPISignalDataTag] == Config._MPISignalReady4Data):
      
      if len(systemsList) > 0:
      
        dataPackage = systemsList.pop()
        clientRank = clientData[Config._MPIRankTag]
  
        server.sendDataToClient(clientRank, dataPackage)
        
      else:
        log(__name__, "Server   | No more jobs to send to client %d " % (clientData[Config._MPIRankTag]), 0)
        
    if (recvCnt >= systemsCnt):
      break
  
  server.finalise()

if __name__ == '__main__':
  """
  It's hammer time!
  
  """
  
  main()