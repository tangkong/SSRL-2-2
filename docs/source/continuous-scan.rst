Continuous Scan XAS
===================

Continuous scanning XAS operates differently from standard scanning paradigms.  
In order to collect data more quickly, motors and monochromator are moved 
continuously.  Data collection is rapid enough that we must record data in batches, 
rather than at every measurement instance.  At SSRL XAS beamlines, this 
orchestration is managed by an FPGA box running EPICS.  We instruct the FPGA box 
to initiate a scan via channel access, and read the `.DATA` PV it emits.  

Data Schema
-----------
For speed considerations, the `.DATA` PV contains all measurement information in 
one contiguous array that must be parsed before recording.  The formatting of 
this array depends on how the FPGA box is configured.  