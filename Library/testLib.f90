subroutine aims(mpi_comm_input, in_unit, mpi_switch)          ! byref(s), byval(length) [long int, implicit]
    USE MPI
    IMPLICIT NONE

    integer, intent(in) :: mpi_comm_input
    integer,intent(in) :: in_unit
    logical, intent(in) :: mpi_switch

    integer :: commRank, commSize, commIerr

    CALL MPI_Comm_size(mpi_comm_input, commSize, commIerr)
    CALL MPI_Comm_rank(mpi_comm_input, commRank, commIerr)

    CALL SLEEP(1)

    print *, 'Hello, World! I am a process ', commRank, 'of ', commSize, '.'

    !if (mpi_switch > 0) THEN
    write(UNIT=in_unit, FMT=*) mpi_comm_input
    write(UNIT=in_unit, FMT=*) mpi_switch

end subroutine aims
