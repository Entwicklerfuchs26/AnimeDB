# AnimeDB

Offene, einheitlich formatierte **Anime**-Datenbank (TV, Film, OVA, ONA, Special — kein Manga), gebaut für Menschen **und** KI-Suche.
Ein Eintrag = ein Werk, gleiche Felder überall, jede Angabe mit Herkunft.

**Daten:** Release [`latest`](../../releases/latest) → `anime.jsonl` (bzw. `.gz`), täglich automatisch neu gebaut (GitHub Actions).
**Lizenz:** Daten ODbL 1.0 + DbCL 1.0 (`LICENSE`), Skripte MIT (`LICENSE-CODE`). Quellen und Namensnennung: `NOTICE.md`.

## Was drin ist
Rund 40.500 Titel aus **Wikidata** (CC0), **anime-offline-database** (ODbL, archivierter Stand in `sources/`) und
**Wikipedia**-Einleitungstexten (CC BY-SA, mit Quelle im Feld). Nicht verwendet: AniList, MyAnimeList, ANN (deren Bedingungen erlauben die Weitergabe nicht).
Abdeckung variiert je Feld; Synopsen gibt es nur für Titel mit Wikipedia-Artikel.

## Format
`schema/anime.schema.json` — Titel (en/ja/Synonyme), Typ, Status (aus Datum abgeleitet), Start/Ende, Saison, Episoden, Studios, Genres, Webseite,
`synopsis` (Text + Quelle + Lizenz + `generated`), `ids` (Verweise auf Wikidata, AniList, MAL, AniDB, Kitsu … **nur IDs**), `dubs` (Sprache → Konfidenzstufe, Quelle MyDubList), `sources`, `layers`, `field_sources`.

## Pipeline (`./update.sh`, optional `OADB_CONTACT` = E-Mail/URL für den User-Agent)
1. `wikidata_new.py all` — alle Anime aus Wikidata (CC0)
2. `manami_import.py` — ältere Titel aus der archivierten anime-offline-database (`sources/`)
3. `merge.py` — Dubletten über Cross-IDs, Rückfall Titel+Jahr+Typ nur wenn eindeutig
4. `wikipedia_synopsis.py` — Kurzbeschreibung aus Wikipedia-Intro (mit Cache)
5. `mydublist.py` — Synchro-Angaben (Feld `dubs`) aus MyDubList, zugeordnet über MAL-/AniList-ID
6. `export_public.py` — Ausgabe `data/anime.jsonl`
7. `validate.py` — Schema + Regeln

## Rechtliches
- Lizenz und Quellen: `LICENSE`, `NOTICE.md`. **Entfernung auf Anfrage** per Issue.
- manami sammelt selbst aus MAL/Kitsu/AniList/AniDB; deren Bedingungen sind nicht geprüft (siehe `NOTICE.md`).
- **AniList, MyAnimeList und ANN sind keine Quellen.** Siehe `CONTRIBUTING.md`.

## Bekannte Grenzen
- Wenige Synopsen (nur Titel mit Wikipedia-Artikel); Rest offen (Community, freie Quellen, KI-generiert mit Kennzeichnung).
- Titel+Jahr-Abgleich kann selten Verschiedenes verbinden (Stichprobe unauffällig, nicht vollständig geprüft).
- Typ „unknown" bei einem Teil der Titel (Wikidata nur generisch als „anime" klassifiziert).
- Neuzugänge kommen nur über Wikidata (und per Pull Request).
