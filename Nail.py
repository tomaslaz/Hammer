#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
MPI based Cient side of the Task manager to run FHI-aims.

@author Tomas Lazauskas, 2016
"""

import datetime
import sys
import time

from mpi4py import MPI

import Aimer
import Config

class client(object):
  """
  MPI Client class.
    
  """
   
  workDir = None
  
  def __init__(self, workDir, clientOutputPath):
    """
    Constructor
    
    """
    
    self.data = None
    self.worker = None
    
    self.clientOutputPath = clientOutputPath
        
    self.workDir = workDir
    
    self.comm = MPI.Comm.Get_parent()
    self.rank = self.comm.Get_rank()
    self.size = self.comm.Get_size()

    
    time.sleep(0.1)
    
    # The work LOOP
    while True:
      
      status = MPI.Status()
      data = self.comm.recv(source=0, tag=Config._MPITagServer, status=status)
      
      # need to use the same communicator to send back data to the server
      sourceRank = status.Get_source()
      parentComm = self.comm.Get_parent()
      
      log(__name__, "Worker %000d | Received message [%s] from the server " % (self.rank, data[Config._MPISignalDataTag]), 1)
      
      if (data[Config._MPISignalDataTag] == Config._MPISignalStop):
        
        self._sendStopSignal(sourceRank)
        
        break
      
      elif (data[Config._MPISignalDataTag] == Config._MPISignalData):
        
        log(__name__, "Worker %000d | received data" % (self.rank), 1)
        
        self.data = data[Config._MPIDataTag]
                      
      else:
        # lets say it did something
        self._sendFinishedSignal(sourceRank)
        
      # do the work
      if (self.data is not None):
               
        log(__name__, "Worker %000d | started working on data" % (self.rank), 1)
                
        Aimer.runAims(self.comm, self.data, True)
        
        self._sendFinishedSignal(sourceRank)
                
        self._sendReadyForDataSignal(sourceRank)
        
        self.data = None
    
    # stop the client
    self.comm.Disconnect()
  
  def _sendStopSignal(self, dest):
    """
    Sends a signal to the server that it is stopping
    
    """
    
    log(__name__, "Worker %000d | received a STOP signal" % (self.rank), 1)
        
    log(__name__, "Worker %000d | sending a QUIT response" % (self.rank), 1)
    
    # sending QUIT message to the server
    dataPackage = {Config._MPIRankTag:self.rank, 
                   Config._MPISignalDataTag:Config._MPISignalQuit}
    
    self.comm.send(dataPackage, dest=dest, tag=Config._MPITagClient)
  
  def _sendFailedSignal(self, dest, failedMessage):
    """
    Sends a signal to the server that the job has failed
    
    """
    
    log(__name__, "Worker %000d | sending a FAILURE response: %s" % (self.rank, failedMessage), 1)
        
    dataPackage = {Config._MPIRankTag:self.rank, 
                   Config._MPISignalDataTag:Config._MPISignalFailed,
                   Config._MPIMessageTag:failedMessage}
    
    self.comm.send(dataPackage, dest=dest, tag=Config._MPITagClient)
  
  def _sendFinishedSignal(self, dest):
    """
    Sends a signal to the server that it is finished its job
    
    """
    
    log(__name__, "Worker %000d | sending a FINISHED response" % (self.rank), 1)
        
    dataPackage = {Config._MPIRankTag:self.rank, 
                   Config._MPISignalDataTag:Config._MPISignalFinished}
    
    self.comm.send(dataPackage, dest=dest, tag=Config._MPITagClient)
    
  def _sendReadyForDataSignal(self, dest):
    """
    Sends a signal to the server that it is ready to receive data
    
    """
    
    log(__name__, "Worker %000d | sending a READY 4 DATA response" % (self.rank), 1)
    
    dataPackage = {Config._MPIRankTag:self.rank, 
                   Config._MPISignalDataTag:Config._MPISignalReady4Data}
    
    self.comm.send(dataPackage, dest=dest, tag=Config._MPITagClient)
  
def log(caller, message, indent=0):
  """
  Log output to screen
  
  """
  
  now = datetime.datetime.now().strftime("%d/%m/%y, %H:%M:%S: %f")
  ind = ""
  for _ in xrange(indent):
      ind += "  "
      
  print "[%s]: %s%s >> %s" % (now, ind, caller, message)

if __name__ == "__main__":
  """
  The main MPI client loop.

  """
  
  if len(sys.argv) != 3:
    print "Usage: Nail.py WORKDIR OUTPUTDIR"
    print sys.argv
    sys.exit(1)
  
  client = client(sys.argv[1], sys.argv[2])