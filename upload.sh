#!/bin/bash

# Recupera la directory in cui si trova lo script
DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"

# Carica le credenziali dal file .env se esiste
if [ -f "$DIR/.env" ]; then
    source "$DIR/.env"
else
    echo "Errore: File .env non trovato. Impossibile caricare le credenziali."
    exit 1
fi

# Spostati nella directory del progetto per sicurezza sui percorsi relativi
cd "$DIR"

# Esegui l'upload usando le variabili protette
lftp <<EOF
set ftp:ssl-allow no
open -u "$FTP_USER","$FTP_PASS" "$FTP_HOST"
put dati_dashboard.json
put stato_sezioni.json
mirror -R --ignore-missing-local storico storico
quit
EOF

echo "✅ Trasferimento completato!"