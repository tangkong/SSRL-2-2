from epics import caget, caput
import ctypes
import numpy as np
import pandas as pd

omFpgaMotionTriggerLib = ctypes.cdll.LoadLibrary("/home/b_spec/omueller/FpgaMotion/motion.so")

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
                    

                    
#-------------------------------------------------                    
# read the trajectory file
#traName = "Fe_EXAFS.tra"
traName = "Cu_XANES.tra"
traPath = "/home/b_spec/omueller/FpgaMotion/" + traName
traFile = open(traPath, "r")

traData = pd.read_csv(    traPath,
                        sep='\t',
                        skiprows=6,
                        comment='#',
                        usecols=[1,2],
                        names=['sec', 'energy'])

# hard code, assume positions
header = []
for _ in range(6):
    header.append(traFile.readline())

bragg_start            = header[0].split()[1]
bragg_stop            = header[1].split()[1]
beam_height_start    = header[2].split()[1]
beam_height_stop    = header[3].split()[1]
traj_length            = header[5].split()[1]

print('trajectory: ', traPath)
print('phi_start: ', bragg_start)
print('z_start: ', beam_height_start)
print('len: ', traj_length)


# can access pandas DataFrame columns as np array
time = traData['sec'].to_numpy()
energy = traData['energy'].to_numpy()
#-------------------------------------------------                
                    
                    
                    
                    
                    
# initialize variables
trigger                = np.zeros(16384, np.float64)
motionPhi            = np.zeros(16384, np.float64)
motionZ                = np.zeros(16384, np.float64)
triggerLen            = np.zeros(1, np.uint32)
motionPhiLen        = np.zeros(1, np.uint32)
motionZLen            = np.zeros(1, np.uint32)
lastErrorCode        = np.zeros(1, np.int32)

fpgaTrigger = FpgaTrigger(    np.ctypeslib.as_ctypes(time),
                            np.ctypeslib.as_ctypes(energy),
                            len(time),
                            
                            np.ctypeslib.as_ctypes(trigger),
                            np.ctypeslib.as_ctypes(triggerLen),
                            
                            np.ctypeslib.as_ctypes(lastErrorCode))
                            
# C function call
omFpgaMotionTriggerLib.restype = None
omFpgaMotionTriggerLib.CalcTrigger(ctypes.byref(fpgaTrigger))


# print some results
print("--- FpgaMotionTrigger ---")
print("error:\t\t", lastErrorCode[0])                        # < 0 on error, 1 on success
print("triggerLen:\t", triggerLen[0])



fpgaMotion = FpgaMotion(    np.ctypeslib.as_ctypes(time),
                            np.ctypeslib.as_ctypes(energy),
                            len(time),
                            
                            1.9202e-10,        # crystalD        [m]
                            5,                # crystalGap    [mm]
                            100000,            # motorPhiRes:    [counts/EGU]        ### please verify
                            40320,            # motorZRes:    [counts/EGU]        ### please verify
                            
                            np.ctypeslib.as_ctypes(motionPhi),
                            np.ctypeslib.as_ctypes(motionPhiLen),
                            
                            np.ctypeslib.as_ctypes(motionZ),
                            np.ctypeslib.as_ctypes(motionZLen),
                            
                            np.ctypeslib.as_ctypes(lastErrorCode))

# C function call
omFpgaMotionTriggerLib.restype = None
omFpgaMotionTriggerLib.CalcMotion(ctypes.byref(fpgaMotion))

# print some results
print("--- FpgaMotionTrigger ---")
print("error:\t\t", lastErrorCode[0])                        # < 0 on error, 1 on success
print("motionPhiLen:\t", motionPhiLen[0])
print("motionZLen:\t", motionZLen[0])

caput('BL22:SCAN:MASTER.TLST',            trigger)            # upload trigger
caput('BL22:SCAN:MASTER:MOTOR1.PLST',    motionPhi)            # upload motionPhi
caput('BL22:SCAN:MASTER:MOTOR3.PLST',    motionZ)            # upload motionZ
caput('BL22:SCAN:MASTER:MOTOR4.PLST',    motionZ)            # upload motionZ

print("-------------------------")
print('CTME:\t\t', caget('BL22:SCAN:MASTER.TTME'))                # check trigger time
print('M1.TMOV:\t', caget('BL22:SCAN:MASTER:MOTOR1.TMOV'))        # check motor time
print('M3.TMOV:\t', caget('BL22:SCAN:MASTER:MOTOR3.TMOV'))        # check motor time
print('M4.TMOV:\t', caget('BL22:SCAN:MASTER:MOTOR4.TMOV'))        # check motor time
print("-------------------------")


#SPMG
#GO




