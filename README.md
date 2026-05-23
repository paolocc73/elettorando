le elezioni comunali di Venezia (24-25 Maggio 2026). Il modello elabora lo *swing* basandosi sullo storico elettorale e sul flusso parziale delle sezioni pervenute.

## 🛠️ Architettura del Progetto

Il sistema è strutturato in tre componenti macro, interconnessi tramite un flusso automatico di esportazione e sincronizzazione:

[ Python Engine ] ➔ genera ➔ [ dati_dashboard.json ] & [ storico/ ]
│
upload.sh (lftp)
▼
[ Server Remoto ] ➔ esegue ➔ [ index.php ] (Dashboard Frontend)


1. **Codice di Elaborazione (`elaboratore.py`)**
   * Script in Python eseguito in ambiente virtuale (`venv`) su macchina locale.
   * Calcola le stime analitiche e l'attendibilità statistica logistica.
   * Esporta ciclicamente il file live `dati_dashboard.json` e archivia i progressivi storici con timestamp nella cartella locale `storico/`.

2. **Script di Sincronizzazione (`upload.sh`)**
   * Script Bash basato su `lftp`.
   * Gestisce il trasferimento in background dei dati sul server remoto.
   * Esegue il mirror automatico della cartella di storicizzazione ignorando eventuali assenze locali (`--ignore-missing-local`).

3. **Interfaccia Web (`index.php`)**
   * Dashboard frontend reattiva con componenti Tailwind CSS e Material Icons.
   * **Polling Automatico:** Sincronizzazione live ogni 30 secondi dal file JSON principale.
   * **Quorum Minimo:** Dispone di una barriera di sicurezza algoritmica che congela la visualizzazione dei grafici e mostra una schermata di attesa fino al raggiungimento di almeno **5 sezioni pervenute**.
   * **Navigazione Temporale:** Menu laterale (Archivio Storico) generato dinamicamente in PHP che permette di consultare i vecchi snapshot disattivando temporaneamente il live.

---

## 🚀 Linee Guida Operative per lo Spoglio (Lunedì)

### 1. Setup Ambiente Locale
Assicurarsi che l'ambiente virtuale Python sia attivo e che la cartella storico esista sul file system:
```bash
source venv/bin/activate
mkdir -p storico
2. Avvio del Flusso
Eseguire il core del modello predittivo:

Bash
python elaboratore_2.py
3. Allineamento Repository (Git)
A fine operazioni o in caso di modifiche al codice della dashboard, sincronizzare il codice su GitHub:

Bash
git add .
git commit -m "Fix: ottimizzazione logica di storicizzazione in index.php"
git push origin main
Sviluppato da pcc soft. Licenza libera da vincoli di riproduzione.