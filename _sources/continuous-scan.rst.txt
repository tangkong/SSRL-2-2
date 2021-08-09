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
this array depends on how the FPGA box is configured, but often many frames are 
saved and emitted with each update of the `.DATA` PV. 

"Raw" data is composed of timestamps, gates, encoders, ADCs, counters.  Given 
some configuration information, these values can be converted to meaningful data. 


Data collection
---------------

High level flow:
Kickoff, collect (collect_asset_docs), complete?

- Collection involves parsing the .DATA PV, which for speed purposes is an unformatted byte string. This is done by communicating with a compiled c module
- 

Detailed Flow:
Home motors, arm motors, load trajectory, configure external triggers (X3), 

