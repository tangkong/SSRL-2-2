Debugging Notes
===============
A mess of notes that might help debug less than obvious issues.  

Re-compiling C modules
----------------------

"root map not modified" when loading data from databroker
---------------------------------------------------------
might need to stop file saving.

xspress3 IOC not visible via channel access
-------------------------------------------
unset EPICS_CAS_INTF_ADDR_LIST
start ioc from ssh session to ensure environment is set correctly
