import threading 
import logging
import time
from pathlib import Path
import ctypes

import numpy as np

from bluesky.plans import fly, count
from bluesky.preprocessors import fly_during_decorator

import ophyd
from ophyd import Device
from ophyd import Component as Cpt
from ophyd.signal import EpicsSignal
from ophyd.sim import det
from ophyd.flyers import FlyerInterface

logger = logging.getLogger()

so_path = Path.cwd() / 'fpga_eval' / 'omFpgaEval.so'
fpga_eval_lib = ctypes.cdll.LoadLibrary(so_path)

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

# Based off of implementations by: 
# https://blueskyproject.io/tutorials/Flyer%20Basics.html
# https://github.com/NSLS-II/sirepo-bluesky/blob/7173258e7570904295bfcd93d5bca3dcc304c15c/sirepo_bluesky/sirepo_flyer.py
# https://github.com/thomascobb/bluefly/blob/0ee7ea837d5f74e3cdc69e2315e9beed28dd7766/bluefly/fly.py#L36

class FPGABox(Device):
    """
    Device to be subclassed, contains the relevant PV's for the FPGA continuous scan box
    """ 
    # signals to interact with
    data = Cpt(EpicsSignal, '.DATA')
    trigger_signal = Cpt(EpicsSignal, '.TRIG')

    # configuration signals
    trigger_width = Cpt(EpicsSignal, '.TWID')
    trigger_base_rate = Cpt(EpicsSignal, '.TBRT')

class CXASFlyer(FPGABox, FlyerInterface):
    """CXASFlyer continuous x-ray spectroscopy flyer device
    Here lies jank, reader beware.

    flyer = CXASFlyer('BL22:SCAN:MASTER', name='flyer')
    """
    def __init__(self, prefix, *, config_attrs=None, read_attrs=None, **kwargs):
        
        # Make status objects accessible by all methods
        self.kickoff_status = None
        self.complete_status = None
        self.t0 = time.time()
        self.last_update_time = None
        #self.trig = EpicsSignal('BL22:SCAN:MASTER.TRIG', name='trigger')
        #self.data = EpicsSignal('BL22:SCAN:MASTER.DATA', name='data')

        # TO-DO: configuration PV's to keep track of, for derived data
        if config_attrs is None:
            config_attrs = ['trigger_width', 'trigger_base_rate']
        if read_attrs is None: 
            read_attrs = []
        super().__init__(prefix, **kwargs) # config attrs kinda broken at the moment?  Disabling works
                            #read_attrs=read_attrs, **kwargs)

    def kickoff(self):
        logger.info("kickoff()")
        print('kickoff()')
        self.kickoff_status = ophyd.DeviceStatus(self)
        self.complete_status = ophyd.DeviceStatus(self)

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
        print('k', self.time)
        print('k', self.num_frames)

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
        self.trigger_signal.subscribe(self._trigger_changed) 
        self.data.subscribe(self._data_update)

        self.trigger_signal.put(2) # enable continuous scanning
        # once started, notify by updating status object
        self.kickoff_status._finished(success=True)

        # Wait for completion, leave this to the _trigger_changed method

    def _trigger_changed(self, value=None, old_value=None, **kwargs):
        "This is called when the 'trigger_signal' changes."
        if self.complete_status is None:
            return
        if old_value > value: #(old_value == 1 or 2) and (value == 0):
            # Negative-going edge means an acquisition just finished.
            self.complete_status._finished()
            self.complete_status = None # wrap up for next run
    
    def _data_update(self, value=None, timestamp=None, **kwargs):
        logging.info('_data_update()')
        print('_data_update()')
        pv_data = self.data.get()
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
            curr_frame = {}
            curr_frame.update({'time': self.time[frame]})
            curr_frame.update({'gate': self.gate[frame]})
            curr_frame.update({f'adc_{i}': self.adc[frame+i] 
                                for i in range(self.num_adc.item())})
            curr_frame.update({f'motor_{i}': self.motor[frame+i] 
                                for i in range(self.num_motor.item())})
            curr_frame.update({f'encoder_{i}': self.encoder[frame+i] 
                                  for i in range(self.num_encoder.item())})
            curr_frame.update({f'counter_{i}': self.counter[frame+i] 
                                for i in range(self.num_counter.item())})

            t = time.time() 
            time_frame ={}
            for key in curr_frame.keys():
                time_frame.update({key:t})
            #print('  --append to buffer')
            self.buffer_dict.append({'time':t,
                                    'data':curr_frame,
                                    'timestamps':time_frame})

    def complete(self):
        logger.info('complete()')
        if self.complete_status is None:
            raise RuntimeError("No collection is in progress")

        return self.complete_status

    def _setup_describe_collect(self):
        """ set up data schema  """
        # currently only single stream
        d = dict(
            source = self.data.pvname,
            dtype = 'number', 
            shape = []
        )
        
        
        self.desc = {self.name:   # hard code for now to check
                        dict(
                            time=d, 
                            gate=d,
                            motor_0=d,
                            motor_1=d,
                            motor_2=d,
                            motor_3=d,
                            adc_0=d,
                            adc_1=d,
                            adc_2=d,
                            adc_3=d,
                            adc_4=d,
                            adc_5=d,
                            adc_6=d,
                            adc_7=d,
                            encoder_0=d,
                            encoder_1=d,
                            encoder_2=d,
                            encoder_3=d,
                            )
                    }

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
            
import bluesky.plan_stubs as bps

def fly_plan(flyer, *, md=None):
    """
    Perform a fly scan with one or more 'flyers'.
    Slight modification to bluesky.plans.fly, takes only single flyer

    Parameters
    ----------
    flyers : collection
        objects that support the flyer interface
    md : dict, optional
        metadata

    Yields
    ------
    msg : Msg
        'kickoff', 'wait', 'complete, 'wait', 'collect' messages

    See Also
    --------
    :func:`bluesky.preprocessors.fly_during_wrapper`
    :func:`bluesky.preprocessors.fly_during_decorator`
    """
    uid = yield from bps.open_run(md)
    
    yield from bps.kickoff(flyer, wait=True)
    complete_status = yield from bps.complete(flyer, wait=False)
    while not complete_status.done:
        yield from bps.sleep(0.1) # rate limit @ 40Hz
        yield from bps.collect(flyer)

    yield from bps.close_run()
    return uid


flyer = CXASFlyer('BL22:SCAN:MASTER', name='flyer') #, configuration_attrs=['trigger_width'])
