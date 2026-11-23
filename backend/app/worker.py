"""Worker entry (MVP stub): boots under compose; real arq tasks land with Phase 5 jobs.

Exits 0 and idles so `compose up` smoke passes without heavy queue deps.
"""
from __future__ import annotations

import logging
import time

log = logging.getLogger("worker")


def main() -> None:
    try:
        import arq  # type: ignore  # noqa: F401
        log.warning("arq installed but task modules not wired yet; idling")
    except ImportError:
        log.warning("arq not installed (MVP): worker idling; API serves inline")
    while True:
        time.sleep(60)


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    main()
