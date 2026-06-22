import sys
import time
from datetime import datetime

from . import core

POLL = 1.5
RETRY_WINDOW = 20


def log(msg):
    print("[%s] %s" % (datetime.now().strftime("%H:%M:%S"), msg), flush=True)


def main():
    log("watching")
    present = False
    applied = False
    deadline = 0.0
    while True:
        cfg = core.load_config()
        here = core.find_target(cfg.get("controller_serial")) is not None

        if here and not present:
            present, applied = True, False
            deadline = time.time() + RETRY_WINDOW
        elif not here and present:
            present, applied = False, False
            log("disconnected")

        if present and not applied:
            code, msg = core.apply_from_config()
            if code == 0:
                log(msg)
                applied = True
            elif time.time() > deadline:
                log("gave up: " + msg)
                applied = True

        time.sleep(POLL)


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        pass
    except Exception as e:
        log("crashed: %s" % e)
        sys.exit(1)
