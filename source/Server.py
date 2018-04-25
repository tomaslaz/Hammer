#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
MPI based Cient-Server Task manager to run FHI-aims.

@author Tomas Lazauskas, 2016-2018
@web lazauskas.net
@email tomas.lazauskas[a]gmail.com
"""

import datetime
import glob
import os
import sys
import subprocess
import time

from mpi4py import MPI

from . import Config
from . import Utilities
from .Utilities import log

class Server(object):
  """
  The MPI Server class.
  
  """
  
  def __init__(self, np):
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
    
    myinfo = MPI.Info.Create()
    
    # TODO: this file should be automatically generated. The number of entries should match self.np
    myinfo.Set("hostfile", "hammer_hosts")
    
    log(__name__, "Server   | Starting MPI clients: %d" % (self.np), 0)

    self.comm = MPI.COMM_WORLD.Spawn(sys.executable, 
      args=[os.path.join(self.srcDir, 'Client.py'), self.workSpace, self.outputDir], maxprocs=self.np, info=myinfo)
            
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
  
def main(np):
  """
  The main loop.
  
  """
  
  dataPackList = []
  results = []
  success = True
  error = "Data has not been read in"
  
  # A section to read in the data to send it to the clients
  # The read in data should be a list: dataPackList
  
  # Example
  dataPackList = ["apple", "orange"]
  
  """ <<< Insert code here >>> """
  
  dataPackCnt = len(dataPackList)
  
  if (dataPackCnt <= 0):
    success = False
    error = "Have not read any data!"
  
  if not success:
    sys.exit("ERROR: %s" % (error))
  
  server = Server(np)
  
  # initiating the server
  server.initiate()
  
  # sending the initial data
  serverStartTime = time.time()
  
  for clientRank in range(min(np, dataPackCnt)):
    server.sendDataToClient(clientRank, dataPackList.pop(), Config._MPITagServer)
  
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
      
      if len(dataPackList) > 0:
      
        dataPackage = dataPackList.pop()
        clientRank = clientData[Config._MPIRankTag]
  
        server.sendDataToClient(clientRank, dataPackCnt)
        
      else:
        log(__name__, "Server   | No more jobs to send to client %d " % (clientData[Config._MPIRankTag]), 0)
        
    if (recvCnt >= dataPackCnt):
      break
  
  server.finalise()
  
  # 
  # A section to post-process the data received from the clients
  #
  
  """ <<< Insert code here >>> """
  
  log(__name__, "Server   | Finished ", 0)

if __name__ == '__main__':
  """
  It's hammer time!
  
  """
  
  main()