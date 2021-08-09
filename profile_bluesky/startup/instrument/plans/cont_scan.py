import logging
logger = logging.getLogger()
            
import bluesky.plan_stubs as bps
from bluesky.preprocessors import inject_md_decorator
from ..devices.stages import px, py

def fly_plan(flyer, *, md=None):
    """
    Perform a fly scan with one or more 'flyers'.
    Slight modification to bluesky.plans.fly, takes only single flyer

    Parameters
    ----------
    flyers : collection
        objects that support the flyer interface
    md : dict, optional
        metadata

    Yields
    ------
    msg : Msg
        'kickoff', 'wait', 'complete, 'wait', 'collect' messages

    See Also
    --------
    :func:`bluesky.preprocessors.fly_during_wrapper`
    :func:`bluesky.preprocessors.fly_during_decorator`
    """
    uid = yield from bps.open_run(md)
    
    yield from bps.kickoff(flyer, wait=True)
    complete_status = yield from bps.complete(flyer, wait=False)
    while not complete_status.done:
        yield from bps.sleep(0.1) # rate limit @ 40Hz
        yield from bps.collect(flyer)
        print('.')
    # one last collect?
    yield from bps.collect(flyer)
    print('fly completed, unstaging')
    flyer.unstage()
    yield from bps.close_run()
    return uid

@inject_md_decorator({'macro_name': 'fly_list'})
def fly_list(flyer, locs, md={}):
    uids = []
    for i in range(len(locs[0])):
        yield from bps.mv(px, locs[0][i])
        yield from bps.mv(py, locs[1][i])
        uid = yield from fly_plan(flyer, md={'x':locs[0][i], 'y':locs[1][i]})
        print(f'x, y: {locs[0][i]}, {locs[1][i]}')
        print(f'pos: {i}')
        # check if dxp's are ok
        yield from bps.sleep(10)
        while ( (flyer.dxp1.start_acquire.get() !=0 ) or 
                (flyer.dxp2.start_acquire.get() !=0 ) or
                (flyer.dxp1.start_acquire.get() !=0 ) ):
            print('dxps not ready')
            yield from bps.sleep(10)
        uids.append(uid)

    return uids
