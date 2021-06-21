# SSRL beamline 2-2 startup scripts
[Documentation](https://tangkong.github.io/SSRL-2-2/)

Template for beamline Bluesky collection profile. To use, clone this repository and make modifications as necessary

## Installation Instructions
### Customize bash
Copy contents of /bin into user's /bin or ~/.bashrc file.  THis will set the ipython profile to auto-run bluesky and the associated configuration files included in this repo

### Load ipython profiles
Copy all folders into ~/.ipython 

### Customization of profile
TO-DO: Customize bits in user

Much of these scripts have been adapted from various other beamline configurations, including [APS-USAXS](https://github.com/APS-USAXS), [NSLS-II CMS](https://github.com/NSLS-II-CMS), and [NSLS-II CSX](https://github.com/NSLS-II-CSX)

# Ipython Profile Organization

```
./profile_bluesky/startup/
.
├── profile_bluesky
│   └── startup
│       ├── 00-instrument.py
│       ├── instrument
│       │   ├── callbacks
│       │   ├── devices
│       │   ├── framework
│       │   ├── mpl
│       │   ├── plans
│       │   ├── __init__.py
│       │   ├── collection.py
│       │   └── session_logs.py 
```
The data collection profile is organized like a python package, with devices and 
plans imported on startup.  For convenience, these modules have been separated 
into folders.  

## `framework`: Bluesky and Databroker framework
These files set up the Bluesky `RunEngine`, which is responsible for orchestrating
data collection.  This `RunEngine` is then connected to the relevant database 
through `databroker`, allowing for data and metadata to be recorded with each run.
Basic metadata is set up.  

## `devices`: Ophyd objects for beamline devices
These files set up the `ophyd` objects representing the devices relevant to the 
beamline in question (detectors, motors, etc).  `ophyd` objects connect to 
EPICS PV's and use them to configure a device.  

## `plans`: Experimental plans
These files define experimental plans building off Bluesky's extensive library of 
plans and stub plans. Files in this folder will likely require the import of 
either devices or RunEngine components from other folders. 

## `callbacks`: Automatic processing
These files are used to set up prompt export or processing of files.  