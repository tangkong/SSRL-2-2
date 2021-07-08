=======
Devices
=======
For continuous scanning X-ray spectroscopy, all equipment talks directly to a 
central control system in the form of a "continuous scan box".  While this simpifies operations, 
it also hides underlying sub-devices from view.    This is necessary to enable 
the acquisition speed and high data throughput that continuous scanning requires.  
This section will attempt to walk a middle-ground, conveying enough information 
to enable operation while not confusing the user.   


Continuous Scan Acquisiton System (CS box)
==========================================
Communication to the continuous scan box is made possible via EPICS and channel access.  
An IOC housed on the CS box connects to the monochromator, table motors, ion 
gauges, and external trigger ports (to name a few).  

Table motors: ``flyer.vert1``, ``flyer.vert2``
----------------------------------------------

Xspress3 Fluorescence Detector: ``flyer.x3``
--------------------------------------------
When The Xspress3 detector writes .h5 files on each acquisition.  Both the full 
multi-channel arrays (MCA's) and integrated ROI values are accessible via PV 
access, and can be inspected directly on the python interpreter.  Normally
ROI ranges should be adjusted from the EDM display. 

.. code:: ipython

    In [1]: xsp3.channel1.rois.roi01.read()
    Out[1]:
    OrderedDict([('xsp3_channel1_rois_roi01_value',
                {'value': 0.0, 'timestamp': 1598804648.400984})])


Taking single measurements via ``bp.count`` is valid.

.. code:: ipython

    In [1]: RE(bp.count([xsp3]))

If taking multiple acquisitions in one run, we must make sure the ``xsp3.total_points``
variable matches the number of acquisitions to be taken.  This ensures that all MCA's 
in one run will be placed in a single h5 file.  Bluesky and Databroker assume 
this behavior when accessing saved data.  **We have done our best to create plans 
that cover this use case**, but if needed this value can be adjusted manually.

.. code:: ipython

    In [1]: RE(bps.mv(xsp3.total_points, 5))

    In [2]: RE(bp.scan([xsp3], motor, -1, 1, 5))

    Transient Scan ID: 2     Time: 2020-09-02 09:57:51
    Persistent Unique Scan ID: 'f0c7917f-f8bf-4d00-88a6-a9383f0920bb'
    New stream: 'primary'
    +-----------+------------+------------+
    |   seq_num |       time |      motor |
    +-----------+------------+------------+
    |         1 | 09:57:53.2 |     -1.000 |
    |         2 | 09:57:54.5 |     -0.500 |
    |         3 | 09:57:55.6 |      0.000 |
    |         4 | 09:57:56.6 |      0.500 |
    |         5 | 09:57:57.7 |      1.000 |
    +-----------+------------+------------+
    generator scan ['f0c7917f'] (scan num: 2)

    In [3]: db[-1].table(fill=True)
    Out[5]:
                                    time  ...                                      xsp3_channel2
    seq_num                                ...
    1       2020-09-02 16:57:53.278821945  ...  [0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, ...
    2       2020-09-02 16:57:54.541794538  ...  [0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, ...
    3       2020-09-02 16:57:55.604745626  ...  [0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, ...
    4       2020-09-02 16:57:56.668115139  ...  [0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, ...
    5       2020-09-02 16:57:57.731433153  ...  [0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, ...

    [5 rows x 11 columns]


Motors
======

Sample Stage: ``s_stage``
-------------------------

``s_stage`` has the following components, used to control the sample setup.  
These can be accessed either from the parent ``s_stage`` object or for 
convenience by their individual names (``px``, ``py``, etc)

=================================== ======================= ==================
Component name                      Motor name              Units
=================================== ======================= ==================
``px``                              Plate x                 mm
``py``                              Plate y                 mm
``pz``                              Plate z                 mm
``vx``                              Vert x                  steps
``vy``                              Vert x                  steps
=================================== ======================= ==================

.. code:: ipython

    In [1]: RE( bps.mv(s_stage.px, 0) ) # move stage plate x to 0

    In [2]: RE( bps.mvr(pz, -1) ) # move stage height -1 from current position

    In [3]: %movr pz -1 # Same as above, move relative stage height by -1 
