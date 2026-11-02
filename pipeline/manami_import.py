"""manami anime-offline-database (ODbL+DbCL) → einheitliches Schema.
Aufruf:  python pipeline/manami_import.py <anime-offline-database-minified.json> [out.jsonl]
Download: https://github.com/manami-project/anime-offline-database/releases (…-minified.json.zst)
Hinweis: manami aggregiert MAL/Kitsu/AniList/AniDB u.a.; die Lizenz (ODbL+DbCL) gilt fuer die Zusammenstellung des Autors,
die Bedingungen der Ursprungsquellen sind nicht geprueft (siehe NOTICE.md). Es werden nur nuechterne Metadaten uebernommen."""
from __future__ import annotations

import json
import re
import sys

TYPE = {"TV": "tv", "MOVIE": "movie", "OVA": "ova", "ONA": "ona", "SPECIAL": "special"}
STATUS = {"FINISHED": "finished", "ONGOING": "airing", "UPCOMING": "upcoming"}
ID_PATTERNS = [
    ("anilist", r"anilist\.co/anime/(\d+)"), ("mal", r"myanimelist\.net/anime/(\d+)"), ("kitsu", r"kitsu\.(?:app|io)/anime/(\d+)"),
    ("anidb", r"anidb\.net/anime/(\d+)"), ("anisearch", r"anisearch\.com/anime/(\d+)"),
]


def convert(e: dict, retrieved: str) -> dict:
    ids: dict = {}
    for url in e.get("sources", []):
        for k, pat in ID_PATTERNS:
            m = re.search(pat, url)
            if m:
                ids[k] = int(m.group(1))
    if not ids:
        ids["manami"] = e["title"][:60]
    se = e.get("animeSeason") or {}
    year = se.get("year") or None
    season = (se.get("season") or "").lower() or None
    if season == "undefined":
        season = None
    eps = e.get("episodes") or None
    return {
        "id": "oadb:mn:" + (f"al{ids['anilist']}" if "anilist" in ids else f"mal{ids['mal']}" if "mal" in ids else f"kt{ids['kitsu']}" if "kitsu" in ids else re.sub(r"\W+", "", e["title"].lower())[:40]),
        "type": TYPE.get(e.get("type"), "unknown"),
        "title": {"en": e["title"], "ja": None, "romaji": None, "synonyms": e.get("synonyms", [])},
        "status": STATUS.get(e.get("status"), "unknown"),
        "start_date": str(year) if year else None, "end_date": None, "episodes": eps,
        "season": {"season": season, "year": year} if (season or year) else None,
        "studios": sorted(set(e.get("studios", []))), "genres": sorted(set(e.get("tags", []))),
        "website": None, "synopsis": None, "ids": ids,
        "sources": [{"name": "anime-offline-database", "url": "https://github.com/manami-project/anime-offline-database", "retrieved": retrieved, "license": "ODbL-1.0"}],
        "layers": ["manami"], "field_sources": {k: "manami" for k in ("studios", "genres", "episodes", "status")},
        "updated_at": retrieved,
    }


def main() -> None:
    src = sys.argv[1]
    out = sys.argv[2] if len(sys.argv) > 2 else "data/manami.jsonl"
    d = json.load(open(src))
    retrieved = d.get("lastUpdate", "unknown")
    n = 0
    seen: set[str] = set()
    with open(out, "w") as f:
        for e in d["data"]:
            r = convert(e, retrieved)
            if r["id"] in seen:  # seltene Kollision der Hilfs-ID
                r["id"] += f"-{n}"
            seen.add(r["id"])
            f.write(json.dumps(r, ensure_ascii=False) + "\n")
            n += 1
    print(f"{n} manami-Einträge → {out} (Stand {retrieved})")


if __name__ == "__main__":
    main()
