#include "dxp.h"

void EvalDxpData(DxpBufferData *dxpBufferData)
{
	int rt;
	int i;
	
	unsigned int mod_num_tot = 0;
	
	unsigned int num_pix_buf;
	unsigned int start_pix_num;
	unsigned int start_pix;
	unsigned int stop_pix;

	unsigned int BufHeadLen;
	unsigned int PixHeadLen;
	unsigned int NumChanLen;

	unsigned int WdLen;

	int mod_num_ctr;
	int pix_num_ctr;
	int chan_num_ctr;

	unsigned int first_offset;
	unsigned int second_offset;
	unsigned int third_offset;

	unsigned int dest_offset;

	unsigned int elem_num;

	unsigned int realtime;
	unsigned int livetime;
	unsigned int triggers;
	unsigned int output_events;
	
		
	rt = DxpDataGetModNum(dxpBufferData->data, dxpBufferData->lenData, &mod_num_tot);
	if (rt < 0)
	{
		*dxpBufferData->lastErrorCode = -1;					// DxpDataGetModNum failed
		return;
	}
	
	
	num_pix_buf		=	dxpBufferData->data[8];				// number of pixels in buffer
	start_pix_num	=	dxpBufferData->data[10] << 16 |		// starting pixel number
						dxpBufferData->data[9];

	start_pix		= start_pix_num;
	stop_pix		= start_pix_num + num_pix_buf;


	// check the the Buffer-Header and the very first Pixel-Buffer-Header
	if (	dxpBufferData->data[0] != 0x55AA ||
			dxpBufferData->data[1] != 0xAA55 ||
			dxpBufferData->data[256] != 0x33CC ||
			dxpBufferData->data[257] != 0xCC33)
	{
		*dxpBufferData->lastErrorCode = -2;					// Buffer header is corrupt		
		return;
	}

	
	// Read some information off the the Buffer-Header and off the very first Pixel-Buffer-Header 		
	BufHeadLen = dxpBufferData->data[2];					// 2	Buffer Header Size
	PixHeadLen = dxpBufferData->data[BufHeadLen + 2];		// 2	Buffer Header Size (within Pixel Buffer)		
	NumChanLen = dxpBufferData->data[BufHeadLen + 8];		// 8	Channel Size, Number of ROI

	
	
	WdLen = 1;
	if (PixHeadLen == 256)			// MCA Data
	{
		WdLen = 1;
		/*
		*_frame_type = 0;
		*_frame_arr_len = (int)(mod_num_tot * CHA_PER_MOD * num_pix_buf);
		*_frame_arr = (_dxp_mca_frame*)calloc(*_frame_arr_len, sizeof(_dxp_mca_frame));
		if (*_frame_arr == NULL)
		{
			printf("Error: DxpDataEval: calloc mca_frame_arr failed\n");
			return -1;
		}
		*/
	}
	else if (PixHeadLen == 64)		// SCA Data
	{
		WdLen = 2;
		/*
		*_frame_type = 1;
		*_frame_arr_len = (int)(mod_num_tot * CHA_PER_MOD * num_pix_buf);
		*_frame_arr = (_dxp_sca_frame*)calloc(*_frame_arr_len, sizeof(_dxp_sca_frame));
		if (*_frame_arr == NULL)
		{
			printf("Error: DxpDataEval: calloc sca_frame_arr failed\n");
			return -1;
		}
		*/
	}
	else
	{		
		*dxpBufferData->lastErrorCode = -3;						// Buffer header length is invalid	
		return;
	}
	
	
	
	// loop through all buffers and pixels
	for (mod_num_ctr = 0; mod_num_ctr < (int)mod_num_tot; mod_num_ctr++)
	{
		first_offset = (unsigned int)(((PixHeadLen + (WdLen * CHA_PER_MOD * NumChanLen)) * num_pix_buf) + BufHeadLen) * (unsigned int)mod_num_ctr;

		for (pix_num_ctr = 0; pix_num_ctr < (int)stop_pix - (int)start_pix; pix_num_ctr++)
		{
			second_offset = ((PixHeadLen + (WdLen * CHA_PER_MOD * NumChanLen)) * (unsigned int)pix_num_ctr) + BufHeadLen;

			// Check if the 'first_offset' points to a Buffer
			if (dxpBufferData->data[first_offset] != 0x55AA)
			{				
				*dxpBufferData->lastErrorCode = -4;				//firts_offset points in the wrong direction
				return;
			}

			// Check if the 'second_offset' points to Pixel-Buffer
			if (dxpBufferData->data[first_offset + second_offset] != 0x33CC)
			{
				
				*dxpBufferData->lastErrorCode = -5;				// second_offset points in the wrong direction
				return;
			}

			//loop through all channels
			for (chan_num_ctr = 0; chan_num_ctr < CHA_PER_MOD; chan_num_ctr++)
			{
				third_offset = 32;

				//destination offset				
				elem_num	= (unsigned int)(mod_num_ctr * CHA_PER_MOD) + (unsigned int)chan_num_ctr;
				dest_offset	= (unsigned int)(mod_num_tot * CHA_PER_MOD * (unsigned int)pix_num_ctr + mod_num_ctr * CHA_PER_MOD + chan_num_ctr);


				realtime =		dxpBufferData->data[first_offset + second_offset + third_offset + (unsigned int)(chan_num_ctr * 8) + 1] << 16 |
								dxpBufferData->data[first_offset + second_offset + third_offset + (unsigned int)(chan_num_ctr * 8) + 0];

				livetime =		dxpBufferData->data[first_offset + second_offset + third_offset + (unsigned int)(chan_num_ctr * 8) + 3] << 16 |
								dxpBufferData->data[first_offset + second_offset + third_offset + (unsigned int)(chan_num_ctr * 8) + 2];

				triggers =		dxpBufferData->data[first_offset + second_offset + third_offset + (unsigned int)(chan_num_ctr * 8) + 5] << 16 |
								dxpBufferData->data[first_offset + second_offset + third_offset + (unsigned int)(chan_num_ctr * 8) + 4];

				output_events =	dxpBufferData->data[first_offset + second_offset + third_offset + (unsigned int)(chan_num_ctr * 8) + 7] << 16 |
								dxpBufferData->data[first_offset + second_offset + third_offset + (unsigned int)(chan_num_ctr * 8) + 6];

				if (WdLen == 1)		// MCA Data
				{
					third_offset = 256;

					dxpBufferData->element[dest_offset]		= elem_num;
					dxpBufferData->pixel[dest_offset]		= start_pix + (unsigned int) pix_num_ctr;
					dxpBufferData->liveTime[dest_offset]	= (double)realtime * 320e-9;
					dxpBufferData->realTime[dest_offset]	= (double)livetime * 320e-9;
					dxpBufferData->icr[dest_offset]			= (double)triggers / ((double)livetime * 320e-9);
					dxpBufferData->ocr[dest_offset]			= (double)output_events / ((double)livetime * 320e-9);
					dxpBufferData->mcaLen[dest_offset]		= (int)NumChanLen;

					for (i = 0; i < (int)NumChanLen; i++)
					{
						dxpBufferData->mca[dest_offset * NumChanLen + i] = dxpBufferData->data[first_offset + second_offset + third_offset + (unsigned int)(chan_num_ctr * NumChanLen) + i];
					}
				}
				else if (WdLen == 2)	// SCA Data
				{
					third_offset = 64;
					
					dxpBufferData->element[dest_offset]		= elem_num;
					dxpBufferData->pixel[dest_offset]		= start_pix + (unsigned int) pix_num_ctr;
					dxpBufferData->liveTime[dest_offset]	= (double)realtime * 320e-9;
					dxpBufferData->realTime[dest_offset]	= (double)livetime * 320e-9;
					dxpBufferData->icr[dest_offset]			= (double)triggers / ((double)livetime * 320e-9);
					dxpBufferData->ocr[dest_offset]			= (double)output_events / ((double)livetime * 320e-9);
					dxpBufferData->mcaLen[dest_offset]		= (int)NumChanLen;					

					for (i = 0; i < (int)NumChanLen; i++)
					{
						dxpBufferData->mca[dest_offset * NumChanLen + i] =	dxpBufferData->data[first_offset + second_offset + third_offset + (unsigned int)(2 * chan_num_ctr * NumChanLen) + (unsigned int)(2 * i) + 1] << 16 |
																			dxpBufferData->data[first_offset + second_offset + third_offset + (unsigned int)(2 * chan_num_ctr * NumChanLen) + (unsigned int)(2 * i)];
					}
				}
			}
		}
	}
	
	*dxpBufferData->lastErrorCode = 1;	
}

int DxpDataGetModNum(unsigned int* _buffer, unsigned int _buffer_len, unsigned int* _mod_num_tot)
{
	unsigned int BufHeadLen;
	unsigned int PixHeadLen;
	unsigned int NumChanLen;
	unsigned int NumPixBuf;
	unsigned int PixBufLen;


	// check the the Buffer-Header and the very first Pixel-Buffer-Header
	if (	_buffer[0]		!= 0x55AA ||
			_buffer[1]		!= 0xAA55 ||
			_buffer[256]	!= 0x33CC ||
			_buffer[257]	!= 0xCC33)
	{
		//printf("Error: DxpDataEval: Buffer header is corrupt\n");
		return -1;
	}


	// Read some information off the the Buffer-Header and off the very first Pixel-Buffer-Header
	BufHeadLen	= _buffer[2];				// 2		main buffer header size
	NumPixBuf	= _buffer[8];				// 8		number of pixels in buffer
	PixHeadLen	= _buffer[BufHeadLen + 2];	// 2		pixel buffer header size
	NumChanLen	= _buffer[BufHeadLen + 8];	// 8		channel size, number of ROIs


	if (PixHeadLen == 256)				// MCA Data
	{
		PixBufLen = PixHeadLen + (unsigned int)(CHA_PER_MOD * NumChanLen);
	}
	else if (PixHeadLen == 64)			// SCA Data
	{
		PixBufLen = PixHeadLen + (unsigned int)(CHA_PER_MOD * 2 * NumChanLen);
	}
	else
	{
		//printf("Error: DxpDataEval: Buffer header length is invalid\n");
		return -1;
	}


	*_mod_num_tot = (unsigned int)((double)(_buffer_len) / (double)(PixBufLen * NumPixBuf + BufHeadLen));

	return 0;
}