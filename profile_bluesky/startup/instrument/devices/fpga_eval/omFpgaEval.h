#define OFFSET_DATA_LEN				0
#define OFFSET_TRIG_REG_1			1
#define OFFSET_TRIG_REG_2			2
#define OFFSET_CONF_REG_1			3
#define OFFSET_CONF_REG_2			4

#define MASK_TRIGGER_TIME_MSB		0xFC000000
#define MASK_TRIGGER_TIME_LSB		0x7FFFFFFF
#define MASK_TRIGGER_WIDTH			0x3FFFFFF

#define MASK_CONFIG					0x3F
#define MASK_ADC					0x3FC00
#define MASK_COUNTER				0xFFFFFFFF
#define MASK_MOTOR_ENCODER			0x3C0000

#define MASK_STATUS_MOTOR_1			0x1F
#define MASK_STATUS_MOTOR_2			0x3E0
#define MASK_STATUS_MOTOR_3			0x7C00
#define MASK_STATUS_MOTOR_4			0xF8000

#define MASK_MOTOR_CW_LIMIT			0x01
#define MASK_MOTOR_CCW_LIMIT		0x02
#define MASK_MOTOR_INDEX_HIT		0x04
#define MASK_MOTOR_CW_MOVING		0x08
#define MASK_MOTOR_CCW_MOVING		0x10
#define MASK_DIGITAL_IN				0xFF00000
#define MASK_DAC					0x80000000

#define SHIFT_STATUS_MOTOR_1		0
#define SHIFT_STATUS_MOTOR_2		5
#define SHIFT_STATUS_MOTOR_3		10
#define SHIFT_STATUS_MOTOR_4		15
#define SHIFT_STATUS_DIGITAL_IN		20
#define SHIFT_STATUS_DAC			32

#define SHIFT_CONFIG_CONFIG			0
#define SHIFT_CONFIG_ADC			10
#define SHIFT_CONFIG_MOTOR_ENCODER	18
#define SHIFT_CONFIG_COUNTER		0

typedef struct FpgaFrameInfo
{
    unsigned int lenData;			// length of *data
	int *data;						// .DATA PV, array of signed integers

    unsigned int *numFrames;		// single element

	unsigned int *numAdc;			// single element
	unsigned int *numCounter;		// single element
	unsigned int *numMotor;			// single element
    unsigned int *numEncoder;		// single element

    unsigned int *lastErrorCode;	// single element

} FpgaFrameInfo;


typedef struct FpgaFrameData
{	
    unsigned int lenData;			// length of *data
	int *data;						// .DATA PV, array of signed integers

    unsigned int *numFrames;		// single element

	unsigned int *numAdc;			// single element
	unsigned int *numCounter;		// single element
	unsigned int *numMotor;			// single element
    unsigned int *numEncoder;		// single element

	unsigned int *adc;				// array, length = numFrames * numAdc
	unsigned int *counter;			// array, length = numFrames * numCounter
	unsigned int *motor;			// array, length = numFrames * numMotor
    unsigned int *encoder;			// array, length = numFrames * numEncoder

    unsigned int *gate;				// array, length = numFrames
	unsigned int *time;				// array, length = numFrames

    unsigned int *lastErrorCode;	// single element
} FpgaFrameData;


void GetFpgaFrameInfo(FpgaFrameInfo *fpgaFrameInfo);
void EvalFpgaData(FpgaFrameData *fpgaFrameData);
unsigned int count_high_bits(unsigned int input);