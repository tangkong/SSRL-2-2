from epics import caget, caput
import time
import ctypes
import numpy

omFpgaEvalLib = ctypes.cdll.LoadLibrary("/home/b_spec/omueller/test_epics/omFpgaEval.so")

class FpgaFrameInfo(ctypes.Structure):
	_fields_ =	[	("lenData",		ctypes.c_uint),
					("data",		ctypes.POINTER(ctypes.c_int)),

					("numFrames",	ctypes.POINTER(ctypes.c_uint)),
					
                    ("numAdc", 		ctypes.POINTER(ctypes.c_uint)),
					("numCounter",	ctypes.POINTER(ctypes.c_uint)),
					("numEncoder",	ctypes.POINTER(ctypes.c_uint)),
					("numMotor",	ctypes.POINTER(ctypes.c_uint)),
					
					("lastErrorCode", ctypes.POINTER(ctypes.c_uint))]

					
class FpgaFrameData(ctypes.Structure):
	_fields_ =	[	("lenData",		ctypes.c_uint),
					("data",		ctypes.POINTER(ctypes.c_int)),

					("numFrames",	ctypes.POINTER(ctypes.c_uint)),
					
                    ("numAdc", 		ctypes.POINTER(ctypes.c_uint)),
					("numCounter",	ctypes.POINTER(ctypes.c_uint)),
					("numEncoder",	ctypes.POINTER(ctypes.c_uint)),
					("numMotor",	ctypes.POINTER(ctypes.c_uint)),

					("adc",			ctypes.POINTER(ctypes.c_uint)),
					("counter",		ctypes.POINTER(ctypes.c_uint)),
					("motor",		ctypes.POINTER(ctypes.c_uint)),	
                    ("encoder",		ctypes.POINTER(ctypes.c_uint)),

                    ("gate",		ctypes.POINTER(ctypes.c_uint)),
					("time",		ctypes.POINTER(ctypes.c_uint)),
					
					("lastErrorCode", ctypes.POINTER(ctypes.c_uint))]
					
					

caput('BL22:SCAN:MASTER.TRIG', 1)			# trigger the FPGA onece to make new .DATA available
while caget('BL22:SCAN:MASTER.TRIG') > 0:	# wait for trigger to complete (time is set via .TWID)
	print('.')								# indicate that the program is still running
	time.sleep(0.1)

	
pvData = caget('BL22:SCAN:MASTER.DATA')		# get the new .DATA


# initialize the variables
numFrames		= numpy.zeros(1, numpy.uint32)
numAdc			= numpy.zeros(1, numpy.uint32)
numCounter		= numpy.zeros(1, numpy.uint32)
numEncoder		= numpy.zeros(1, numpy.uint32)
numMotor		= numpy.zeros(1, numpy.uint32)
lastErrorCode	= numpy.zeros(1, numpy.uint32)

fpgaFrameInfo = FpgaFrameInfo(	0,
								numpy.ctypeslib.as_ctypes(pvData),
								
								numpy.ctypeslib.as_ctypes(numFrames),
								
								numpy.ctypeslib.as_ctypes(numAdc),
								numpy.ctypeslib.as_ctypes(numCounter),
								numpy.ctypeslib.as_ctypes(numEncoder),
								numpy.ctypeslib.as_ctypes(numMotor),
								
								numpy.ctypeslib.as_ctypes(lastErrorCode))

# C function call
omFpgaEvalLib.GetFpgaFrameInfo.restype = None
omFpgaEvalLib.GetFpgaFrameInfo(ctypes.byref(fpgaFrameInfo))

# print some results
print("--- GetFpgaFrameInfo ---")
print("error: ", lastErrorCode[0])	# < 0 on error, 1 on success
print("numFrames: ", numFrames[0])
print("numAdc: ", numAdc[0])
print("numCounter: ", numCounter[0])
print("numEncoder: ", numEncoder[0])
print("------------------------")

# initialize a few more variables
adc		= numpy.zeros(numFrames * numAdc, numpy.uint32)
counter	= numpy.zeros(numFrames * numCounter, numpy.uint32)
motor	= numpy.zeros(numFrames * numMotor, numpy.uint32)
encoder	= numpy.zeros(numFrames * numEncoder, numpy.uint32)
gate	= numpy.zeros(numFrames, numpy.uint32)
time	= numpy.zeros(numFrames, numpy.uint32)

fpgaFrameData = FpgaFrameData (	0,
								numpy.ctypeslib.as_ctypes(pvData),
								
								numpy.ctypeslib.as_ctypes(numFrames),
								
								numpy.ctypeslib.as_ctypes(numAdc),
								numpy.ctypeslib.as_ctypes(numCounter),
								numpy.ctypeslib.as_ctypes(numEncoder),
								numpy.ctypeslib.as_ctypes(numMotor),
								
								numpy.ctypeslib.as_ctypes(adc),
								numpy.ctypeslib.as_ctypes(counter),
								numpy.ctypeslib.as_ctypes(motor),
								numpy.ctypeslib.as_ctypes(encoder),
								
								numpy.ctypeslib.as_ctypes(gate),
								numpy.ctypeslib.as_ctypes(time),
								
								numpy.ctypeslib.as_ctypes(lastErrorCode))

# C function call								
omFpgaEvalLib.EvalFpgaData.restype = None
omFpgaEvalLib.EvalFpgaData(ctypes.byref(fpgaFrameData))


# print some results	
print("--- EvalFpgaData -------")
print("error: ", lastErrorCode[0])								
print("numFrames: ", numFrames[0])
for value in gate:
	print("gate: ", value)
	
for value in adc:
	print("adc: ", value)

for value in counter:
	print("counter: ", value)

for value in motor:
	print("motor: ", value)
	
print("------------------------")



