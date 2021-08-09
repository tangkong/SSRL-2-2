#include "motion.h"

void CalcTrigger(FpgaTrigger *fpgaTrigger)
{	
	int rt = calc_trigger(	fpgaTrigger->time,
							fpgaTrigger->energy,
							fpgaTrigger->timeEnergyLen,
												
							fpgaTrigger->trigger,
							fpgaTrigger->triggerLen);
												
	*fpgaTrigger->lastErrorCode = rt;
}
void CalcMotion(FpgaMotion *fpgaMotion)
{
	int rt = calc_motion( fpgaMotion->time,
							fpgaMotion->energy,
							fpgaMotion->timeEnergyLen,
												
							fpgaMotion->crystalD,
							fpgaMotion->crystalGap,
							fpgaMotion->motorResPhi,
							fpgaMotion->motorResZ,
										
							fpgaMotion->motionPhi,
							fpgaMotion->motionPhiLen,
							fpgaMotion->motionZ,
							fpgaMotion->motionZLen);
												
	*fpgaMotion->lastErrorCode = rt;
}







int calc_trigger(	double *_time,
					double *_energy,
					unsigned int _len, 
					double *_trigger,
					unsigned int *_trigger_len)
{
	int rt;
	int i, j;
	int num_seg;	

	double *trigger_time;
	double *target_trigger_time;
	int *trigger_time_int;
	unsigned int *trigger_uint;	
		
	double trigger_time_err;
	double gen_trigger_time;
	double target_time;

	
	trigger_time_err = 0;
	num_seg = _len - 1;
	*_trigger_len = num_seg + 1;


	//-------------------------------------------------------------------
	// allocate memory
	//-------------------------------------------------------------------
	trigger_time = (double *)calloc(num_seg, sizeof(double));
	if (trigger_time == NULL) {
		//error("ERROR: calc motion: calloc");
		return -1;
	}
	target_trigger_time = (double *)calloc(num_seg, sizeof(double));
	if (target_trigger_time == NULL) {
		//error("ERROR: calc motion: calloc");
		return -1;
	}
	trigger_time_int = (int *)calloc(num_seg, sizeof(double));
	if (trigger_time_int == NULL) {
		//error("ERROR: calc motion: calloc");
		return -1;
	}
	//*_trigger = (double*)calloc(*_trigger_len, sizeof(double));
	//if (*_trigger == NULL) {
	//	//error("ERROR: calc motion: calloc");
	//	return -1;
	//}
	trigger_uint = (unsigned int*)calloc(*_trigger_len, sizeof(unsigned int));
	if (trigger_uint == NULL) {
		//error("ERROR: calc motion: calloc");
		return -1;
	}
	//-------------------------------------------------------------------
	

	//-------------------------------------------------------------------
	// generate trigger
	//-------------------------------------------------------------------
	// Header
	// ToDo: check if num_seg exceeds maximum length
	trigger_time_err = 0;
	trigger_uint[0] = (num_seg & 0x3fff);											// time base: ms
	for (i = 0; i < num_seg; i++) {
		trigger_time[i] = (_time[i + 1] - _time[i]) * 1000.0;						// precise trigger time in ms

		target_trigger_time[i] = trigger_time[i] + trigger_time_err;				// target trigger time with rounding errors from last segment
		trigger_time_int[i] = (int)round(target_trigger_time[i]);					// actual trigger time in this segment		
		trigger_time_err = target_trigger_time[i] - (double)trigger_time_int[i];	// rounding error of this segment

		trigger_uint[i + 1] = (unsigned int)trigger_time_int[i];		
	}	
	//-------------------------------------------------------------------
	for (i = 0; i < *_trigger_len; i++) {		
		_trigger[i] = (double)trigger_uint[i];
	}
	//-------------------------------------------------------------------


	//-------------------------------------------------------------------
	// verify trigger
	//-------------------------------------------------------------------
	gen_trigger_time = 0;
	for (i = 0; i < num_seg; i++) {
		gen_trigger_time += (double)trigger_uint[i + 1];
	}
	gen_trigger_time /= 1000.0;
	target_time = fabs(_time[_len - 1] - _time[0]);
	//-------------------------------------------------------------------
	//sprintf(msg, "Target Trigger Time:\t%.4f", target_time);
	//debug(msg);
	//sprintf(msg, "Actual Trigger Time:\t%.4f", gen_trigger_time);
	//debug(msg);
	//sprintf(msg, "Error Trigger Time:\t%.4f", target_time - gen_trigger_time);
	//debug(msg);
	//-------------------------------------------------------------------

	free(trigger_time);
	free(target_trigger_time);
	free(trigger_time_int);
	free(trigger_uint);

	return 1;
}

int calc_motion(	double *_time,
					double *_energy,
					unsigned int _len,
					double _crystal_lattice,
					double _crystal_gap,
					double _motor_res_phi,
					double _motor_res_z,
					double *_phi_motion,
					unsigned int *_phi_motion_len,	
					double *_z_motion,
					unsigned int *_z_motion_len)
{
	int rt;
	int i, j, k, n, m;
	double *phi;
	double *z;

	int num_seg;	

	unsigned int *phi_motion_uint;
	unsigned int *z_motion_uint;

	double *seg_phi;
	double *seg_z;

	double seg_num_steps_err = 0;
	double seg_step_time_err = 0;
	double seg_delta_step_time_err = 0;

	double *seg_time;
	double *seg_num_steps;
	double *seg_step_time;
	double *seg_delta_step_time;

	int *seg_num_steps_int;
	int *seg_step_time_int;
	int *seg_delta_step_time_int;
	
	double gen_steps;
	double gen_time;
	double seg_time_int;
	double target_steps;
	double target_time;	

	//-------------------------------------------------------------------
	// allocate memory
	//-------------------------------------------------------------------
	phi = (double *)calloc(_len, sizeof(double));
	if (phi == NULL) {
		//error("ERROR: calc motion: calloc");
		return -1;
	}
	z = (double *)calloc(_len, sizeof(double));
	if (z == NULL) {
		//error("ERROR: calc motion: calloc");
		return -1;
	}
	//-------------------------------------------------------------------
	seg_time = (double *)calloc(_len, sizeof(double));
	if (seg_time == NULL) {
		//error("ERROR: calc motion: calloc");
		return -1;
	}
	seg_phi = (double *)calloc(_len, sizeof(double));
	if (seg_phi == NULL) {
		//error("ERROR: calc motion: calloc");
		return -1;
	}
	seg_z = (double *)calloc(_len, sizeof(double));
	if (seg_z == NULL) {
		//error("ERROR: calc motion: calloc");
		return -1;
	}
	//-------------------------------------------------------------------
	seg_num_steps = (double *)calloc(_len, sizeof(double));
	if (seg_num_steps == NULL) {
		//error("ERROR: calc motion: calloc");
		return -1;
	}
	seg_step_time = (double *)calloc(_len, sizeof(double));
	if (seg_step_time == NULL) {
		//error("ERROR: calc motion: calloc");
		return -1;
	}
	seg_delta_step_time = (double *)calloc(_len, sizeof(double));
	if (seg_delta_step_time == NULL) {
		//error("ERROR: calc motion: calloc");
		return -1;
	}
	seg_num_steps_int = (int *)calloc(_len, sizeof(int));
	if (seg_num_steps_int == NULL) {
		//error("ERROR: calc motion: calloc");
		return -1;
	}
	seg_step_time_int = (int *)calloc(_len, sizeof(int));
	if (seg_step_time_int == NULL) {
		//error("ERROR: calc motion: calloc");
		return -1;
	}
	seg_delta_step_time_int = (int *)calloc(_len, sizeof(int));
	if (seg_delta_step_time_int == NULL) {
		//error("ERROR: calc motion: calloc");
		return -1;
	}		
	//-------------------------------------------------------------------	


	//-------------------------------------------------------------------
	// calculate phi
	//-------------------------------------------------------------------
	for (i = 0; i < (int)_len; i++)
	{
		rt = convert_energy_to_angle(_energy[i], &(phi[i]), _crystal_lattice);
		if (!rt)
		{
			//error("ERROR: calc motion: convert_energy_to_angle");
			return -1;
		}
	}
	//-------------------------------------------------------------------


	//-------------------------------------------------------------------
	// calculate z
	//-------------------------------------------------------------------
	for (i = 0; i < (int)_len; i++)
	{
		z[i] = 2.0 * _crystal_gap * cos(phi[i] * PI / 180.0);
	}
	//-------------------------------------------------------------------


	//-------------------------------------------------------------------
	// calculate phi_motion segments																	// BASE SPEED not considered !!!
	//-------------------------------------------------------------------
	// claculate number of steps 'seg_num_steps_int' and 
	// calculate initial time betweeen steps 'seg_step_time_int'	
	i = 0;
	j = 1;
	k = 0;	
	seg_num_steps_err = 0;	
	while (i + j < _len)
	{
		//--- Get Time ------------------------------------------------------				
		seg_time[k] = (_time[i + j] - _time[i]) * 1000000.0;											// precise duration of this grid-element in us
		//-------------------------------------------------------------------


		//--- Get Steps -----------------------------------------------------		
		seg_num_steps[k] = fabs(phi[i + j] - phi[i]) * _motor_res_phi;									// precise number of steps in this grid-segment
		seg_num_steps[k] += seg_num_steps_err;															// precise number of steps in this grid-segment (including accumulated error)
		seg_num_steps_int[k] = (int)round(seg_num_steps[k]);											// actual number of steps in this grid-segment (including accumulated error)
		if (seg_num_steps_int[k] < 1)																	// if there are no steps in this grid-segment
		{			
			j++;																						// the grid length needs to be increased
			continue;
		}
		seg_num_steps_err = seg_num_steps[k] - seg_num_steps_int[k];									// rounding error of this grid-segment
		//-------------------------------------------------------------------
		
		
		//-- Get Time Between Steps -----------------------------------------			
		seg_step_time[k] = seg_time[k] / (fabs(phi[i + j] - phi[i]) * _motor_res_phi);					// precise initial time between setps in us in this grid-segment
		seg_step_time[k] += seg_step_time_err;															// account for rounding errors from last grid-segment
		seg_step_time_int[k] = (int)round(seg_step_time[k]);											// actual time between steps in us in this segment
		if (seg_step_time_int[k] < 1)
		{
			//sprintf(msg, "seg_step_time_int < 1");
			//error(msg);
		}
		seg_step_time_err = seg_step_time[k] - seg_step_time_int[k];									// rounding error of this segment
		//----------------------------------------------------------------------------
		
		seg_phi[k] = phi[i];

		i += j;
		j = 1;
		k++;
	}
	

	//-------------------------------------------------------------------
	// allocate memory
	//-------------------------------------------------------------------
	num_seg = k;																						// This is the actual number of segments	
	*_phi_motion_len = num_seg + num_seg + 2;	
	//-------------------------------------------------------------------
	//*_phi_motion = (double*)calloc(*_phi_motion_len, sizeof(double));
	//if (*_phi_motion == NULL) {
	//	//error("ERROR: calc motion: calloc");
	//	return -1;
	//}
	phi_motion_uint = (unsigned int *)calloc(*_phi_motion_len, sizeof(unsigned int));
	if (phi_motion_uint == NULL) {
		//error("ERROR: calc motion: calloc");
		return -1;
	}
	//-------------------------------------------------------------------

	if (num_seg > 0) {																					// can be 0 if there is no motion
		// claculate change of time between steps 'seg_delta_step_time_int'
		for (i = 0; i < num_seg; i++) {
			seg_num_steps[i] = fabs(seg_phi[i + 1] - seg_phi[i]) * _motor_res_phi;						// precise number of steps in this segment
			seg_step_time[i] = seg_time[i] / seg_num_steps[i];											// precise initial time between setps in us in this segment
		}
		for (i = 0; i < num_seg - 1; i++) {
			seg_delta_step_time[i] = (seg_step_time[i + 1] - seg_step_time[i]) / seg_num_steps[i];		// precise detlta_step_time in us in this segment
			seg_delta_step_time[i] += seg_delta_step_time_err;											// account for rounding errors from last segment
			seg_delta_step_time_int[i] = (int)round(seg_delta_step_time[i]);							// actual delta_setp_time in us in this segment		
			seg_delta_step_time_err = seg_delta_step_time[i] - seg_delta_step_time_int[i];				// rounding error of this segment
		}

		// calculate the last segment	
		seg_delta_step_time_int[num_seg - 1] = 0;
	}
	//-------------------------------------------------------------------


	//-------------------------------------------------------------------
	// verify phi_motion
	//-------------------------------------------------------------------
	gen_steps = 0;
	gen_time = 0;
	seg_time_int = 0;
	target_steps = fabs(phi[_len - 1] - phi[0]) * _motor_res_phi;
	target_time = fabs(_time[_len - 1] - _time[0]);
	//-------------------------------------------------------------------
	for (i = 0; i < num_seg; i++) {		
		seg_time_int = (double)seg_num_steps_int[i] * (double)seg_step_time_int[i];
		seg_time_int += 0.5 * seg_delta_step_time_int[i] * ((seg_num_steps_int[i] - 1.0) * (seg_num_steps_int[i] - 1.0) + (seg_num_steps_int[i] - 1.0));

		gen_steps += seg_num_steps_int[i];
		gen_time += seg_time_int;
	}
	gen_time /= 1000000.0;
	//-------------------------------------------------------------------	
	//sprintf(msg, "PHI Segments:\t%d", num_seg);
	//debug(msg);
	//sprintf(msg, "PHI Target Steps:\t%.4f", target_steps);
	//debug(msg);
	//sprintf(msg, "PHI Gen Steps:\t%.4f", gen_steps);
	//debug(msg);
	//sprintf(msg, "PHI Error Steps:\t%.4f", gen_steps - target_steps);
	//debug(msg);
	//sprintf(msg, "PHI Target Time:\t%.4f", target_time);
	//debug(msg);
	//sprintf(msg, "PHI Actual Time:\t%.4f", gen_time);
	//debug(msg);
	//sprintf(msg, "PHI Error Time:\t%.4f", target_time - gen_time);
	//debug(msg);
	//-------------------------------------------------------------------



	//-------------------------------------------------------------------
	// generate phi_motion
	//-------------------------------------------------------------------
	// Header
	phi_motion_uint[0] = (unsigned int)(num_seg & 0x1fff);														// 13 bits						bit 0 - 12	number of segments;	
	phi_motion_uint[0] |= (1 << 31);																			// 1 bit						bit 31		initial direction: 0 - CW, 1 - CCW
	phi_motion_uint[1] = 0;

	for (i = 0; i < num_seg; i++) {
		phi_motion_uint[2 * i + 2] |= (unsigned int)(seg_num_steps_int[i] - 1) & 0x7fffff;						// 23 bits						bit 0 - 22	number of steps, less 1
		phi_motion_uint[2 * i + 2] |= (((unsigned int)(seg_step_time_int[i] - 1) & 0x1ff) << 23);				// 9 least significant bits		bit 23 - 31	starting interval in 1us ticks, less 1 (9 LSBs)
		phi_motion_uint[2 * i + 3] |= ((unsigned int)(seg_step_time_int[i] - 1) >> 9) & 0x7ff;					// 11 most significant bits		bit 0 - 10	starting interval in 1us ticks, less 1 (11 MSBs)

		if (seg_delta_step_time_int[i] < 0) {
			phi_motion_uint[2 * i + 3] |= (((unsigned int)(-1 * seg_delta_step_time_int[i]) & 0xfffff) << 11);	// 20 bits						bit 11 - 30	change in interval between steps
			phi_motion_uint[2 * i + 3] |= (1 << 31);															// 1 bit						bit 31		0 - decelerate, 1 - accelerate
		}
		else {
			phi_motion_uint[2 * i + 3] |= (((unsigned int)(seg_delta_step_time_int[i]) & 0xfffff) << 11);		// 20 bits						bit 11 - 30	change in interval between steps
		}
	}
	//-------------------------------------------------------------------
	for (i = 0; i < *_phi_motion_len; i++) {
		_phi_motion[i] = (double)phi_motion_uint[i];
	}
	//-------------------------------------------------------------------


	//-------------------------------------------------------------------
	// calculate z_motion segments																	// BASE SPEED not considered !!!
	//-------------------------------------------------------------------
	// claculate number of steps 'seg_num_steps_int' and 
	// calculate initial time betweeen steps 'seg_step_time_int'
	i = 0;
	j = 1;
	k = 0;
	seg_num_steps_err = 0;
	while (i + j < _len) {
		//--- Get Time ------------------------------------------------------				
		seg_time[k] = (_time[i + j] - _time[i]) * 1000000.0;									// precise duration of this segment in us
		//-------------------------------------------------------------------

		//--- Get Steps -----------------------------------------------------		
		seg_num_steps[k] = fabs(z[i + j] - z[i]) * _motor_res_z;								// precise number of steps in this segment
		seg_num_steps[k] += seg_num_steps_err;													// account for rounding errors from last segment
		seg_num_steps_int[k] = (int)round(seg_num_steps[k]);									// actual number of steps in this segment
		if (seg_num_steps_int[k] < 1) {
			j++;
			continue;
		}
		seg_num_steps_err = seg_num_steps[k] - seg_num_steps_int[k];							// rounding error of this segment
		//-------------------------------------------------------------------

		//-- Get Time Between Steps -----------------------------------------		
		seg_step_time[k] = seg_time[k] / (fabs(z[i + j] - z[i]) * _motor_res_z);				// precise initial time between setps in us in this segment
		seg_step_time[k] += seg_step_time_err;													// account for rounding errors from last segment
		seg_step_time_int[k] = (int)round(seg_step_time[k]);									// actual time between steps in us in this segment
		if (seg_step_time_int[k] < 1) {
			//sprintf(msg, "z-motion: seg_step_time_int < 1");
			//error(msg);
		}
		seg_step_time_err = seg_step_time[k] - seg_step_time_int[k];							// rounding error of this segment
		//-------------------------------------------------------------------

		seg_z[k] = z[i];
		i += j;
		j = 1;
		k++;
	}


	//-------------------------------------------------------------------
	// allocate memory
	//-------------------------------------------------------------------
	num_seg = k;		// This is the actual number of segments		
	*_z_motion_len = num_seg + num_seg + 2;
	//-------------------------------------------------------------------	
	//*_z_motion = (double*)calloc(*_z_motion_len, sizeof(double));
	//if (*_z_motion == NULL) {
	//	//error("ERROR: calc motion: calloc");
	//	return -1;
	//}
	z_motion_uint = (unsigned int *)calloc(*_z_motion_len, sizeof(unsigned int));
	if (z_motion_uint == NULL) {
		//error("ERROR: calc motion: calloc");
		return -1;
	}
	//-------------------------------------------------------------------

	if (num_seg > 0) {																				// can be 0 if there is no motion
		// claculate change of time between steps 'seg_delta_step_time_int'
		for (i = 0; i < num_seg; i++) {
			seg_num_steps[i] = fabs(z[i + 1] - z[i]) * _motor_res_z;								// precise number of steps in this segment
			seg_step_time[i] = seg_time[i] / seg_num_steps[i];										// precise initial time between setps in us in this segment
		}
		for (i = 0; i < num_seg - 1; i++) {
			seg_delta_step_time[i] = (seg_step_time[i + 1] - seg_step_time[i]) / seg_num_steps[i];	// precise detlta_step_time in in us in this segment
			seg_delta_step_time[i] += seg_delta_step_time_err;										// account for rounding errors from last segment
			seg_delta_step_time_int[i] = (int)round(seg_delta_step_time[i]);						// actual delta_setp_time in us in this segment
			seg_delta_step_time_err = seg_delta_step_time[i] - seg_delta_step_time_int[i];			// rounding error of this segment
		}
		// calculate the last segment	
		seg_delta_step_time_int[num_seg - 1] = 0;
		//-------------------------------------------------------------------
	}


	//-------------------------------------------------------------------
	// verify z_motion
	//-------------------------------------------------------------------
	gen_steps = 0;
	gen_time = 0;
	seg_time_int = 0;
	target_steps = fabs(z[_len - 1] - z[0]) * _motor_res_z;
	target_time = fabs(_time[_len - 1] - _time[0]);
	//-------------------------------------------------------------------
	for (i = 0; i < num_seg; i++) {		
		seg_time_int = (double)seg_num_steps_int[i] * (double)seg_step_time_int[i];
		seg_time_int +=  0.5 * seg_delta_step_time_int[i] * ((seg_num_steps_int[i] - 1.0) * (seg_num_steps_int[i] - 1.0) + (seg_num_steps_int[i] - 1.0));
		
		gen_steps += seg_num_steps_int[i];
		gen_time += seg_time_int;
	}
	gen_time /= 1000000.0;
	//-------------------------------------------------------------------
	//sprintf(msg, "Z Segments:\t%d", num_seg);
	//debug(msg);	
	//sprintf(msg, "Z Target Steps:\t%.4f", target_steps);
	//debug(msg);
	//sprintf(msg, "Z Gen Steps:\t%.4f", gen_steps);
	//debug(msg);
	//sprintf(msg, "Z Error Steps:\t%.4f", gen_steps - target_steps);
	//debug(msg);
	//sprintf(msg, "Z Target Time:\t%.4f", target_time);
	//debug(msg);
	//sprintf(msg, "Z Actual Time:\t%.4f", gen_time);
	//debug(msg);
	//sprintf(msg, "Z Error Time:\t%.4f", target_time - gen_time);
	//debug(msg);
	//-------------------------------------------------------------------

	

	//-------------------------------------------------------------------
	// generate z_motion
	//-------------------------------------------------------------------
	// Header
	z_motion_uint[0] = (unsigned int)(num_seg & 0x1fff);														// 13 bits						bit 0 - 12	number of segments;	
	//z_motion_uint[0] |= (1 << 31);																			// 1 bit						bit 31		initial direction: 0 - CW, 1 - CCW
	z_motion_uint[1] = 0;

	for (i = 0; i < num_seg; i++) {
		z_motion_uint[2 * i + 2] |= (unsigned int)(seg_num_steps_int[i] - 1) & 0x7fffff;						// 23 bits						bit 0 - 22
		z_motion_uint[2 * i + 2] |= (((unsigned int)(seg_step_time_int[i] - 1) & 0x1ff) << 23);					// 9 least significant bits		bit 23 - 31
		z_motion_uint[2 * i + 3] |= ((unsigned int)(seg_step_time_int[i] - 1) >> 9) & 0x7ff;					// 11 most significant bits		bit 0 - 10

		if (seg_delta_step_time_int[i] < 0) {
			z_motion_uint[2 * i + 3] |= (((unsigned int)(-1 * seg_delta_step_time_int[i]) & 0xfffff) << 11);	// 20 bits						bit 11 - 30
			z_motion_uint[2 * i + 3] |= (1 << 31);																// 1 bit						bit 31
		}
		else {
			z_motion_uint[2 * i + 3] |= (((unsigned int)(seg_delta_step_time_int[i]) & 0xfffff) << 11);			// 20 bits						bit 11 - 30
		}		
	}	
	//----------------------------------------------------------------------------------------------------------------------------------------------------------
	for (i = 0; i < *_z_motion_len; i++) {
		_z_motion[i] = (double)z_motion_uint[i];
	}
	//----------------------------------------------------------------------------------------------------------------------------------------------------------	


	

	free(phi);
	free(z);
	free(seg_time);
	free(seg_phi);
	free(seg_z);
	free(seg_num_steps);
	free(seg_step_time);
	free(seg_delta_step_time);
	free(seg_num_steps_int);
	free(seg_step_time_int);
	free(seg_delta_step_time_int);
	free(phi_motion_uint);
	free(z_motion_uint);	

	return 1;
}





int convert_energy_to_angle(double _energy, double *_angle, double _d_spacing)
{

	double low_threshold = H_PLANCK * C_LIGHT / (PI * Q_E * _d_spacing);

	if (_energy < low_threshold)
		return -1;

	*_angle = asin(H_PLANCK * C_LIGHT / (2.0 * _d_spacing * Q_E * _energy)) * 180.0 / PI;


	return 1;
}
int convert_angle_to_energy(double _angle, double *_energy, double _d_spacing)
{

	if (_angle <= 0 || _angle >= 90.0)
		return -1;

	*_energy = H_PLANCK * C_LIGHT / (2.0 * _d_spacing * Q_E * sin(_angle * PI / 180.0));

	return 1;
}




