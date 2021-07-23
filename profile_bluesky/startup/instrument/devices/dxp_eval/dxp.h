#define CHA_PER_MOD			4
#define MAX_MCA_CHANNELS	2048
#define MAX_SCA_WINDOWS		8

#include <stdio.h>
#include <stdlib.h>

typedef struct DxpBufferData
{
	unsigned int lenData;			// length of *data
	//unsigned int *data;			// .DATA Pv, array of integers
	double *data;					// .DATA Pv, array of integers
	
	unsigned int *numPixel;			// single element
	
	unsigned int *element;			// array, length = numPixel
	unsigned int *pixel;			// array, length = numPixel

	double *liveTime;				// array, length = numPixel
	double *realTime;				// array, length = numPixel
	double *icr;					// array, length = numPixel
	double *ocr;					// array, length = numPixel
	
	int *mcaLen;					// array, length = numPixel
	unsigned int *mca;				// array, length = numPixel * MAX_MCA_CHANNELS
	
	unsigned int *lastErrorCode;	// single element
} DxpBufferData;

typedef struct TestBuffer
{
	unsigned int lenData;			// length of *data
	double *data;						// .DATA Pv, array of integers
	
	unsigned int *numPixel;			// single element
	
	unsigned int *element;			// array, length = numPixel
	unsigned int *pixel;			// array, length = numPixel

	double *liveTime;				// array, length = numPixel
	double *realTime;				// array, length = numPixel
	double *icr;					// array, length = numPixel
	double *ocr;					// array, length = numPixel
	
	int *mcaLen;					// array, length = numPixel
	unsigned int *mca;				// array, length = numPixel * MAX_MCA_CHANNELS
	
	unsigned int *lastErrorCode;	// single element
} TestBuffer;

void test(TestBuffer *dxpBufferData);
void EvalDxpData(DxpBufferData *dxpBufferData);
int DxpDataGetModNum(unsigned int* _buffer, unsigned int _buffer_len, unsigned int* _mod_num_tot);