import threading 
import logging
import time
from pathlib import Path
import ctypes

import numpy as np
import pandas as pd

from bluesky.plans import fly, count
from bluesky.preprocessors import fly_during_decorator

import ophyd
from ophyd import Device
from ophyd import Component as Cpt
from ophyd.signal import EpicsSignal, Signal
from ophyd.sim import det
from ophyd.flyers import FlyerInterface

from .misc_devices import CXASEpicsMotor
from .xspress3 import xsp3

logger = logging.getLogger()

__all__ = ['flyer']

so_eval_path = Path(__file__).parent / 'fpga_eval' / 'omFpgaEval.so'
fpga_eval_lib = ctypes.cdll.LoadLibrary(so_eval_path)

# C# helper functions to decode PV
class FpgaFrameInfo(ctypes.Structure):
    _fields_ =    [ ("lenData",     ctypes.c_uint),
                    ("data",        ctypes.POINTER(ctypes.c_int)),

                    ("self.num_frames",   ctypes.POINTER(ctypes.c_uint)),
                    
                    ("numAdc",      ctypes.POINTER(ctypes.c_uint)),
                    ("numCounter",  ctypes.POINTER(ctypes.c_uint)),
                    ("numEncoder",  ctypes.POINTER(ctypes.c_uint)),
                    ("numMotor",    ctypes.POINTER(ctypes.c_uint)),
                    
                    ("lastErrorCode", ctypes.POINTER(ctypes.c_uint))]
         
class FpgaFrameData(ctypes.Structure):
    _fields_ =    [ ("lenData",     ctypes.c_uint),
                    ("data",        ctypes.POINTER(ctypes.c_int)),

                    ("self.num_frames",   ctypes.POINTER(ctypes.c_uint)),
                    
                    ("numAdc",      ctypes.POINTER(ctypes.c_uint)),
                    ("numCounter",  ctypes.POINTER(ctypes.c_uint)),
                    ("numEncoder",  ctypes.POINTER(ctypes.c_uint)),
                    ("numMotor",    ctypes.POINTER(ctypes.c_uint)),

                    ("adc",         ctypes.POINTER(ctypes.c_uint)),
                    ("counter",     ctypes.POINTER(ctypes.c_uint)),
                    ("motor",       ctypes.POINTER(ctypes.c_uint)),    
                    ("encoder",     ctypes.POINTER(ctypes.c_uint)),

                    ("gate",        ctypes.POINTER(ctypes.c_uint)),
                    ("time",        ctypes.POINTER(ctypes.c_uint)),
                    
                    ("lastErrorCode", ctypes.POINTER(ctypes.c_uint))]

so_motion_path = Path(__file__).parent / 'fpga_motion' / 'motion.so'
fpga_motion_lib = ctypes.cdll.LoadLibrary(so_motion_path)

class FpgaTrigger(ctypes.Structure):
    _fields_ = [    
                    ("time",            ctypes.POINTER(ctypes.c_double)),
                    ("energy",            ctypes.POINTER(ctypes.c_double)),
                    ("timeEnergyLen",    ctypes.c_uint),
                    
                    ("trigger",            ctypes.POINTER(ctypes.c_double)),                    
                    ("triggerLen",        ctypes.POINTER(ctypes.c_uint)),
                    
                    ("lastErrorCode",    ctypes.POINTER(ctypes.c_int))]
                    
class FpgaMotion(ctypes.Structure):
    _fields_ = [    ("time",            ctypes.POINTER(ctypes.c_double)),
                    ("energy",            ctypes.POINTER(ctypes.c_double)),
                    ("timeEnergyLen",    ctypes.c_uint),
                    
                    ("crystalD",        ctypes.c_double),
                    ("crystalGap",        ctypes.c_double),
                    ("motorResPhi",        ctypes.c_double),
                    ("motorResZ",        ctypes.c_double),
                                        
                    ("motionPhi",        ctypes.POINTER(ctypes.c_double)),
                    ("motionPhiLen",    ctypes.POINTER(ctypes.c_uint)),
                    
                    ("motionZ",            ctypes.POINTER(ctypes.c_double)),
                    ("motionZLen",        ctypes.POINTER(ctypes.c_uint)),
                    
                    ("lastErrorCode",    ctypes.POINTER(ctypes.c_int))]


# Based off of implementations by: 
# https://blueskyproject.io/tutorials/Flyer%20Basics.html
# https://github.com/NSLS-II/sirepo-bluesky/blob/7173258e7570904295bfcd93d5bca3dcc304c15c/sirepo_bluesky/sirepo_flyer.py
# https://github.com/thomascobb/bluefly/blob/0ee7ea837d5f74e3cdc69e2315e9beed28dd7766/bluefly/fly.py#L36

class FPGABox(Device):
    """
    Device to be subclassed for fpga continuous scan
    Contains the relevant PV's for the FPGA continuous scan box
    """ 
    # signals to interact with
    data = Cpt(EpicsSignal, '.DATA')
    trigger_signal = Cpt(EpicsSignal, '.TRIG')

    # configuration signals
    trigger_profile_list = Cpt(EpicsSignal, '.TLST')
    trigger_width = Cpt(EpicsSignal, '.TWID')
    trigger_base_rate = Cpt(EpicsSignal, '.TBRT')
    trigger_source = Cpt(EpicsSignal, '.TSRC')

    dout1_type = Cpt(EpicsSignal, '.OTP1')
    dout1_control = Cpt(EpicsSignal, '.DO1') 

    dout1_width = Cpt(EpicsSignal, '.OWD1')

    phi = Cpt(CXASEpicsMotor, ':MOTOR1') # mono
    z1 = Cpt(CXASEpicsMotor, ':MOTOR3') # should be synced with z2
    z2 = Cpt(CXASEpicsMotor, ':MOTOR4')

class CXASFlyer(FPGABox, FlyerInterface):
    """CXASFlyer continuous x-ray spectroscopy flyer device
    Here lies jank, reader beware.

    flyer = CXASFlyer('BL22:SCAN:MASTER', name='flyer')
    """

    use_x3 = Cpt(Signal, value=0, doc='Enabling x3 in this flyer')
    x3 = xsp3
    def __init__(self, prefix, *, config_attrs=None, read_attrs=None, **kwargs):
        
        # Make status objects accessible by all methods
        self.kickoff_status = None
        self.complete_status = None
        self.t0 = time.time()
        self.last_update_time = None
        self.traj_file_path=Path(__file__).parent / 'fpga_motion' / 'Co_XANES_2kpts.tra'

        self.buffer_dict = []

        super().__init__(prefix, **kwargs) 
            # config attrs kinda broken at the moment?  Disabling works
                            #configuration_attrs=config_attrs, read_attrs=read_attrs, **kwargs)

    def kickoff(self):
        logger.info("kickoff()")
        self.kickoff_status = ophyd.DeviceStatus(self)
        self.complete_status = ophyd.DeviceStatus(self)
        
        self._info_update() # read config PV's, initialize frames

        # initialize data format for describe_collect(), collect()
        self.buffer_dict = [] # will store event dictionaries

        self._setup_describe_collect() # given info dataframe
        
        # Don't block RunEngine thread, construct a different one
        thread = threading.Thread(target=self.my_activity, daemon=True)
        thread.start()

        return self.kickoff_status

    def my_activity(self):
        """ Main activity """
        logger.info('activity()')
        if self.complete_status is None: 
            # I assume if activity gets called before kickoff initializes complete_status
            logger.info('leaving activity() - not complete')
            return

        # Kickoff activity here. Set up activity that runs when PV's update
        # set up fly scan configuration.  Eventually record as stage_sigs
        self.stage_sigs[self.trigger_source] = 3

        # set up stage sigs
        self.stage_sigs[self.phi.spmg] = 2 # set motors to synchronize
        #self.stage_sigs[self.z1.spmg] = 2 # set motors to synchronize
        #self.stage_sigs[self.z2.spmg] = 2 # set motors to synchronize
        # ...

        self.trigger_ctr = 0

        if self.use_x3.get():
            self.stage_sigs[self.dout1_type] = 0
            self.stage_sigs[self.dout1_control] = 4
            self.stage_sigs[self.dout1_width] = 8 # ms,  probably not the right setting for all
            # need to make sure this time fits between triggers
            # TO-DO: Set this dynamically based on trajectory list?

        # apply stage sigs to self and components (x3)
        self.stage()
        
        self.load_trajectory()
        if self.use_x3.get():
            self.x3.total_points.put(self.trigger_len) 
            self.x3.stage()
            self.x3.prep_asset_docs() # generate all asset documents
            self.frame_ctr = 0

            # once we're set up, ready x3 to receive trigger signals
            # Normally don't begin acquisition through stage sigs, 
            # but triggering here is dictated by FPGA externally
            self.x3.settings.acquire.put(1)
            #self.stage_sigs[self.x3.hdf5.capture] = 1 


        # sub before to make sure we don't miss any data?
        self.data.subscribe(self._data_update)
        self.trigger_signal.put(2)
        # for some reason, callback fires once sub'd, so place after
        self.trigger_signal.subscribe(self._trigger_changed) 

        # once started, notify by updating status object
        self.kickoff_status._finished(success=True)

        # Wait for completion, leave this to the _trigger_changed method

    def complete(self):
        logger.info('complete()')
        if self.complete_status is None:
            raise RuntimeError("No collection is in progress")

        return self.complete_status

    def describe_collect(self):
        """
        Describe details for ``collect()`` method
        """
        logger.info("describe_collect()")
        return self.desc

    def collect(self):
        """
        Start this Flyer
        """
        logger.info("collect()")
        # yield dictionary to bluesky
        # clear data dictionary
        d = self.buffer_dict
        self.buffer_dict = []
        for subd in d:
            yield subd

    def trigger(self):
        """ trigger: Capture a single frame, write to buffer dict. 
        TO-DO: Determine if inherited trigger behavior can be used
        """
        self.trigger_signal.put(1) # single trigger
        self._data_update()
        
    def read(self):
        """read: overwrite ophyd.device.read for this specific flyer
        """
        if len(self.buffer_dict) < 1:
            self._data_update()
        
        curr_frame = self.buffer_dict[-1]

        results = {}
        for k in curr_frame['data'].keys():
            results[k] = {'value': curr_frame['data'][k],
                           'timestamp': curr_frame['timestamps'][k] }

    def stage(self):
        """ stage: initialize variables?  Record resting config PV's? 
        TO-DO: Figure out what configuration is needed?
        TO-DO: Differentiate between fly scan and step scan config?  Maybe this 
                is only for step scan?
        """
        ret = super().stage()
        return ret 

    def unstage(self):
        """ unstage: return configuration to resting state
        TO-DO: Determine what resting state is
        turn off x3 collection, h5 plugin
        move motors back to original location
        Will undo stage_sigs in reverse order 
        """
        ret = super().unstage()
        return ret

    def _setup_describe_collect(self):
        """ set up data schema  """
        # currently only single stream
        d = dict(
            source = self.data.pvname,
            dtype = 'number', 
            shape = []
        )
       
        # construct the schema
        dd = {}
        dd.update({'cycletime':d})
        dd.update({'gate':d})
        dd.update({f'motor_{i}':d for i in range(self.num_motor.item())})
        dd.update({f'adc_{i}':d for i in range(self.num_adc.item())})
        dd.update({f'encoder_{i}':d for i in range(self.num_encoder.item())})
        dd.update({f'counter_{i}':d for i in range(self.num_counter.item())})
        
        if self.use_x3.get():
            dmca = dict(
                    source = 'xsp3',
                    dtype = 'array', 
                    shape = [-1, -1],
                    external= 'FILESTORE:'
                    )
            dd.update({'mca_0': dmca})
            dd.update({'mca_1': dmca})


        self.desc = {self.name: dd}

    def _trigger_changed(self, value=None, old_value=None, **kwargs):
        "This is called when the 'trigger_signal' changes."
        logger.info(f'_trigger_changed(), {old_value}->{value}')
        if self.complete_status is None:
            return
        if old_value > value: #(old_value == 1 or 2) and (value == 0):
            # Negative-going edge means an acquisition just finished.
            self.complete_status._finished()
            # remove callbacks, could do this in unstage(), but wait to gather more tasks?
            # Also unsure when unstage would be called during a fly scan.
            self.data.unsubscribe_all()
            self.trigger_signal.unsubscribe_all()

            self.unstage()
            if self.use_x3.get():
                self.x3.unstage()
                # stop file writing
                self.x3.settings.acquire.put(0)
                self.x3.hdf5.capture.put(0)

    def _info_update(self):
        # initialize parameters
        self.num_frames         = np.zeros(1, np.uint32)
        self.num_adc            = np.zeros(1, np.uint32)
        self.num_counter        = np.zeros(1, np.uint32)
        self.num_encoder        = np.zeros(1, np.uint32)
        self.num_motor          = np.zeros(1, np.uint32)
        self.last_error_code    = np.zeros(1, np.uint32)

        pv_data = self.data.get() # array of ints

        # get info from the FPGA box and record
        fpgaFrameInfo = FpgaFrameInfo(0,
                                np.ctypeslib.as_ctypes(pv_data),
                                
                                np.ctypeslib.as_ctypes(self.num_frames),
                                
                                np.ctypeslib.as_ctypes(self.num_adc),
                                np.ctypeslib.as_ctypes(self.num_counter),
                                np.ctypeslib.as_ctypes(self.num_encoder),
                                np.ctypeslib.as_ctypes(self.num_motor),
                                # 1 for success
                                np.ctypeslib.as_ctypes(self.last_error_code))

        fpga_eval_lib.GetFpgaFrameInfo.restype = None
        fpga_eval_lib.GetFpgaFrameInfo(ctypes.byref(fpgaFrameInfo)) 

        # initialize data 
        self.adc         = np.zeros(self.num_frames * self.num_adc, np.uint32)
        self.counter     = np.zeros(self.num_frames * self.num_counter, np.uint32)
        self.motor       = np.zeros(self.num_frames * self.num_motor, np.uint32)
        self.encoder     = np.zeros(self.num_frames * self.num_encoder, np.uint32)
        self.gate        = np.zeros(self.num_frames, np.uint32)
        self.time        = np.zeros(self.num_frames, np.uint32)

    def _data_update(self, value=None, timestamp=None, **kwargs):
        """ Update in python buffer with data PV information.  
        Could have frame info change between collections, so be sure to update
        """
        logging.info('_data_update()')
        self._info_update()

        pv_data = self.data.get()

        # parse new frame data
        #print('--init fpgaFrameData')
        fpgaFrameData = FpgaFrameData (	0,
								np.ctypeslib.as_ctypes(pv_data),
								
								np.ctypeslib.as_ctypes(self.num_frames),
								
								np.ctypeslib.as_ctypes(self.num_adc),
								np.ctypeslib.as_ctypes(self.num_counter),
								np.ctypeslib.as_ctypes(self.num_encoder),
								np.ctypeslib.as_ctypes(self.num_motor),
								
								np.ctypeslib.as_ctypes(self.adc),
								np.ctypeslib.as_ctypes(self.counter),
								np.ctypeslib.as_ctypes(self.motor),
								np.ctypeslib.as_ctypes(self.encoder),
								
								np.ctypeslib.as_ctypes(self.gate),
								np.ctypeslib.as_ctypes(self.time),
								
								np.ctypeslib.as_ctypes(self.last_error_code))

        # C function call
        #print('--calling EvalFpgaData')
        fpga_eval_lib.EvalFpgaData.restype = None
        fpga_eval_lib.EvalFpgaData(ctypes.byref(fpgaFrameData))
       
        # if we don't have a new frame
        #print('--checking timestamps')
        if self.last_update_time == self.time[0]:
            return # we don't have a new frame
        else: 
            self.last_update_time = self.time[0] # remember last update time

        # for each frame in self.frame_num, append to buffer
        #print('--setup dictionary')
        for frame in range(self.num_frames.item()):
            self.trigger_ctr +=1
            curr_frame = {}
            curr_frame.update({'cycletime': self.time[frame]})
            curr_frame.update({'gate': self.gate[frame]})
            curr_frame.update({f'adc_{i}': self.adc[frame*self.num_adc.item()+i] 
                                for i in range(self.num_adc.item())})
            curr_frame.update({f'motor_{i}': self.motor[frame*self.num_motor.item()+i] 
                                for i in range(self.num_motor.item())})
            curr_frame.update({f'encoder_{i}': self.encoder[frame*self.num_encoder.item()+i] 
                                  for i in range(self.num_encoder.item())})
            curr_frame.update({f'counter_{i}': self.counter[frame*self.num_counter.item()+i] 
                                for i in range(self.num_counter.item())})

            if self.use_x3.get():
                datums = list(self.x3._datum_ids)
                curr_frame.update({'mca_0': datums[self.frame_ctr]})
                curr_frame.update({'mca_1': datums[self.frame_ctr + 1]})
                
                self.frame_ctr += 2

            t = time.time() 
            time_frame ={}
            for key in curr_frame.keys():
                time_frame.update({key:t})
                
            final_dict = {'time':t,
                          'data':curr_frame,
                          'timestamps':time_frame}
            if self.use_x3.get():
                final_dict.update({'filled' : 
                               {key: False for key in ['mca_0', 'mca_1']} })

            #print('  --append to buffer')
            self.buffer_dict.append(final_dict)

    def collect_asset_docs(self):
        """ default to the asset docs in x3? """
        if self.use_x3.get():
            yield from self.x3.collect_asset_docs()        

    def set_trajectory(self, 
        traj_file_path=Path(__file__).parent / 'fpga_motion' / 'Cu_XANES.tra'):
        self.traj_file_path = traj_file_path

    def load_trajectory(self):
        
        traData = pd.read_csv(  self.traj_file_path,
                                sep='\t',
                                skiprows=6,
                                comment='#',
                                usecols=[1,2],
                                names=['sec', 'energy'])

        # hard code, assume positions
        header = []
        with open(self.traj_file_path) as traj_file:
            for _ in range(6):
                header.append(traj_file.readline())

        bragg_start            = header[0].split()[1]
        bragg_stop            = header[1].split()[1]
        beam_height_start    = header[2].split()[1]
        beam_height_stop    = header[3].split()[1]
        traj_length            = header[5].split()[1]

        self.time_list = traData['sec'].to_numpy()
        self.energy_list = traData['energy'].to_numpy()

        # initialize variables
        self.trigger_list           = np.zeros(16384, np.float64)
        self.motion_phi_list            = np.zeros(16384, np.float64)
        self.motion_Z_list                = np.zeros(16384, np.float64)
        self.trigger_len            = np.zeros(1, np.uint32)
        self.motion_phi_len        = np.zeros(1, np.uint32)
        self.motion_Z_len            = np.zeros(1, np.uint32)
        last_error_code        = np.zeros(1, np.int32)

        fpgaTrigger = FpgaTrigger(    np.ctypeslib.as_ctypes(self.time_list),
                                    np.ctypeslib.as_ctypes(self.energy_list),
                                    len(self.time_list),
                                    
                                    np.ctypeslib.as_ctypes(self.trigger_list),
                                    np.ctypeslib.as_ctypes(self.trigger_len),
                                    
                                    np.ctypeslib.as_ctypes(last_error_code))
                                    
        # C function call, determine trigger details
        fpga_motion_lib.restype = None
        fpga_motion_lib.CalcTrigger(ctypes.byref(fpgaTrigger))

        fpgaMotion = FpgaMotion(    np.ctypeslib.as_ctypes(self.time_list),
                            np.ctypeslib.as_ctypes(self.energy_list),
                            len(self.time_list),
                            
                            1.9202e-10,        # crystalD        [m]
                            5,                # crystalGap    [mm]
                            50000,            # motorPhiRes:    [counts/EGU]        ### please verify
                            40320,            # motorZRes:    [counts/EGU]        ### please verify
                            
                            np.ctypeslib.as_ctypes(self.motion_phi_list),
                            np.ctypeslib.as_ctypes(self.motion_phi_len),
                            
                            np.ctypeslib.as_ctypes(self.motion_Z_list),
                            np.ctypeslib.as_ctypes(self.motion_Z_len),
                            
                            np.ctypeslib.as_ctypes(last_error_code))

        # C function call, calculate trigger details
        fpga_motion_lib.restype = None
        fpga_motion_lib.CalcMotion(ctypes.byref(fpgaMotion))

        self.trigger_profile_list.put(self.trigger_list)
        self.phi.profile_list.put(self.motion_phi_list)
        #self.z1.profile_list.put(self.motion_Z_list)
        #self.z2.profile_list.put(self.motion_Z_list)

flyer = CXASFlyer('BL93:SCAN:MASTER', name='flyer') #, configuration_attrs=['trigger_width'])

# add configuration attrs
flyer.configuration_attrs.extend(['dout1_width', 'trigger_width', 'trigger_base_rate'])
