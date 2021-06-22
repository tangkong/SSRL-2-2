from bluesky.plans import fly, count
from bluesky.preprocessors import fly_during_decorator
from ophyd.signal import EpicsSignalRO

from ophyd.sim import det


data_pv = EpicsSignalRO('BL22:SCAN:MASTER.DATA', name='DATA')

def cs_dispatch_plan():
    print('c# plan')
    yield from count([det])


