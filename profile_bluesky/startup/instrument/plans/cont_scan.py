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

    yield from bps.close_run()
    return uid

@inject_md_decorator({'macro_name': 'fly_list'})
def fly_list(flyer, locs, md={}):
    uids = []
    for i in range(len(locs[0])):
        yield from bps.mv(px, locs[0][i])
        yield from bps.mv(py, locs[1][i])
        uid = yield from fly_plan(flyer, md={'x':locs[0][i], 'y':locs[1][i]})
        uids.append(uid)

    return uids