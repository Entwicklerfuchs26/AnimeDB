"""Wikidata → einheitliche Anime-Einträge (Neuzugaenge ab einem Datum). Wikidata = CC0."""
from __future__ import annotations

import datetime as dt
import json
import os
import sys

import httpx

H = {"User-Agent": f"orbit-anime-db/0.1 (research prototype; {os.environ.get('OADB_CONTACT', 'contact-not-set')})"}
cl = httpx.Client(headers=H, timeout=90, follow_redirects=True)
SINCE = sys.argv[1] if len(sys.argv) > 1 else "2026-07-01"  # Datum oder "all"
OUT = sys.argv[2] if len(sys.argv) > 2 else "data/wikidata_new.jsonl"

TYPE_Q = {  # Wikidata-Klassen → unser Typ (Reihenfolge = Prioritaet)
    "Q63952888": "tv", "Q20650540": "movie", "Q1107": None,  # Q1107 = anime (generisch)
    "Q220898": "ova", "Q1257444": "ona", "Q104604700": "ona",
}
EXT = {  # Wikidata-Property → ids-Schluessel
    "P8729": "anilist", "P4086": "mal", "P1985": "ann", "P5646": "anidb", "P4983": "tmdb_tv", "P345": "imdb",
}


def sparql(q: str) -> list[dict]:
    r = cl.get("https://query.wikidata.org/sparql", params={"query": q}, headers={"Accept": "application/sparql-results+json"})
    r.raise_for_status()
    return r.json()["results"]["bindings"]


def entities(ids: list[str], props: str) -> dict:
    out = {}
    for k in range(0, len(ids), 50):
        r = cl.get("https://www.wikidata.org/w/api.php", params={"action": "wbgetentities", "ids": "|".join(ids[k:k + 50]), "props": props, "languages": "en|ja", "sitefilter": "enwiki", "format": "json"})
        r.raise_for_status()
        out.update(r.json()["entities"])
    return out


def val(c: dict, p: str):
    return [x["mainsnak"]["datavalue"]["value"] for x in c.get(p, []) if "datavalue" in x.get("mainsnak", {})]


def iso(t: dict | None) -> str | None:
    if not t:
        return None
    s, prec = t["time"].lstrip("+"), t["precision"]
    d = s[:10]
    return d[:4] if prec <= 9 else d[:7] if prec == 10 else d


def main() -> None:
    if SINCE == "all":
        q = "SELECT DISTINCT ?i WHERE { ?i wdt:P31/wdt:P279* wd:Q1107 }"
    else:
        q = f'''SELECT DISTINCT ?i WHERE {{ ?i wdt:P31/wdt:P279* wd:Q1107 . ?i wdt:P577|wdt:P580 ?d .
            FILTER(?d >= "{SINCE}T00:00:00Z"^^xsd:dateTime) }}'''
    ids = [b["i"]["value"].rsplit("/", 1)[1] for b in sparql(q)]
    ents = entities(ids, "claims|labels|aliases|descriptions|sitelinks")
    # Referenzierte Entitaeten (Studio, Genre, Typ) auf Labels aufloesen
    refs = set()
    for e in ents.values():
        for p in ("P272", "P136", "P31"):
            refs.update(v["id"] for v in val(e.get("claims", {}), p) if isinstance(v, dict))
    lab = {k: (v["labels"].get("en") or {}).get("value") for k, v in entities(sorted(refs), "labels").items()}
    now = dt.datetime.now(dt.timezone.utc).strftime("%Y-%m-%dT%H:%MZ")
    today = dt.date.today().isoformat()
    n = 0
    with open(OUT, "w") as f:
        for q_, e in ents.items():
            c = e.get("claims", {})
            classes = {v["id"] for v in val(c, "P31") if isinstance(v, dict)}
            typ = next((TYPE_Q[k] for k in TYPE_Q if k in classes and TYPE_Q[k]), None) or "unknown"
            start = iso(next(iter(val(c, "P580") or val(c, "P577")), None))
            end = iso(next(iter(val(c, "P582")), None))
            if not start and SINCE != "all":
                continue
            start = start or None
            status = "unknown" if not start else "finished" if (end and end <= today) else "airing" if start <= today else "upcoming"
            if start and len(start) == 4 and start > today[:4]:
                status = "announced"
            if typ == "movie" and status == "airing":
                status = "finished"  # Film: Premiere vorbei = erschienen
            ids_ = {"wikidata": q_}
            wp = (e.get("sitelinks") or {}).get("enwiki", {}).get("title")
            if wp:
                ids_["wikipedia_en"] = wp
            for p, k in EXT.items():
                v = next(iter(val(c, p)), None)
                if v:
                    ids_[k] = int(v) if v.isdigit() and k not in ("imdb",) else v
            titles = [v["text"] for v in val(c, "P1476") if isinstance(v, dict)]
            en = (e["labels"].get("en") or {}).get("value") or (titles[0] if titles else None)
            ja = (e["labels"].get("ja") or {}).get("value")
            eps = next(iter(val(c, "P1113")), None)
            site = next(iter(val(c, "P856")), None)
            rec = {
                "id": f"oadb:wd:{q_}", "type": typ,
                "title": {"en": en, "ja": ja, "romaji": None, "synonyms": [a["value"] for a in e.get("aliases", {}).get("en", [])]},
                "status": status, "start_date": start, "end_date": end,
                "episodes": int(float(eps["amount"])) if isinstance(eps, dict) else None,
                "studios": sorted({lab.get(v["id"]) for v in val(c, "P272") if isinstance(v, dict) and lab.get(v["id"])}),
                "genres": sorted({lab.get(v["id"]) for v in val(c, "P136") if isinstance(v, dict) and lab.get(v["id"])}),
                "website": site, "synopsis": None, "ids": ids_,
                "sources": [{"name": "Wikidata", "url": f"https://www.wikidata.org/wiki/{q_}", "retrieved": now, "license": "CC0"}],
                "updated_at": now,
            }
            f.write(json.dumps(rec, ensure_ascii=False) + "\n")
            n += 1
    print(f"{n} Einträge ab {SINCE} → {OUT}")


if __name__ == "__main__":
    main()
