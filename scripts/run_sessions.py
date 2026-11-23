"""Batch runner: prompts -> sessions/*. Produces >=15 results.json incl. failures."""
from __future__ import annotations

import json
from pathlib import Path

from backend.engine.schema import Clip, create_timeline
from backend.engine.session import MockLLM, run_session
from backend.engine.words import ingest_transcript

PROMPTS = [
    ("cut silences, keep demo", '{"version":"v1","response":"results","ops":[{"op":"cut","start":0,"end":1}]}'),
    ("tighten intro", '{"version":"v1","response":"results","ops":[{"op":"cut","start":0,"end":0.5}]}'),
    ("speed up middle 2x", '{"version":"v1","response":"results","ops":[{"op":"speed","start":4,"end":6,"factor":2}]}'),
    ("caption ending", '{"version":"v1","response":"results","ops":[{"op":"caption","start":8,"end":10,"text":"thanks","style":"subtitle"}]}'),
    ("keep only demo", '{"version":"v1","response":"results","ops":[{"op":"keep","start":3,"end":7}]}'),
    ("make it punchy", "vague"),
    ("30s short?", "vague"),
    ("remove person", "unsafe"),
    ("translate voice", "unsafe"),
    ("bad json test", "{not json"),
    ("overflow test", '{"version":"v1","response":"results","ops":[{"op":"cut","start":0,"end":999}]}'),
    ("extra key test", '{"version":"v1","ops":[{"op":"cut","start":0,"end":1}],"evil":1}'),
    ("placeholder test", '{"version":"v1","response":"results","ops":[{"op":"caption","start":1,"end":2,"text":"{placeholder}"}]}'),
    ("hook short", '{"version":"v1","response":"results","ops":[{"op":"keep","start":2,"end":9}]}'),
    ("undo that", '{"version":"v1","response":"clarify","clarify_question":"Which step to undo?","ops":[]}'),
    ("restore v1", '{"version":"v1","response":"clarify","clarify_question":"Which version?","ops":[]}'),
]


def main(out: str = "sessions") -> None:
    outp = Path(out)
    data = json.loads(Path("backend/tests/fixtures/words_10s.json").read_text())
    words = ingest_transcript(data, 30, 1)
    base = create_timeline(30, 1, [Clip("c1", "src", 0, 300)], words=words)
    script = {}
    for prompt, canned in PROMPTS:
        script[prompt.split()[0]] = canned
    # map vague/unsafe explicitly
    llm = MockLLM({
        "cut": PROMPTS[0][1], "tighten": PROMPTS[1][1], "speed": PROMPTS[2][1],
        "caption": PROMPTS[3][1], "keep": PROMPTS[4][1], "hook": PROMPTS[13][1],
        "make": '{"version":"v1","response":"clarify","clarify_question":"What target duration?","ops":[]}',
        "30s": '{"version":"v1","response":"clarify","clarify_question":"Full or Short?","ops":[]}',
        "remove": '{"version":"v1","response":"reject","rejection_reason":"cannot remove person","ops":[]}',
        "translate": '{"version":"v1","response":"reject","rejection_reason":"voice clone out of scope","ops":[]}',
        "bad": "{not json", "overflow": PROMPTS[10][1], "extra": PROMPTS[11][1],
        "placeholder": PROMPTS[12][1], "undo": PROMPTS[14][1], "restore": PROMPTS[15][1],
    })
    for i, (prompt, _) in enumerate(PROMPTS):
        run_session(outp / f"run_{i:02d}", prompt, base, llm)
    print(f"wrote {len(PROMPTS)} sessions to {outp}")


if __name__ == "__main__":
    main()
