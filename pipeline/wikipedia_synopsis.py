"""Kurzbeschreibung aus dem Wikipedia-Einleitungstext (en), CC BY-SA 4.0.
Nur fuer Titel mit `ids.wikipedia_en`. Max. ~900 Zeichen, an Satzgrenze gekuerzt. Quelle + Lizenz stehen im Eintrag.
Aufruf: python pipeline/wikipedia_synopsis.py in.jsonl out.jsonl"""
from __future__ import annotations

import json
import os
import re
import sys
import time
import urllib.parse

import httpx

H = {"User-Agent": f"orbit-anime-db/0.1 (research prototype; {os.environ.get('OADB_CONTACT', 'contact-not-set')})"}
cl = httpx.Client(headers=H, timeout=60)
LIMIT = 900


def trim(t: str) -> str:
    t = re.sub(r"\s+", " ", t).strip()
    if len(t) <= LIMIT:
        return t
    cut = t[:LIMIT]
    m = max(cut.rfind(". "), cut.rfind("! "), cut.rfind("? "))
    return cut[: m + 1] if m > 300 else cut.rsplit(" ", 1)[0] + " …"


def main() -> None:
    src, out = sys.argv[1], sys.argv[2]
    recs = [json.loads(l) for l in open(src)]
    cache_fn = "data/synopsis_cache.json"
    cache = json.load(open(cache_fn)) if os.path.exists(cache_fn) else {}
    for r in recs:  # Cache zuerst (Tageslauf soll Wikipedia nicht jedes Mal komplett abfragen)
        t = r["ids"].get("wikipedia_en")
        if t and not r.get("synopsis") and t in cache:
            r["synopsis"] = cache[t]
    todo = {r["ids"]["wikipedia_en"]: r for r in recs if r["ids"].get("wikipedia_en") and not r.get("synopsis")}
    titles = list(todo)
    got = 0
    for k in range(0, len(titles), 20):
        chunk = titles[k:k + 20]
        try:
            r = cl.get("https://en.wikipedia.org/w/api.php", params={
                "action": "query", "prop": "extracts", "exintro": 1, "explaintext": 1, "exlimit": 20,
                "titles": "|".join(chunk), "redirects": 1, "format": "json"})
            r.raise_for_status()
            q = r.json()["query"]
        except Exception as e:
            print("Fehler", str(e)[:80]); time.sleep(3); continue
        # Weiterleitungen/Normalisierung auf Originaltitel zurueckfuehren
        back = {}
        for lst in (q.get("normalized", []), q.get("redirects", [])):
            for m in lst:
                back[m["to"]] = m["from"]
        for p in q["pages"].values():
            t = p.get("title"); ex = (p.get("extract") or "").strip()
            orig = back.get(t, t)
            orig = back.get(orig, orig)
            rec = todo.get(orig) or todo.get(t)
            if not rec or len(ex) < 80:
                continue
            rec["synopsis"] = {"text": trim(ex), "source": "Wikipedia (en): " + t, "license": "CC BY-SA 4.0",
                               "url": "https://en.wikipedia.org/wiki/" + urllib.parse.quote(t.replace(" ", "_")), "generated": False}
            cache[orig] = rec["synopsis"]
            got += 1
        time.sleep(0.3)
    json.dump(cache, open(cache_fn, "w"), ensure_ascii=False)
    with open(out, "w") as f:
        for r in recs:
            f.write(json.dumps(r, ensure_ascii=False) + "\n")
    print(f"Synopsen: {got} von {len(titles)} Titeln mit Wikipedia-Artikel → {out}")


if __name__ == "__main__":
    main()
