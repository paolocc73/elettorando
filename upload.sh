#!/bin/bash

# Configurazione
HOST="ftp.ipage.com"
USER="paolocc60686"
PASS="iSsettembree10!!!"
REMOTE_DIR="/paolo.cc/app/elettorando"
LOCAL_FILE="dati_dashboard.json"

echo "🔄 Avvio trasferimento in background..."

# Comando LFTP che gestisce la connessione e l'upload sicuro
lftp -c "
open -u $USER,$PASS $HOST
set ftp:ssl-allow no # Cambia in 'yes' se il tuo FTP richiede FTPS esplicito
cd $REMOTE_DIR
put $LOCAL_FILE
bye
"

echo "✅ Trasferimento completato!"