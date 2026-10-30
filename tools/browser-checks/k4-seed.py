"""K4 Task 5: a fixture store for the browser checks.

The test fixtures' store (seed_store + seed_german), one scoped k3-trocr run on a
German page (one line re-read, the rest v1), page_lang rows so About lists pages by
language. Usage: .venv-w3/bin/python tools/browser-checks/k4-seed.py <store path>

The checks themselves: tools/browser-checks/k4-checks.mjs (Playwright, from a scratch
directory holding `npm install playwright axe-core`; deploy/README.md and STATUS.md K4).
"""

import json
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]  # the repository root
sys.path.insert(0, str(REPO))

from tests.conftest import W1, W3, seed_german, seed_store  # noqa: E402

from leibniz import db  # noqa: E402
from leibniz.pipeline import import_readings as I  # noqa: E402

out = Path(sys.argv[1])
for p in (out, out.with_name(out.name + "-wal"), out.with_name(out.name + "-shm")):
    p.unlink(missing_ok=True)
db.init_db(out).close()
seed_store(out)
seed_german(out)
page = f"{W3}:0001"
readings = out.with_suffix(".k3.jsonl")
readings.write_text(
    json.dumps({"line_id": f"{page}:000", "text": "Jch habe", "conf": 0.9}) + "\n",
    encoding="utf-8",
)
conn = db.init_db(out)
stats = I.import_readings(
    conn,
    readings_path=readings,
    page_ids=[page],
    model="k3-trocr@runs-615-epoch-5",
    reader="k3-trocr",
    write=True,
)
for seq in (1, 2):
    db.upsert_page_lang(
        conn, db.PageLangRow(page_id=f"{W3}:{seq:04d}", lang="de", score=0.8, n_tokens=40)
    )
db.upsert_page_lang(conn, db.PageLangRow(page_id=f"{W1}:0001", lang="la", score=0.9, n_tokens=50))
conn.commit()
conn.close()
print(f"seeded {out} run {stats.run_id} page {page}")
