#!/bin/sh
# Régénère le rapport GoAccess immédiatement, puis à chaque écriture dans le
# journal d'accès (une visite = une ligne ajoutée = un événement inotify) —
# plutôt qu'un sondage à intervalle fixe. Pas de mode --real-time-html : pas
# de WebSocket à exposer, on recharge simplement /stats/ pour voir le rapport
# à jour, qui l'est déjà à quelques millisecondes près.
set -eu

LOG=/var/log/paleo/access.log
OUT=/report/index.html

regen() {
    goaccess "$LOG" -a -o "$OUT" --log-format=COMBINED --ignore-crawlers
}

regen
while inotifywait -e modify,create,moved_to -q "$LOG" >/dev/null 2>&1; do
    regen
done
