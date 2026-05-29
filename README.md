# Elettorando 2026 🗳️

Elettorando è un motore di calcolo statistico e proiezione geopolitica progettato per interpretare il flusso dei dati in tempo reale (Live Spoglio) delle elezioni comunali di Venezia del 24-25 maggio 2026. L'obiettivo del sistema è superare la distorsione ottica causata dall'afflusso asincrono dei primi dati sezionali, fornendo una proiezione stabilizzata, pesata e affidabile del risultato finale cittadino.

---

## 🚀 Novità ed Evoluzione dell'Architettura (Maggio 2026)

Il sistema è stato potenziato con un'architettura di **Backtesting e Simulazione Locale** che permette di stressare il modello e la dashboard simulando l'andamento reale dello spoglio senza sovraccaricare i server del Comune:
1. **Download Una Tantum (`scarica_tutto.py`)**: Estrae massivamente via thread concorrenti i dati definitivi di tutte le 254 sezioni, storicizzandoli in un database locale (`database_voti_reali_finiti.json`).
2. **Simulatore Nativo Incrementale (`elaboratore.py`)**: Popola incrementalmente il database live iniettando blocchi casuali di 20 sezioni inedite alla volta ogni 20 secondi, calcolando l'evoluzione delle stime e salvando gli snapshot temporali in `storico/`.
3. **Bypass del Controllo Remoto**: Introdotta la modalità isolata (`modalita_simulazione=True`) per inibire le chiamate HTTP e analizzare lo spoglio differenziale basandosi esclusivamente sui dati parziali accumulati.
4. **Interfaccia Dinamica Ottimizzata**: La dashboard (`index.php`) è stata aggiornata con una Sidebar d'archivio dotata di scorrimento verticale dinamico (`overflow-y-auto`) e pulsante di riallineamento "Live" ancorato in modalità `sticky`.

---

## 📐 L'Algoritmo di Calcolo: Proiezione Differenziale dello Swing

Il cuore di *Elettorando* non si limita a fare una media ponderata dei voti scrutinati, poiché i primi seggi a chiudere lo spoglio (es. le sezioni storicamente sbilanciate o i seggi insulari minori) potrebbero alterare artificialmente la percezione del risultato globale. 

Il modello applica un'**estrapolazione differenziale dello swing** basata sul confronto con lo storico politico del territorio.

### Il Modello Matematico e Logico

1. **Allineamento Geopolitico Lineare**: In fase di caricamento, ogni singola sezione di Venezia viene mappata combinando i propri dati attuali con i dati delle precedenti elezioni omologhe (memorizzati in `storico_elezioni.xlsx`). I candidati del 2026 sono associati ai rispettivi blocchi storici di riferimento (es. Centrodestra `cdx`, Centrosinistra `csx`).

2. **Calcolo dello Swing Parziale Live**: Per ogni sezione $s$ in cui lo scrutinio è concluso (stato = 1), l'algoritmo calcola lo *scostamento* (lo *swing*) tra la percentuale attuale e la percentuale storica della coalizione di riferimento:

```math
\\Delta_{\\text{coalizione}, s} = \\text{Pct}_{\\text{Live}, s} - \\text{Pct}_{\\text{Storica}, s}
```

3. **Stabilizzazione del Dato (Filtro Massivo Comunale)**: Gli swing delle singole sezioni pervenute vengono aggregati a livello macro, calcolando lo **swing medio globale** delle coalizioni principali (pesato sui voti validi per limitare il rumore statistico dei seggi piccolissimi):

```math
\\text{Swing\\_Globale}_{\\text{coalizione}} = \\frac{\\sum_{s \\in \\text{Pervenite}} \\Delta_{\\text{coalizione}, s} \\cdot \\text{Voti\\_Validi}_s}{\\sum_{s \\in \\text{Pervenite}} \\text{Voti\\_Validi}_s}
```

4. **Proiezione Predittiva sulle Sezioni Mancanti**: Qui risiede il potere predittivo del motore. Per tutte le sezioni non ancora pervenute (il restante dello spoglio), il modello **non assegna lo zero**, ma ipotizza che in quelle sezioni l'elettorato si comporterà seguendo lo storico del 2025, *corretto però dallo swing globale registrato fino a quel momento*:

```math
\\text{Pct}_{\\text{Proiettata}, u} = \\text{Pct}_{\\text{Storica}, u} + \\text{Swing\\_Globale}_{\\text{coalizione}}
```

5. **Riorchestrazione e Normalizzazione**: I voti proiettati teorici delle sezioni mancanti vengono sommati ai voti reali scrutinati delle sezioni pervenute. Il totale complessivo viene infine normalizzato a base 100 distribuendo le frazioni residue sugli 8 candidati sindaco, restituendo la **Stima Proiettata Finale** visibile nella dashboard.

6. **Attendibilità Statistica**:
   L'indice di attendibilità espresso in percentuale sale linearmente all'aumentare del numero di seggi pervenuti e della stabilità dello swing globale. Al di sotto delle **5 sezioni**, il sistema attiva un blocco di sicurezza sulla UI in quanto la varianza statistica dello swing è troppo elevata per elaborare una proiezione scientificamente valida.

---

## 🛠️ Flusso d'Esecuzione per la Simulazione

Per avviare un intero ciclo di simulazione e analizzare il comportamento dinamico del modello e del front-end, esegui in sequenza dal terminale del Mac:

```bash
# 1. Attiva l'ambiente virtuale
source venv/bin/activate

# 2. Scarica i dati reali definitivi dal Comune (Una tantum)
python scarica_tutto.py

# 3. Avvia il motore in modalità simulazione backtest
python elaboratore.py