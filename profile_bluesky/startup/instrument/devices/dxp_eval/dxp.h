#define CHA_PER_MOD			4
#define MAX_MCA_CHANNELS	2048
#define MAX_SCA_WINDOWS		8


typedef struct DxpBufferData
{
	unsigned int lenData;			// length of *data
	int *data;						// .DATA Pv, array of integers
	
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


void EvalDxpData(DxpBufferData *dxpBufferData);
int DxpDataGetModNum(unsigned int* _buffer, unsigned int _buffer_len, unsigned int* _mod_num_tot);