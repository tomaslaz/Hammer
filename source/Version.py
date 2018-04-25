#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
A module to get the version of the project from git.

@author Tomas Lazauskas, 2016-2018
@web lazauskas.net
@email tomas.lazauskas[a]gmail.com
"""

from __future__ import print_function

import os
import subprocess

_versionFile = os.path.join(os.path.dirname(__file__), "version.info")

def getAuthor():
  """
  Returns the name of the author
  
  """
  
  return "Tomas Lazauskas"

def getGitVersion():
  """
  Attempt to determine the version from git.
  
  """
  
  cwd = os.getcwd()
  
  dn = os.path.dirname(__file__)
  if dn:
    os.chdir(dn)
  
  # get current version
  try:
    command = "git describe"
    proc = subprocess.Popen(command, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    stdout, stderr = proc.communicate()
    
    status = proc.poll()
    if status:
      version = None
      
    else:
      version = stdout.decode("utf-8").strip().split("-")[0]
  
  finally:
    os.chdir(cwd)
  
  return version

def getGitVersionDate(versionIn=None):
  """
  Attempt to determine the date of the version from git
  
  """
  
  if not versionIn:
    version = getGitVersion()
  else:
    version = versionIn
  
  cwd = os.getcwd()
  
  dn = os.path.dirname(__file__)
  if dn:
    os.chdir(dn)
  
  if version:
    try:
      command = "git log -1 --format=%ai " + version
      proc = subprocess.Popen(command, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
      stdout, stderr = proc.communicate()
      
      status = proc.poll()
      if status:
        versionDate = None
      else:
        versionDate = stdout.decode("utf-8").strip().split(" ")[0]
        
    finally:
      os.chdir(cwd)
      
  else:
    versionDate = None
  
  return versionDate

def getName():
  """
  Returns the name of the software
  
  """
  
  return "Hammer"

def getVersion():
  """
  Tries to determine the version. First from git, if not successful, form the version file
  
  """
  
  version = getGitVersion()
  
  if version:
    versionDate = getGitVersionDate(version)
    
    writeVersion(version, versionDate)
  
  else:
    version, versionDate = readVersion()
  
  if version == None:
    version = "unknown"
  if versionDate == None:
    versionDate = "unknown"
  
  return version, versionDate

def getWeb():
  """
  Returns the web address for the project
  
  """
  
  return "www.lazauskas.net/hammer"
  
def printVersionAuthor():
  """
  Prints the version and the author of the project
  """
  
  version, date = getVersion()
  
  print ("")
  print ("")
  print ("%s v.%s (%s)" % (getName(), version, date))
  print ("Author: %s" % (getAuthor()))
  print ("")
  print ("")

def readVersion():
  """
  Reads the version from the version file
  
  """
  
  version = None
  versionDate = None
  
  try:
    f = open(_versionFile)
  except:
    print ("Cannot read file %s" % (_versionFile))
    return version, versionDate
  
  try:
    version = f.readline().strip()
  except:
    print ("Cannot read version from file %s" % (_versionFile))
    return version, versionDate
  
  try:
    versionDate = f.readline().strip()
  except:
    print ("Cannot read date of the version from file %s" % (_versionFile))
    return version, versionDate
  
  f.close()
  
  return version, versionDate

def writeVersion(version, date):
  """
  Writes version into the version file
  
  """
  
  if version and date:
    
    cwd = os.getcwd()
  
    dn = os.path.dirname(__file__)
    if dn:
      os.chdir(dn)
    
    try:
      f = open(_versionFile, "w")
    except:
      print ("Cannot open: %s" % (_versionFile))
      
      os.chdir(cwd)
      return
    
    f.write("%s\n" % version)
    f.write("%s\n" % date)
        
    f.close()
    
    os.chdir(cwd)
    
if __name__ == "__main__":
  
  _, _ = getVersion()