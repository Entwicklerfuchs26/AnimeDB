#!/usr/bin/env bash
# Tageslauf: alles neu zusammenbauen → data/anime.jsonl (die veröffentlichte Fassung).
# Quellen: Wikidata (live), anime-offline-database (archivierter Stand in sources/), Wikipedia (Einleitungstexte).
# OADB_CONTACT (E-Mail oder URL) gehört in den User-Agent; Standard: dieses Repository.
set -euo pipefail
cd "$(dirname "$0")"
PY="${PYTHON:-python3}"
export OADB_CONTACT="${OADB_CONTACT:-https://github.com/Entwicklerfuchs26/AnimeDB}"
mkdir -p data
MANAMI="${MANAMI_JSON:-data/anime-offline-database.json}"
[ -f "$MANAMI" ] || zstd -d -q -f sources/anime-offline-database.json.zst -o "$MANAMI"
$PY pipeline/wikidata_new.py all data/wikidata_all.jsonl
$PY pipeline/manami_import.py "$MANAMI" data/manami.jsonl
$PY pipeline/merge.py data/merged.jsonl data/wikidata_all.jsonl data/manami.jsonl
$PY pipeline/wikipedia_synopsis.py data/merged.jsonl data/syn.jsonl
$PY pipeline/export_public.py data/syn.jsonl data/anime.jsonl --allow-manami
$PY pipeline/validate.py data/anime.jsonl
