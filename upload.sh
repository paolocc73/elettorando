#!/bin/bash

# Configurazione
HOST="ftp.ipage.com"
USER="paolocc60686"
PASS="iSsettembree10!!!"
REMOTE_DIR="/paolo.cc/app/elettorando"
LOCAL_FILE="dati_dashboard.json"

echo "🔄 Avvio trasferimento in background..."

# Comando LFTP che gestisce la connessione e l'upload sicuro
# ... (tua configurazione iniziale HOST, USER, PASS) ...

lftp -c "
open -u $USER,$PASS $HOST
cd $REMOTE_DIR
put $LOCAL_FILE
mirror -R storico storico 
bye
"

echo "✅ Trasferimento completato!"