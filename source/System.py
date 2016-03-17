#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
System module

@author Tomas Lazauskas
@web www.lazauskas.net/hammer
@email tomas.lazauskas[a]gmail.com
"""

import copy
import sys
import os

import numpy as np

from source import Atoms

class System(object):
  """
  A class to save the structure of a system.
    
  """
    
  def __init__(self, NAtoms):
    
    self.name = ""
    self.fileName = ""
    
    self.totalEnergy = 0.0
    self.energyDefinition = ""
    self.NAtoms = NAtoms
    
    self.cellDims = np.zeros(3, np.float64)
    self.cellAngles = np.empty(3, np.float64)
    
    self.cellType = None
    self.coordType = None 
    
    self.coordConverted = False
    self.coordTransfMatrix = None
    
    self.specie = np.empty(self.NAtoms, np.int32)
    self.pos = np.empty(3*self.NAtoms, np.float64)
    self.minPos = np.empty(3, np.float64)
    self.maxPos = np.empty(3, np.float64)
    
    self.charge = np.empty(self.NAtoms, np.float64)
    
    self.com = np.empty(3, np.float64)
    self.momentOfInertia = np.zeros([3, 3], np.float64)
    
    # specie
    dt = np.dtype((str, 2))
    self.specieList = np.empty(0, dt)
    self.specieCount = np.empty(0, np.int32)
    
    # core, shel, mesh
    dt2 = np.dtype((str, 4))
    self.atomType = np.empty(self.NAtoms, dt2)
    
    # mesh
    self.mesh = np.empty(self.NAtoms, np.int32)
    self.meshList = np.empty(0, np.int32)
    self.meshCount = np.empty(0, np.int32)
    self.meshArrays = []
    
    self.PBC = np.zeros(3, np.int32)
    
    # additional data
    self.addData1 = np.empty(self.NAtoms, np.float64)
    self.addData2 = np.empty(self.NAtoms, np.float64)
    
    self.addData3 = np.empty(self.NAtoms, np.int32)
    self.addData4 = np.empty(self.NAtoms, np.int32)
    self.addData5 = np.empty(self.NAtoms, np.int32)
    
    # vacancy flag
    self.vacancyCnt = 0
    self.vacancyType = np.zeros(NAtoms, np.int32)
    
    # hashkeys
    self.hashkeyRadius = 0.0
    self.hashkey = None
    
    # point group
    self.pointGroup = ""
    
    # GULP header and footer
    self.gulpHeader = None
    self.gulpFooter = None
    
    # flag to update properties
    self.__propertiesUpdated = False
    
  def addAtom(self, sym, pos, charge):
    """
    Add an atom to the system
    
    """
    
    if sym not in self.specieList:
        self.addSpecie(sym)
    
    specInd = self.specieIndex(sym)
    
    self.specieCount[specInd] += 1
    
    pos = np.asarray(pos, dtype=np.float64)
    
    self.specie = np.append(self.specie, np.int32(specInd))
    self.pos = np.append(self.pos, pos)
    self.charge = np.append(self.charge, charge)

    self.NAtoms += 1
    
  def calcCOM(self):
      
    """
    Calculates the centre of mass of a system
    
    """
    
    totMass = 0.0
    self.com[:] = 0.0
    
    for i in range(self.NAtoms):
      atomMass = Atoms.atomicMassAMU(self.specieList[self.specie[i]])
      totMass += atomMass
      
      for j in range(3):
        self.com[j] += atomMass * self.pos[3*i + j]

    self.com = self.com / totMass
  
  def calcMOI(self):
    """
    Calculates moment of inertia
    
    """
    
    moi = np.zeros(6, np.float64)

    self.momentOfInertia[:] = 0.0
    
    for i in range(self.NAtoms):
      atomMass = Atoms.atomicMassAMU(self.specieList[self.specie[i]])
        
      moi[0] += (self.pos[3*i+1]**2 + self.pos[3*i+2]**2) * atomMass
      moi[1] += (self.pos[3*i+0]**2 + self.pos[3*i+2]**2) * atomMass
      moi[2] += (self.pos[3*i+0]**2 + self.pos[3*i+1]**2) * atomMass
      moi[3] += -(self.pos[3*i+0] * self.pos[3*i+1]) * atomMass
      moi[4] += -(self.pos[3*i+0] * self.pos[3*i+2]) * atomMass
      moi[5] += -(self.pos[3*i+1] * self.pos[3*i+2]) * atomMass
    
    self.momentOfInertia[0][0] = moi[0]
    self.momentOfInertia[1][1] = moi[1]
    self.momentOfInertia[2][2] = moi[2]
    
    self.momentOfInertia[0][1] = moi[3]
    self.momentOfInertia[0][2] = moi[4]
    
    self.momentOfInertia[1][0] = moi[3]
    self.momentOfInertia[1][2] = moi[5]
    
    self.momentOfInertia[2][0] = moi[4]
    self.momentOfInertia[2][1] = moi[5]
  
 
  
  def createMeshArrays(self):
    """
    Creates mesh arrays and puts atoms' indices into mesh arrays.
    
    """
    
    noMeshes = len(self.meshList)
    
    if noMeshes > 0:
      
      for i in range(noMeshes):
        meshCnt = 0
        meshIdx = self.meshList[i]
        meshArray = np.empty(self.meshCount[i], np.int32)
        
        for j in range(self.NAtoms):
          if self.mesh[j] == meshIdx:
            
            meshArray[meshCnt] = j
            meshCnt += 1
        
        self.meshArrays.append(meshArray)

  def getPropertiesStatus(self):
    """
    Returns the properties update status
    
    """
    return self.__propertiesUpdated
  
  def setPropertiesStatusUpdated(self):
    """
    Sets the properties update status as updated
    
    """
    
    self.__propertiesUpdated = True
    
  def setPropertiesStatusOutdated(self):
    """
    Sets the properties update status as oudated
    
    """
    
    self.__propertiesUpdated = False

  def removeAtom( self, index ):
    """
    Remove an atom from the structure
    
    """
    
    specInd = self.specie[index]
    self.specie = np.delete(self.specie, index)
    self.pos = np.delete(self.pos, [3*index,3*index+1,3*index+2])
    self.charge = np.delete(self.charge, index)

    self.NAtoms -= 1
    
    self.specieCount[specInd] -= 1
    if self.specieCount[specInd] == 0 and not self.specieListForced:
        self.removeSpecie(specInd)
  
  def removeSpecie(self, index):
    """
    Remove a specie from the specie list.
    
    """
    self.specieCount = np.delete(self.specieCount, index)
    self.specieList = np.delete(self.specieList, index)
    
    for i in xrange(self.NAtoms):
        if self.specie[i] > index:
            self.specie[i] -= 1

  def specieIndex(self, check):
    """
    Index of sym in specie list
    
    """
    
    count = 0
    index = -1
    for sym in self.specieList:
        if sym == check:
            index = count
            break
        
        count += 1
    
    return index 
  
  def swapAtomCoords(self, atom1Idx, atom2Idx):
    """
    Swaps the coordinates of two atoms
    
    """
    
    posTmp = copy.copy(self.pos[atom1Idx*3:(atom1Idx+1)*3])
    
    self.pos[atom1Idx*3:(atom1Idx+1)*3] = self.pos[atom2Idx*3:(atom2Idx+1)*3]
    
    self.pos[atom2Idx*3:(atom2Idx+1)*3] = posTmp

  def addMesh(self, mesh, count=None):
    """
    Add a mesh to a mesh list
    
    """
      
    if mesh in self.meshList:
        if count is not None:
            meshInd = self.meshIndex(mesh)
            self.meshCount[meshInd] = count
        
        return
    
    if count is None:
        count = 0
    
    self.meshList = np.append(self.meshList, mesh)
    self.meshCount = np.append(self.meshCount, np.int32(count))
  
  def meshIndex(self, check):
    """
    Index of mesh in mesh list
    
    """
    
    count = 0
    index = -1
    for mesh in self.meshList:
        if mesh == check:
            index = count
            break
        
        count += 1
    
    return index 
  
  def addSpecie(self, sym, count=None):
    """
    Add a specie to a specie list
    
    """
      
    if sym in self.specieList:
        if count is not None:
            specInd = self.specieIndex(sym)
            self.specieCount[specInd] = count
        
        return
    
    if count is None:
        count = 0
    
    self.specieList = np.append(self.specieList, sym)
    self.specieCount = np.append(self.specieCount, np.int32(count))
    
  def minMaxPos(self, PBC):
    """
    Finds the min and max coordinates
    """
    
    for i in xrange(3):
      if not PBC[i]:
          self.minPos[i] = self.pos[i::3].min()
          self.maxPos[i] = self.pos[i::3].max()
  
  def writeSystem(self, fileName, append=0, zipfile=False):
    """
    Write system into a file
    
    """
    
    sucess, erorr = _writeSystem(fileName, self, append, zipfile)
    
    return sucess, erorr

def _writeSystem(fileName, system, append, zipfile):
  """
  Writes system into a file depending on the format
  
  """
  
  if fileName.endswith(".xyz"):
    sucess, erorr = _writeXYZ(system, fileName, append)
    
  elif fileName.endswith(".car"):
    sucess, erorr = _writeCAR(system, fileName, append)
    
  else:
    sys.exit(__name__ +" : Undefined export format.")
  
  return sucess, erorr

def _writeCAR(system, outputFile, append=False):
  """
  Writes system as a CAR file.
  """
  
  error = ""
  success = True
  
  if system is None:
    success = False
    error = __name__ + ": no data to write"
    
    return success, error
  
  try:
    if append:
      fout = open(outputFile, "a")
    else:
      fout = open(outputFile, "w")
      
  except:
    success = False
    error = __name__ + ": Cannot open: " + filePath
    
    return success, error
  
  fout.write("%s\n" % "!BIOSYM archive 3")
 
  if (system.PBC[0] <> 0 or system.PBC[0] <> 0 or system.PBC[0] <> 0):
    success = False
    error = __name__ + ": PBC are not implemented for CAR"
  
    return success, error
  
  fout.write("%s\n" % "PBC=OFF")
    
  fout.write("\n")
  fout.write("%s\n" % "!DATE")
  
  for i in range(system.NAtoms):
    
    if not system.vacancyType[i]:
      tempStr =  ("%s%d" % (system.specieList[system.specie[i]], i+1))
      tempStr = "{:<7}".format(tempStr)
      
      fout.write("%7s %13.10f %13.10f %13.10f XXXX 1      xx      %2s %.4f\n" % (tempStr, 
        system.pos[3*i], system.pos[3*i+1], system.pos[3*i+2], 
        "{:<2}".format(system.specieList[system.specie[i]]), system.charge[i]))
  
  fout.write("end\n")
  fout.write("end\n")
  
  fout.close()
  
  return success, error

def _writeXYZ(system, outputFile, append=False):
  """
  Writes system as an XYZ file.
  """
  
  error = ""
  success = True
  
  if system is None:
    success = False
    error = __name__ + ": no data to write"
    
    return success, error
  
  try:
    if append:
      fout = open(outputFile, "a")
    else:
      fout = open(outputFile, "w")
      
  except:
    success = False
    error = __name__ + ": Cannot open: " + filePath
    
    return success, error
  
  fout.write("%d\n" % (system.NAtoms - system.vacancyCnt))
  
  metaData = "energy=%.10e" % (system.totalEnergy)
  
  if len(system.name) > 0:
    metaData = "%s;name=%s" % (metaData, system.name)
  
  fout.write("%s\n" % (metaData))
  for i in range(system.NAtoms):
    
    if not system.vacancyType[i]:
    
      fout.write("%s %.10f %.10f %.10f %.2f\n" % (system.specieList[system.specie[i]], 
        system.pos[3*i], system.pos[3*i+1], system.pos[3*i+2], system.charge[i]))
  
  fout.close()
  
  return success, error
