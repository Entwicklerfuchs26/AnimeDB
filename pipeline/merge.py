"""Schichten (wikidata/ann/manami) zu EINER Liste zusammenfuehren, Dubletten ueber Cross-IDs erkennen.
Aufruf: python pipeline/merge.py out.jsonl in1.jsonl in2.jsonl ...
Vorrang je Feld (siehe PRIO). Fallback-Abgleich ueber (normalisierter Titel, Jahr, Typ) nur wenn eindeutig."""
from __future__ import annotations

import datetime as dt
import json
import re
import sys
from collections import defaultdict

ID_KEYS = ["wikidata", "anilist", "mal", "kitsu", "anidb", "anisearch", "ann"]
PRIO = {  # Reihenfolge der Schichten je Feld (erste nicht-leere gewinnt)
    "title": ["wikidata", "ann", "manami"], "type": ["wikidata", "ann", "manami"],
    "studios": ["wikidata", "ann", "manami"], "genres": ["ann", "manami", "wikidata"],
    "episodes": ["wikidata", "manami", "ann"], "website": ["wikidata", "ann", "manami"],
    "season": ["manami", "wikidata", "ann"],
}


SEQUEL = re.compile(r"\bseason \d+\b|\b\d+(?:st|nd|rd|th) season\b|第\d+期", re.I)


def clean_genre(g: str) -> str:
    """Wikidata-Genrelabels vereinheitlichen („science fiction anime and manga“ → „science fiction“)."""
    g = re.sub(r"\s+(anime and manga|anime|manga|film|films)$", "", g.strip().lower())
    return g


def norm(t: str | None) -> str:
    return re.sub(r"[^a-z0-9]+", "", (t or "").lower())


class UF:
    def __init__(self) -> None:
        self.p: dict[int, int] = {}

    def find(self, x: int) -> int:
        self.p.setdefault(x, x)
        while self.p[x] != x:
            self.p[x] = self.p[self.p[x]]
            x = self.p[x]
        return x

    def union(self, a: int, b: int) -> None:
        self.p[self.find(a)] = self.find(b)


def layer(r: dict) -> str:
    return (r.get("layers") or ["wikidata" if r["id"].startswith("oadb:wd") else "ann" if r["id"].startswith("oadb:ann") else "manami"])[0]


def year_of(r: dict) -> str | None:
    s = r.get("start_date")
    return s[:4] if s else None


def precision(s: str | None) -> int:
    return len(s) if s else 0


def status_of(start: str | None, end: str | None, typ: str, fallback: str) -> str:
    today = dt.date.today().isoformat()
    if not start:
        return fallback
    if len(start) == 4 and start > today[:4]:
        return "announced"
    if start > today:
        return "upcoming"
    if end and end <= today:
        return "finished"
    if typ == "movie":
        return "finished"
    return fallback if fallback in ("finished", "airing") and len(start) == 4 else "airing" if not end else "finished"


def main() -> None:
    out, files = sys.argv[1], sys.argv[2:]
    recs: list[dict] = []
    for fn in files:
        for line in open(fn):
            r = json.loads(line)
            r["_layer"] = layer(r)
            if r["_layer"] == "wikidata":
                r["genres"] = sorted({clean_genre(g) for g in r.get("genres", []) if g})
            recs.append(r)
    uf = UF()
    owner: dict[tuple, int] = {}
    for i, r in enumerate(recs):
        uf.find(i)
        for k in ID_KEYS:
            v = r["ids"].get(k)
            if v is None:
                continue
            key = (k, v)
            if key in owner:
                uf.union(i, owner[key])
            else:
                owner[key] = i
    # Fallback: Titel+Jahr+Typ, nur wenn eindeutig und noch in verschiedenen Gruppen
    idx: dict[tuple, set[int]] = defaultdict(set)
    for i, r in enumerate(recs):
        y, t = year_of(r), r["type"]
        for name in [r["title"].get("en")] + list(r["title"].get("synonyms") or [])[:6]:
            n = norm(name)
            if len(n) >= 6 and y:
                idx[(n, y, t)].add(uf.find(i))
    fb = 0
    for key, groups in idx.items():
        if len(groups) == 2:  # genau zwei Gruppen -> eindeutig genug
            a, b = list(groups)
            uf.union(a, b)
            fb += 1
    groups: dict[int, list[dict]] = defaultdict(list)
    for i, r in enumerate(recs):
        groups[uf.find(i)].append(r)
    today = dt.date.today().isoformat()
    merged: list[dict] = []
    for g in groups.values():
        by = {}
        for r in sorted(g, key=lambda r: ["wikidata", "ann", "manami"].index(r["_layer"]) if r["_layer"] in ("wikidata", "ann", "manami") else 9):
            by.setdefault(r["_layer"], r)
        def pick(field: str, getter):
            for ly in PRIO.get(field, ["wikidata", "ann", "manami"]):
                if ly in by:
                    v = getter(by[ly])
                    if v:
                        return v, ly
            return None, None
        ids: dict = {}
        for r in g:
            for k, v in r["ids"].items():
                ids.setdefault(k, v)
        title, _ = pick("title", lambda r: r["title"].get("en"))
        syn = sorted({s for r in g for s in (r["title"].get("synonyms") or [])} - {title})
        ja = next((r["title"]["ja"] for r in g if r["title"].get("ja")), None)
        typ, _ = pick("type", lambda r: r["type"] if r["type"] != "unknown" else None)
        fs_ty = None
        if not typ:
            # Fortsetzungen im Titel ("season 3", "2nd season", "第3期") sind praktisch immer TV-Serien
            tt = " ".join(filter(None, [title, ja]))
            if SEQUEL.search(tt):
                typ, fs_ty = "tv", "heuristic"
        typ = typ or "unknown"
        start = max((r.get("start_date") for r in g if r.get("start_date")), key=precision, default=None)
        end = next((r["end_date"] for r in g if r.get("end_date")), None)
        studios, fs_st = pick("studios", lambda r: r["studios"])
        genres, fs_ge = pick("genres", lambda r: r["genres"])
        eps, fs_ep = pick("episodes", lambda r: r.get("episodes"))
        site, fs_ws = pick("website", lambda r: r.get("website"))
        season, fs_se = pick("season", lambda r: r.get("season"))
        fallback = next((r["status"] for r in g if r["status"] != "unknown"), "unknown")
        src: list[dict] = []
        seen = set()
        for r in g:
            for s in r["sources"]:
                k = (s["name"], s.get("url"))
                if k not in seen:
                    seen.add(k); src.append(s)
        base = by.get("wikidata") or by.get("ann") or by.get("manami")
        merged.append({
            "id": base["id"], "type": typ,
            "title": {"en": title, "ja": ja, "romaji": None, "synonyms": syn[:20]},
            "status": status_of(start, end, typ, fallback), "start_date": start, "end_date": end, "episodes": eps,
            "season": season, "studios": studios or [], "genres": genres or [], "website": site,
            "synopsis": next((r["synopsis"] for r in g if r.get("synopsis")), None),
            "ids": ids, "sources": src, "layers": sorted(by),
            "field_sources": {k: v for k, v in {"type": fs_ty, "studios": fs_st, "genres": fs_ge, "episodes": fs_ep, "website": fs_ws, "season": fs_se}.items() if v},
            "updated_at": max(r["updated_at"] for r in g),
        })
    merged.sort(key=lambda r: (r["start_date"] or "", r["id"]), reverse=True)
    with open(out, "w") as f:
        for r in merged:
            f.write(json.dumps(r, ensure_ascii=False) + "\n")
    multi = sum(1 for r in merged if len(r["layers"]) > 1)
    print(f"{len(recs)} Eingangs-Einträge → {len(merged)} Titel ({multi} aus mehreren Schichten verknüpft, {fb} Titel-Jahr-Treffer) → {out}")


if __name__ == "__main__":
    main()
