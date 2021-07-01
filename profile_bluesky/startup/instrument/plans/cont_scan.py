import logging

logger = logging.getLogger()
            
import bluesky.plan_stubs as bps

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