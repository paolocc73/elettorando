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

# SICUREZZA: Crea la cartella storico locale se non esistesse, 
# e inserisci un file nascosto temporaneo così non risulterà mai del tutto vuota
mkdir -p storico
touch storico/.anchor

# Esegui l'upload usando le variabili protette (senza il flag che ha generato l'errore)
lftp <<EOF
set ftp:ssl-allow no
open -u "$FTP_USER","$FTP_PASS" "$FTP_HOST"
put dati_dashboard.json
put stato_sezioni.json
mirror --reverse --continue storico storico
quit
EOF

echo "✅ Trasferimento completato!"