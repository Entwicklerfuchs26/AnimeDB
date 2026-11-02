"""Erzeugt den oeffentlichen Release aus data/anime.jsonl.
Regeln (siehe README „Rechtliches"): Felder/Eintraege nach Herkunft filtern.
  ANN (Anime News Network) wird NIE uebernommen: keine Inhalte, keine IDs, keine Quellen (alle Rechte vorbehalten).
  --allow-manami   manami-Schicht behalten (aggregiert MAL/AniList/Kitsu/AniDB → Risiko!)
Standard: STRENG — nur Wikidata (CC0) + Wikipedia-Synopsen (CC BY-SA, mit Quelle).
Aufruf: python pipeline/export_public.py in.jsonl out.jsonl [--allow-manami]"""
from __future__ import annotations

import json
import sys


def main() -> None:
    src, out = sys.argv[1], sys.argv[2]
    allow_mn = "--allow-manami" in sys.argv
    kept = dropped = 0
    with open(out, "w") as f:
        for line in open(src):
            r = json.loads(line)
            fs = r.get("field_sources", {})
            if r["layers"] == ["ann"]:
                dropped += 1
                continue  # reine ANN-Eintraege weglassen
            if not allow_mn and r["layers"] == ["manami"]:
                dropped += 1
                continue  # reine manami-Eintraege weglassen
            for fld in ("studios", "genres", "website", "episodes", "season"):
                src_ = fs.get(fld)
                if src_ == "ann" or (src_ == "manami" and not allow_mn):
                    r[fld] = [] if fld in ("studios", "genres") else None
                    fs.pop(fld, None)
            r["field_sources"] = fs
            keep_src = [s for s in r["sources"] if (s["name"] == "Wikidata") or (s["name"] == "Wikipedia")
                        or (s["name"] == "anime-offline-database" and allow_mn)]
            r["sources"] = [s for s in keep_src if s["name"] != "anime-offline-database" or allow_mn]
            r["layers"] = [l for l in r["layers"] if l == "wikidata" or (l == "manami" and allow_mn)] or ["wikidata"]
            (r.get("ids") or {}).pop("ann", None)
            f.write(json.dumps(r, ensure_ascii=False) + "\n")
            kept += 1
    print(f"Öffentlicher Export: {kept} Einträge, {dropped} nur-manami-Einträge weggelassen → {out}")


if __name__ == "__main__":
    main()
