# Makefile for a dummy dynamic shared FORTRAN library to check weather mpi4py can pass communicator and a filehandler
#   as for FHI-aims interface
# author: Tomas Lazauskas, 2016
# web:    www.lazauskas.net/hammer
# email:  tomas.lazauskas[a]gmail.com
# mpifort -dynamiclib -fPIC -o testLib.so testLib.f90

MF=Makefile
FC=mpifort
FFLAGS=-dynamiclib -fPIC
LFLAGS=$(FFLAGS)
SOURCE=testLib.f90

EXECUTABLE=testLib

.SUFFIXES:
.SUFFIXES: .f90 .so

OBJECT=$(SOURCE:.f90=.o)

.f90.o:
	$(FC) $(FFLAGS) -c $<

$(EXECUTABLE): $(OBJECT) 
	$(FC) $(LFLAGS) -o $@ $(OBJECT)

$(OBJ): $(MF)

clean:
	rm -f $(OBJECT) $(EXECUTABLE) core