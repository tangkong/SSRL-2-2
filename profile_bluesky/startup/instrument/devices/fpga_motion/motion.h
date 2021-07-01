//------------------------------------------------------------------------------------------------------------------
// DEFINITIONS
//------------------------------------------------------------------------------------------------------------------
#define PI			3.14159265358979323846
#define H_PLANCK	6.62607004e-34
#define C_LIGHT		299792458
#define Q_E			1.60217662e-19
//------------------------------------------------------------------------------------------------------------------


//------------------------------------------------------------------------------------------------------------------
// INCLUDES
//------------------------------------------------------------------------------------------------------------------
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <math.h>
//------------------------------------------------------------------------------------------------------------------


typedef struct FpgaTrigger
{
	double			*time;
	double			*energy;
	unsigned int	timeEnergyLen;
	
	double			*trigger;
	unsigned int	*triggerLen;		// single Element
	
	int				*lastErrorCode;		// single Element
} FpgaTrigger;

typedef struct FpgaMotion
{
	double			*time;
	double			*energy;
	unsigned int	timeEnergyLen;
	
	double 			crystalD;
	double			crystalGap;
	double 			motorResPhi;
	double 			motorResZ;
	
	double			*motionPhi;
	unsigned int	*motionPhiLen;		// single Element
	
	double			*motionZ;				
	unsigned int	*motionZLen;		// single Element
	
	int				*lastErrorCode;		// single Element
} FpgaMotion;




//------------------------------------------------------------------------------------------------------------------
// PROTOTYPES
//------------------------------------------------------------------------------------------------------------------
void CalcTrgger(FpgaTrigger *fpgaTrigger);
void CalcMotion(FpgaMotion *fpgaMotion);


int calc_trigger(		double *_time,
						double *_energy,
						unsigned int _len,
						double *_trigger,
						unsigned int *_trigger_len);

int calc_motion(		double *_time,
						double *_energy,
						unsigned int _len,
						double _crystal_lattice,
						double _crystal_gap,
						double _motor_res_phi,
						double _motor_res_z,
						double *_phi_motion,
						unsigned int *_phi_motion_len,
						double *_z_motion,
						unsigned int *_z_motion_len);
						
//------------------------------------------------------------------------------------------------------------------
int convert_energy_to_angle(double _energy, double *_angle, double _d_spacing);
int convert_angle_to_energy(double _angle, double *_energy, double _d_spacing);
//------------------------------------------------------------------------------------------------------------------