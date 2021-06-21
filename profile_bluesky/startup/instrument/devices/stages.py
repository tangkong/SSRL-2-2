"""
stages 
"""

__all__ = ['s_stage', 'px', 'py'] #, 'pz', 'th', 'vx', 'vy']

from ..framework import sd
from ..session_logs import logger
logger.info(__file__)

from ophyd import Component as Cpt, MotorBundle, EpicsMotor

class HiTpStage(MotorBundle):
    """HiTp Sample Stage"""
    #stage x, y
    px = Cpt(EpicsMotor, 'BL22:IMS:MOTOR1', kind='hinted', labels=('sample',))
    py = Cpt(EpicsMotor, 'BL22:IMS:MOTOR2', kind='hinted', labels=('sample',))

s_stage = HiTpStage('', name='s_stage')

class FPGABoxMotors(MotorBundle):
    """FPGA box motors"""
    


# measure stage status at beginning of every plan
sd.baseline.append(s_stage)

# convenience definitions 
px = s_stage.px
py = s_stage.py