import time
def start(seconds:int) -> dict:        # returns a timer dict
    return {"t0": time.time(), "d": seconds}

def remaining(t:dict) -> int:          # seconds left
    return max(0, int(t["d"] - (time.time() - t["t0"]))) 