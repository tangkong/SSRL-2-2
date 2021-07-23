from epics import caget, caput
import ctypes
import numpy


omDxpLib = ctypes.cdll.LoadLibrary("/home/b_spec/omueller/Dxp/dxp.so")

class DxpData(ctypes.Structure):
	_fields_ = [	("lenData",			ctypes.c_uint),
					("data",			ctypes.POINTER(ctypes.c_double)),
					
					("numPixel",		ctypes.POINTER(ctypes.c_uint)),
					
					("element",			ctypes.POINTER(ctypes.c_uint)),
					("pixel",			ctypes.POINTER(ctypes.c_uint)),
					
					("liveTime",		ctypes.POINTER(ctypes.c_double)),
					("realTime",		ctypes.POINTER(ctypes.c_double)),
					("icr",				ctypes.POINTER(ctypes.c_double)),
					("ocr",				ctypes.POINTER(ctypes.c_double)),
					
					("mcaLen",			ctypes.POINTER(ctypes.c_int)),
					("mca",				ctypes.POINTER(ctypes.c_uint)),
										
					("lastErrorCode",	ctypes.POINTER(ctypes.c_int))]

					
maxMcaLen		= 2048
numBufPix		= caget('DXP1:DXP.NumBufPix')		# numBufPix should be the same for all DXPs
numDetElements	= caget('DXP1:DXP.NumDetElements')	# numDetElements is not the same for all DXPs
pvDxpData		= caget('DXP1:DXP.Data')			# for this test here, this should get you the most recent buffer

print("pvDxpData: ", pvDxpData.dtype)

#initialize the variables
numPixel		= numpy.zeros(1,										numpy.uint32)
element			= numpy.zeros(numBufPix * numDetElements,				numpy.uint32)
pixel			= numpy.zeros(numBufPix * numDetElements,				numpy.uint32)
liveTime		= numpy.zeros(numBufPix * numDetElements,				numpy.float64)
realTime		= numpy.zeros(numBufPix * numDetElements,				numpy.float64)
icr				= numpy.zeros(numBufPix * numDetElements,				numpy.float64)
ocr				= numpy.zeros(numBufPix * numDetElements,				numpy.float64)
mcaLen			= numpy.zeros(numBufPix * numDetElements,				numpy.int32)
mca				= numpy.zeros(numBufPix * numDetElements * maxMcaLen,	numpy.uint32)
lastErrorCode	= numpy.zeros(1,										numpy.int32)


dxpData = DxpData(	0,
					numpy.ctypeslib.as_ctypes(pvDxpData),					
					numpy.ctypeslib.as_ctypes(numPixel),
					numpy.ctypeslib.as_ctypes(element),
					numpy.ctypeslib.as_ctypes(pixel),
					numpy.ctypeslib.as_ctypes(liveTime),
					numpy.ctypeslib.as_ctypes(realTime),
					numpy.ctypeslib.as_ctypes(icr),
					numpy.ctypeslib.as_ctypes(ocr),					
					numpy.ctypeslib.as_ctypes(mcaLen),					
					numpy.ctypeslib.as_ctypes(mca),
					numpy.ctypeslib.as_ctypes(lastErrorCode))

# C function call					
omDxpLib.EvalDxpData.restype = None
omDxpLib.EvalDxpData(ctypes.byref(dxpData))


# print some results
print("--- EvalDxpData -------")
print("error: ", lastErrorCode[0])								
print("numPixel: ", numPixel[0])
print("------------------------")
print("element: ",	element[0])
print("pixel: ",	pixel[0])
print("icr: ",		icr[0])
print("liveTime: ",	liveTime[0])
print("------------------------")


