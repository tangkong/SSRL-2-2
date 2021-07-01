#include "omFpgaEval.h"

void GetFpgaFrameInfo(FpgaFrameInfo *fpgaFrameInfo)
{
	unsigned int word;
	unsigned int data_num_bytes			= 0;
	unsigned int user_data_per_frame	= 0;
	unsigned int num_frames				= 0;
	
	unsigned int frame_size;
	unsigned int frame_offset;

	unsigned int config_config;
	unsigned int config_adc;
	unsigned int config_counter;
	unsigned int config_encoder;
	unsigned int config_motor;

	unsigned int num_trigger	= 2;
	unsigned int num_config		= 0;
	unsigned int num_counters	= 0;
	unsigned int num_adcs		= 0;
	unsigned int num_motors		= 0;
	unsigned int num_encoders	= 0;
	
	
	//unsigned int *buffer = (unsigned int*)&fpgaFrameData->data
	
	//--- LENGTH -----------------------------------------------------------	
	word = (unsigned int)fpgaFrameInfo->data[0];
	data_num_bytes = word;
	if (data_num_bytes < 20)				// The firts frame must have at least 5 words (20 bytes)
	{
		*fpgaFrameInfo->lastErrorCode = -1;
		return;
	}
	//----------------------------------------------------------------------

	
	//--- DAQ DATA TYPE ----------------------------------------------------			
	word = (unsigned int)fpgaFrameInfo->data[1];
	if ((word & 0x80000000) != 0)			// check if daq data or automatic status report
	{	
		*fpgaFrameInfo->lastErrorCode = -2;	
		return;
	}
	//----------------------------------------------------------------------


	//--- CONFIG -----------------------------------------------------------
	// Config 1
	word = (unsigned int)fpgaFrameInfo->data[3];
	config_config	=	(word & MASK_CONFIG)		>> SHIFT_CONFIG_CONFIG;
	config_adc		=	(word & MASK_ADC)			>> SHIFT_CONFIG_ADC;
	config_encoder	=	(word & MASK_MOTOR_ENCODER)	>> SHIFT_CONFIG_MOTOR_ENCODER;
	config_motor	=	(word & MASK_MOTOR_ENCODER)	>> SHIFT_CONFIG_MOTOR_ENCODER;

	// Config 1
	word = (unsigned int)fpgaFrameInfo->data[4];
	config_counter	=	(word & MASK_COUNTER)		>> SHIFT_CONFIG_COUNTER;
	//----------------------------------------------------------------------


	//----------------------------------------------------------------------
	num_config		=	count_high_bits(config_config);
	num_adcs		=	count_high_bits(config_adc);
	num_encoders	=	count_high_bits(config_encoder);
	num_motors		=	count_high_bits(config_motor);
	num_counters	=	count_high_bits(config_counter);
	//----------------------------------------------------------------------


	//----------------------------------------------------------------------
	// verify the validity of data_num_bytes and get num_frames
	//----------------------------------------------------------------------
	frame_size = num_config + num_adcs + num_encoders + num_motors + num_counters + 3;
	user_data_per_frame = 4 * frame_size;
	if ((data_num_bytes - 8) % user_data_per_frame != 0)
	{
		*fpgaFrameInfo->lastErrorCode = -3;
		return;
	}
	num_frames = (data_num_bytes - 8) / user_data_per_frame;
	//----------------------------------------------------------------------


	//----------------------------------------------------------------------
	*fpgaFrameInfo->numFrames	= num_frames;	
	*fpgaFrameInfo->numAdc		= num_adcs;
	*fpgaFrameInfo->numCounter	= num_counters;
	*fpgaFrameInfo->numEncoder	= num_encoders;
	*fpgaFrameInfo->numMotor	= num_motors;
	//----------------------------------------------------------------------
	
	*fpgaFrameInfo->lastErrorCode = 1;
	return;
}

void EvalFpgaData(FpgaFrameData *fpgaFrameData)
{
	int n;
	int i = 0;
	int j = 0;

	unsigned int word;
	unsigned int data_num_bytes			= 0;
	unsigned int user_data_per_frame	= 0;
	unsigned int num_frames				= 0;
	
	unsigned int frame_size;
	unsigned int frame_offset;

	unsigned int config_config;
	unsigned int config_adc;
	unsigned int config_counter;
	unsigned int config_encoder;
	unsigned int config_motor;

	unsigned int num_trigger	= 2;
	unsigned int num_config		= 0;
	unsigned int num_counters	= 0;
	unsigned int num_adcs		= 0;
	unsigned int num_motors		= 0;
	unsigned int num_encoders	= 0;

	unsigned int offset_trigger;
	unsigned int offset_config;
	unsigned int offset_counter;
	unsigned int offset_adc;
	unsigned int offset_encoder;
	unsigned int offset_motor;
	unsigned int offset_ios;

	unsigned int status_motor_1;
	unsigned int status_motor_2;
	unsigned int status_motor_3;
	unsigned int status_motor_4;
	unsigned int status_digital_in;
	unsigned int status_dac;

	//----------------------------------------------------------------------
	// The ZERO Header
	//----------------------------------------------------------------------
	// the very first 5 words (20 bytes) conatin additional information
	// which is not repeated in subsequent headers
	//
	//	0	Total lentgh in Bytes
	//	1	Trigger 1
	//	2	Trigger 2
	//	3	Config 1
	//	4	Config 2
	//----------------------------------------------------------------------


	//--- LENGTH -----------------------------------------------------------
	word = fpgaFrameData->data[0];
	data_num_bytes = word;
	if (data_num_bytes < 20)				// The firts frame must have at least 5 words (20 bytes)
	{
		*fpgaFrameData->lastErrorCode = -1;
		return;
	}
	//----------------------------------------------------------------------

	
	//--- DAQ DATA TYPE ----------------------------------------------------			
	word = fpgaFrameData->data[1];
	if ((word & 0x80000000) != 0)			// check if daq data or automatic status report
	{	
		*fpgaFrameData->lastErrorCode = -2;	
		return;
	}
	//----------------------------------------------------------------------


	//--- CONFIG -----------------------------------------------------------
	// Config 1
	word = fpgaFrameData->data[3];
	config_config	=	(word & MASK_CONFIG)		>> SHIFT_CONFIG_CONFIG;
	config_adc		=	(word & MASK_ADC)			>> SHIFT_CONFIG_ADC;
	config_encoder	=	(word & MASK_MOTOR_ENCODER)	>> SHIFT_CONFIG_MOTOR_ENCODER;
	config_motor	=	(word & MASK_MOTOR_ENCODER)	>> SHIFT_CONFIG_MOTOR_ENCODER;

	// Config 1
	word = fpgaFrameData->data[4];
	config_counter	=	(word & MASK_COUNTER)		>> SHIFT_CONFIG_COUNTER;
	//----------------------------------------------------------------------


	//----------------------------------------------------------------------
	num_config		=	count_high_bits(config_config);
	num_adcs		=	count_high_bits(config_adc);
	num_encoders	=	count_high_bits(config_encoder);
	num_motors		=	count_high_bits(config_motor);
	num_counters	=	count_high_bits(config_counter);
	//----------------------------------------------------------------------


	//----------------------------------------------------------------------
	// verify the validity of data_num_bytes and get num_frames
	//----------------------------------------------------------------------
	frame_size = num_config + num_adcs + num_encoders + num_motors + num_counters + 3;
	user_data_per_frame = 4 * frame_size;
	if ((data_num_bytes - 8) % user_data_per_frame != 0)
	{
		*fpgaFrameData->lastErrorCode = -3;
		return;
	}
	num_frames = (data_num_bytes - 8) / user_data_per_frame;
	//----------------------------------------------------------------------


	
	//----------------------------------------------------------------------
	*fpgaFrameData->numFrames	= num_frames;	
	*fpgaFrameData->numAdc		= num_adcs;
	*fpgaFrameData->numCounter	= num_counters;
	*fpgaFrameData->numEncoder	= num_encoders;
	*fpgaFrameData->numMotor	= num_motors;
	//----------------------------------------------------------------------
	


	//----------------------------------------------------------------------
	// Read data frames
	//----------------------------------------------------------------------						
	for (n = 0; n < num_frames; n++)
	{

		// determine correct offsets
		// the 1st frame (n == 0) differs from the others
		if (n == 0)
		{
			frame_offset = 1;

			offset_trigger	=	frame_offset;
			offset_config	=	offset_trigger	+ num_trigger + 2;
			offset_counter	=	offset_config	+ num_config;
			offset_adc		=	offset_counter	+ num_counters;
			offset_encoder	=	offset_adc		+ num_adcs;
			offset_motor	=	offset_encoder	+ num_encoders;
			offset_ios		=	offset_motor	+ num_motors;
		}
		else
		{
			frame_offset = (unsigned int)(frame_size * n) + 3;

			offset_trigger	=	frame_offset;
			offset_config	=	offset_trigger	+ num_trigger;
			offset_counter	=	offset_config	+ num_config;
			offset_adc		=	offset_counter	+ num_counters;
			offset_encoder	=	offset_adc		+ num_adcs;
			offset_motor	=	offset_encoder	+ num_encoders;
			offset_ios		=	offset_motor	+ num_motors;
		}


		//--- read TRIGGER --- 2 words ---
		word = fpgaFrameData->data[offset_trigger];		
		fpgaFrameData->time[n]	=	word & MASK_TRIGGER_TIME_LSB;
				
		word = fpgaFrameData->data[offset_trigger + 1];
		fpgaFrameData->time[n]	|=	(word & MASK_TRIGGER_TIME_MSB) << 5;
		fpgaFrameData->gate[n]	=	word & MASK_TRIGGER_WIDTH;


		//--- read COUNTERs --- 32 words ---
		for (i = 0; i < num_counters; i++)
		{
			fpgaFrameData->counter[i + n * num_counters] = fpgaFrameData->data[offset_counter + i];
		}


		//--- read ADCs --- 8 words ---
		for (i = 0; i < num_adcs; i++)
		{
			fpgaFrameData->adc[i + n * num_adcs] = fpgaFrameData->data[offset_adc + i];
		}


		//--- read ENCODERs --- 4 words ---
		for (i = 0; i < num_encoders; i++)
		{			
			fpgaFrameData->encoder[i + n * num_encoders] = fpgaFrameData->data[offset_encoder + i] + 0x7FFFFFFF;
		}


		//--- read MOTORs --- 4 words ---
		for (i = 0; i < num_motors; i++)
		{
			fpgaFrameData->motor[i + n * num_motors] = fpgaFrameData->data[offset_motor + i];			
		}
	}
	//----------------------------------------------------------------------
	
	*fpgaFrameData->lastErrorCode = 1;
	return;
}

unsigned int count_high_bits(unsigned int input)
{
	unsigned int value = input;
	unsigned int num = 0;

	while (value > 0)
	{
		num += value & 0x01;
		value >>= 1;
	}

	return num;
}

