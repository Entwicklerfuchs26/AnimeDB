# Quellen & Namensnennung

| Quelle | Wofür | Lizenz / Bedingung |
|---|---|---|
| [Wikidata](https://www.wikidata.org) | Basis-Datensatz (Titel, Typ, Daten, Studios, Genres, IDs) | CC0 1.0 |
| [Wikipedia (en)](https://en.wikipedia.org) | Kurzbeschreibungen (Einleitungstext) | CC BY-SA 4.0 — Quelle und Link stehen in jedem `synopsis`-Feld |
| Anime News Network | — | **Wird nicht verwendet.** ANN hat keine Lizenz für die Weitergabe ("All rights reserved"); der öffentliche Katalog enthält weder Inhalte noch IDs von ANN. |
| [anime-offline-database](https://github.com/manami-project/anime-offline-database) | Basisschicht für ältere Titel (Titel, Typ, Folgen, Status, Saison, Studios, Synonyme, Querverweis-IDs) | ODbL 1.0 + DbCL 1.0 — Namensnennung, Weitergabe unter gleicher Lizenz (Share-Alike) |

Nicht verwendet (Nutzungsbedingungen verbieten Sammeln/Weitergabe): AniList-API, MyAnimeList-API/Jikan.

## Hinweise
- **Ursprungsquellen von manami:** anime-offline-database aggregiert selbst aus MyAnimeList, AniList, Kitsu, AniDB u. a.
  Die ODbL/DbCL-Lizenz gilt für die Zusammenstellung des Autors. Die Nutzungsbedingungen der Ursprungsquellen haben wir **nicht** geprüft.
  Übernommen werden nur nüchterne Metadaten (Titel, Typ, Folgenzahl, Status, Saison, Studios, Genres, Synonyme, Querverweis-IDs) —
  keine Bilder, Beschreibungstexte oder Bewertungen. Der archivierte Stand liegt unter `sources/`.
- **Entfernung auf Anfrage:** Wer Rechte an einzelnen Angaben hat und deren Entfernung wünscht, öffnet ein Issue in diesem Repository.
  Betroffene Daten werden aus dem Datensatz genommen.
- **Lizenz:** Daten ODbL 1.0 + DbCL 1.0 (`LICENSE`), Skripte MIT (`LICENSE-CODE`). Eine „CC0-Daten“-Freigabe ist wegen
  Share-Alike der Quellen (Wikipedia CC BY-SA, manami ODbL) nicht möglich.
