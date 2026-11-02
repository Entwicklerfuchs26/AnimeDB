"""Prueft jede Zeile einer JSONL-Datei gegen schema/anime.schema.json und einige Zusatzregeln.
Aufruf: python pipeline/validate.py data/anime.jsonl   (Exit-Code 1 bei Fehlern — fuer CI)"""
from __future__ import annotations

import json
import re
import sys
from pathlib import Path

try:
    import jsonschema
except ImportError:  # CI installiert es; lokal Hinweis
    sys.exit("pip install jsonschema")

SCHEMA = json.load(open(Path(__file__).resolve().parent.parent / "schema" / "anime.schema.json"))
DATE = re.compile(r"^\d{4}(-\d{2}(-\d{2})?)?$")
BANNED = ("anilist.co", "myanimelist.net")  # Beitragsregel: keine kopierten Texte dieser Quellen als Synopsis-Quelle


def main() -> int:
    path = sys.argv[1]
    v = jsonschema.Draft202012Validator(SCHEMA)
    errors = 0
    ids = set()
    n = 0
    for ln, line in enumerate(open(path), 1):
        r = json.loads(line)
        n += 1
        for e in v.iter_errors(r):
            errors += 1
            print(f"{path}:{ln} {r.get('id')}: {'/'.join(map(str, e.path))}: {e.message[:120]}")
        if r["id"] in ids:
            errors += 1; print(f"{path}:{ln} doppelte ID {r['id']}")
        ids.add(r["id"])
        for k in ("start_date", "end_date"):
            if r.get(k) and not DATE.match(r[k]):
                errors += 1; print(f"{path}:{ln} {r['id']}: {k} kein ISO-Datum: {r[k]}")
        sy = r.get("synopsis")
        if sy:
            blob = json.dumps(sy).lower()
            if any(b in blob for b in BANNED):
                errors += 1; print(f"{path}:{ln} {r['id']}: Synopsis stammt aus gesperrter Quelle (AniList/MAL)")
            if not sy.get("license") or not sy.get("source"):
                errors += 1; print(f"{path}:{ln} {r['id']}: Synopsis ohne Quelle/Lizenz")
    print(f"{n} Einträge geprüft, {errors} Fehler")
    return 1 if errors else 0


if __name__ == "__main__":
    sys.exit(main())
