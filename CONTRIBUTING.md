# Mitmachen

Dieses Projekt sammelt **Anime** (TV, Film, OVA, ONA, Special) in einem einheitlichen, KI-freundlichen Format. Kein Manga.

## Goldene Regel
**Kopiere nichts von AniList, MyAnimeList oder Anime News Network** (Texte, Beschreibungen, Wertungen, Bilder). Deren Nutzungsbedingungen verbieten das. Erlaubte Quellen: Wikidata, Wikipedia, manami (ODbL), offizielle Seiten/Pressemitteilungen (selbst formuliert), eigenes Wissen.

## Ablauf
1. Eintrag ändern/ergänzen in `data/…` (oder per Skript).
2. `python pipeline/validate.py data/anime.jsonl` — muss ohne Fehler laufen.
3. Pull Request mit kurzer Begründung und **Quelle**; jeder Eintrag führt seine Herkunft in `sources`.
4. Maintainer prüfen: Schema, Quelle, Duplikate.

## Regeln für Felder
- `synopsis`: eigene Worte oder freie Quelle (Wikipedia-Intro, CC BY-SA), mit `source` + `license`. KI-erzeugte Texte `generated: true`.
- `status` wird aus Start-/Enddatum abgeleitet; bei Zweifel Datum angeben, nicht raten.
- Eine Zeile = ein Werk. Staffeln mit eigener Veröffentlichung sind eigene Einträge.
- Cross-IDs (`ids`) bevorzugen — damit lassen sich Duplikate automatisch erkennen.
