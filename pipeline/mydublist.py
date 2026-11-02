"""Synchro-Angaben (Dubs) aus MyDubList → Feld `dubs` pro Titel.
Quelle: https://github.com/Joelis57/MyDubList (Datensatz CC BY 4.0, nur Namensnennung noetig, siehe NOTICE.md).
Die Dub-Dateien fuehren MAL-IDs; Zuordnung zu unseren Titeln ueber ids.mal, sonst ueber ids.anilist
(per MyDubList-Mapping). Pro Sprache steht die beste Konfidenzstufe (very-high > high > normal > low).
Es werden nur IDs/Flags uebernommen — keine Texte, keine Fremd-IDs ausser den ohnehin vorhandenen.
Aufruf: python pipeline/mydublist.py in.jsonl out.jsonl"""
from __future__ import annotations

import datetime as dt
import json
import os
import sys

import httpx

BASE = "https://raw.githubusercontent.com/Joelis57/MyDubList/main/dubs/"
TIERS = ["very-high", "high", "normal", "low"]  # bestes zuerst
LANGS = [
    "german", "english", "spanish", "french", "italian", "portuguese", "japanese",
    "russian", "polish", "chinese", "korean", "arabic", "hungarian", "turkish", "dutch",
]
SOURCE = {
    "name": "MyDubList",
    "url": "https://mydublist.com",
    "license": "CC-BY-4.0",
    "attribution": "Dub data © MyDubList - https://mydublist.com - (CC BY 4.0)",
}
H = {"User-Agent": f"orbit-anime-db/0.1 (research prototype; {os.environ.get('OADB_CONTACT', 'contact-not-set')})"}


def fetch_dubs(cl: httpx.Client) -> dict[int, dict[str, str]]:
    """mal_id -> {sprache: beste_stufe}. Fehlende Dateien einer Nebensprache werden uebersprungen,
    Deutsch muss vollstaendig kommen (sonst Abbruch statt stiller Datenverlust)."""
    out: dict[int, dict[str, str]] = {}
    for lang in LANGS:
        for t in TIERS:
            r = cl.get(f"{BASE}confidence/{t}/dubbed_{lang}.json")
            if r.status_code == 404 and lang != "german":
                continue
            r.raise_for_status()
            for mid in r.json().get("dubbed", []):
                out.setdefault(int(mid), {}).setdefault(lang, t)  # erstes (beste Stufe) gewinnt
    return out


def fetch_anilist_to_mal(cl: httpx.Client) -> dict[int, int]:
    r = cl.get(BASE + "mappings/mappings_merged.jsonl", timeout=120)
    r.raise_for_status()
    m: dict[int, int] = {}
    for line in r.text.splitlines():
        try:
            o = json.loads(line)
        except Exception:
            continue
        if o.get("anilist_id") is not None and o.get("mal_id") is not None:
            m[int(o["anilist_id"])] = int(o["mal_id"])
    return m


def main() -> None:
    src, out = sys.argv[1], sys.argv[2]
    with httpx.Client(headers=H, timeout=90, follow_redirects=True) as cl:
        dubs = fetch_dubs(cl)
        a2m = fetch_anilist_to_mal(cl)
    today = dt.date.today().isoformat()
    n = de = 0
    with open(out, "w") as f:
        for line in open(src):
            r = json.loads(line)
            ids = r.get("ids") or {}
            d = dubs.get(int(ids["mal"])) if ids.get("mal") is not None else None
            if not d and ids.get("anilist") is not None:  # Rueckfall: AniList-ID -> MAL-ID laut MyDubList-Mapping
                m2 = a2m.get(int(ids["anilist"]))
                d = dubs.get(m2) if m2 is not None else None
            if d:
                r["dubs"] = {"languages": d, "source": "MyDubList"}
                r.setdefault("field_sources", {})["dubs"] = "mydublist"
                if not any(s.get("name") == "MyDubList" for s in r.setdefault("sources", [])):
                    r["sources"].append({"name": "MyDubList", "url": SOURCE["url"], "retrieved": today, "license": SOURCE["license"]})
                n += 1
                de += "german" in d
            f.write(json.dumps(r, ensure_ascii=False) + "\n")
    print(f"MyDubList: {n} Titel mit Synchro-Angabe ({de} mit deutscher Synchro) → {out}")


if __name__ == "__main__":
    main()
