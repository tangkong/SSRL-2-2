from ophyd import Device, Component as Cpt, EpicsSignal

import ctypes
from pathlib import Path

import numpy as np
import pandas as pd

dxp_path = Path(__file__).parent / 'dxp_eval' / 'dxp.so'
omDxpLib = ctypes.cdll.LoadLibrary(dxp_path)

class DxpData(ctypes.Structure):
    _fields_ = [    ("lenData",         ctypes.c_uint),
                    ("data",            ctypes.POINTER(ctypes.c_double)),
                    
                    ("numPixel",        ctypes.POINTER(ctypes.c_uint)),
                    
                    ("element",         ctypes.POINTER(ctypes.c_uint)),
                    ("pixel",           ctypes.POINTER(ctypes.c_uint)),
                    
                    ("liveTime",        ctypes.POINTER(ctypes.c_double)),
                    ("realTime",        ctypes.POINTER(ctypes.c_double)),
                    ("icr",             ctypes.POINTER(ctypes.c_double)),
                    ("ocr",             ctypes.POINTER(ctypes.c_double)),
                    
                    ("mcaLen",          ctypes.POINTER(ctypes.c_int)),
                    ("mca",             ctypes.POINTER(ctypes.c_uint)),
                                        
                    ("lastErrorCode",   ctypes.POINTER(ctypes.c_int))]



class Dxp(Device):
    """Dxp portion of 100e detector, for use as component of 100e flyer object.
    Will likely be missing methods like .read() etc.  

    Separating this into modules in order to deal with multiple dxp's 

    dxp1 = Dxp('DXP1:DXP', name='dxp1')
    """

    max_MCA_length = 2048
    num_buffer_pixels = Cpt(EpicsSignal, '.NumBufPix')
    num_map_pixels = Cpt(EpicsSignal, '.NumMapPix')
    start_acquire = Cpt(EpicsSignal, '.StartAcq') # 0:idle, 1:starting, 2:running, 3:error
    is_armed = Cpt(EpicsSignal, '.IsArmed') # bool
    update_dxp = Cpt(EpicsSignal, '.UpdateDxp') # 0:update req, 1:updating, 2:up-to-date, 3:error
    num_detector_elems = Cpt(EpicsSignal, '.NumDetElements')
    first_element = Cpt(EpicsSignal, '.FirstDetElement')
    data = Cpt(EpicsSignal, '.Data') # long, serialized array holding all data

    curr_buff_pixels = None
    curr_num_elems = None
    curr_first_elem = None
    def describe_data(self):
        d = dict(
            source = 'dxp 100E detector',
            dtype = 'number',
            shape = []
        )

        dd = {  'element': d,
                'first_element':d,
                'pixel': d,
                'live_time': d,
                'real_time': d,
                'icr': d,
                'ocr': d,
                'mca_length': d
            } 
        dd.update({
            'mca':{'source': 'dxp 100E detector',
                   'dtype':'array',
                   'shape':[-1, -1]} 
                  })
        
        return dd

    def get_data(self):
        pv_data = self.data.get()
        # try to limit access
        if not self.curr_buff_pixels:
            n_buf_pix = self.num_buffer_pixels.get()
            self.curr_buff_pixels = n_buf_pix
            print(self.curr_buff_pixels)
        else:
            n_buf_pix = self.curr_buff_pixels
        if not self.curr_num_elems:
            n_det_elem = self.num_detector_elems.get()
            self.curr_num_elems = n_det_elem
            print(self.curr_num_elems)
        else:
            n_det_elem = self.curr_num_elems
        if not self.curr_first_elem:
            self.curr_first_elem = self.first_element.get()


        # parse frame data
        numPixel        = np.zeros(1,                      np.uint32)
        element         = np.zeros(n_buf_pix * n_det_elem, np.uint32)
        pixel           = np.zeros(n_buf_pix * n_det_elem, np.uint32)
        liveTime        = np.zeros(n_buf_pix * n_det_elem, np.float64)
        realTime        = np.zeros(n_buf_pix * n_det_elem, np.float64)
        icr             = np.zeros(n_buf_pix * n_det_elem, np.float64)
        ocr             = np.zeros(n_buf_pix * n_det_elem, np.float64)
        mcaLen          = np.zeros(n_buf_pix * n_det_elem, np.int32)
        mca             = np.zeros(n_buf_pix * n_det_elem * self.max_MCA_length, 
                                                           np.uint32)
        lastErrorCode   = np.zeros(1, np.int32)

        dxp_data = DxpData( 0,
                            np.ctypeslib.as_ctypes(pv_data),
                            np.ctypeslib.as_ctypes(numPixel),
                            np.ctypeslib.as_ctypes(element),
                            np.ctypeslib.as_ctypes(pixel),
                            np.ctypeslib.as_ctypes(liveTime),
                            np.ctypeslib.as_ctypes(realTime),
                            np.ctypeslib.as_ctypes(icr),
                            np.ctypeslib.as_ctypes(ocr),
                            np.ctypeslib.as_ctypes(mcaLen),
                            np.ctypeslib.as_ctypes(mca),
                            np.ctypeslib.as_ctypes(lastErrorCode))
                            
        # C function call                    
        omDxpLib.EvalDxpData.restype = None
        omDxpLib.EvalDxpData(ctypes.byref(dxp_data))

        # construct dataframe
        frame_dicts= []
        for i in range( int(n_buf_pix * n_det_elem) ):
            d = {
                  'element': element[i],
                  'first_element': self.curr_first_elem,
                  'pixel': pixel[i],
                  'live_time': liveTime[i],
                  'real_time': realTime[i],
                  'icr': icr[i],
                  'ocr': ocr[i],
                  'mca_length': mcaLen[i],
                  'mca': list(mca[i*self.max_MCA_length:(i+1)*self.max_MCA_length])
                }

            frame_dicts.append(d)

        # return a list of dictionaries suitable for collect()

        print(self.name + '_get_data: ' + str(np.max(pixel)))
        return frame_dicts 
