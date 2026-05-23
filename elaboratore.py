import pandas as pd
import numpy as np
import requests
from bs4 import BeautifulSoup
import json
import time
import random
import os
from concurrent.futures import ThreadPoolExecutor
import subprocess

# ==========================================
# CONSTANTI DI CONFIGURAZIONE STATISTICA
# ==========================================
PESO_STORICO_2020 = 0.40  # Peso della specificità comunale
PESO_STORICO_2025 = 0.60  # Peso del trend recente
CACHE_SEZIONI_FILE = "stato_sezioni.json"

# ==========================================
# 1. PARTE STATICA: CARICAMENTO STORICO
# ==========================================
def carica_e_prepara_storico(file_excel):
    df = pd.read_excel(file_excel)
    df = df.rename(columns={
        'Tot altri cdx.1': 'Stefani_altri_cdx',
        'Tot altri csx.1': 'Manildo_altri_csx'
    })
    if 'Unnamed: 6' in df.columns:
        df = df.drop(columns=['Unnamed: 6'])
        
    df = df.dropna(subset=['Sezione'])
    df['Sezione'] = df['Sezione'].astype(int)
    
    df['voti_tot_2020'] = df['Brugnaro'] + df['Tot altri cdx'] + df['Baretta'] + df['Tot altri csx']
    df['voti_tot_2025'] = df['Stefani'] + df['Stefani_altri_cdx'] + df['Manildo'] + df['Manildo_altri_csx']
    
    df['voti_tot_2020'] = df['voti_tot_2020'].replace(0, 1)
    df['voti_tot_2025'] = df['voti_tot_2025'].replace(0, 1)

    df['pct_cdx_2020'] = (df['Brugnaro'] + df['Tot altri cdx']) / df['voti_tot_2020']
    df['pct_csx_2020'] = (df['Baretta'] + df['Tot altri csx']) / df['voti_tot_2020']
    df['pct_cdx_2025'] = (df['Stefani'] + df['Stefani_altri_cdx']) / df['voti_tot_2025']
    df['pct_csx_2025'] = (df['Manildo'] + df['Manildo_altri_csx']) / df['voti_tot_2025']
    
    totale_comune_2020 = df['voti_tot_2020'].sum()
    totale_comune_2025 = df['voti_tot_2025'].sum()
    
    df['peso_sezione'] = (
        (df['voti_tot_2020'] / totale_comune_2020) * PESO_STORICO_2020 + 
        (df['voti_tot_2025'] / totale_comune_2025) * PESO_STORICO_2025
    )
    return df

# ==========================================
# 2. PARTE DINAMICA: LIVE & DIFF CHECKING
# ==========================================
def analizza_semaforo_e_scopri_variazioni():
    """Legge il semaforo globale e restituisce l'elenco delle sezioni mutate"""
    timestamp = int(time.time() * 1000)
    url_semaforo = f"https://elezioni.comune.venezia.it/data/json/ComunaliCoalizioni.json?quando={timestamp}"
    
    # Carichiamo la situazione precedente se esiste
    stato_precedente = {}
    if os.path.exists(CACHE_SEZIONI_FILE):
        with open(CACHE_SEZIONI_FILE, 'r') as f:
            try:
                stato_precedente = json.load(f)
            except:
                pass
                
    stato_corrente = {}
    sezioni_da_aggiornare = []
    
    try:
        risposta = requests.get(url_semaforo, timeout=10)
        if risposta.status_code == 200:
            features = risposta.json().get('features', [])
            for f in features:
                prop = f.get('properties', {})
                id_sez = prop.get('SEZ')
                if id_sez is not None:
                    id_sez_str = str(id_sez)
                    num_voti_raw = prop.get('NUM_VOTI', 0)
                    try:
                        num_voti = int(num_voti_raw) if num_voti_raw is not None else 0
                    except ValueError:
                        num_voti = 0
                    
                    stato = prop.get('STATO', 0)
                    
                    # Salviamo l'impronta di questa sezione per il prossimo controllo
                    stato_corrente[id_sez_str] = {"voti": num_voti, "stato": stato}
                    
                    if id_sez_str not in stato_precedente:
                        if num_voti > 0 or str(stato) == "-1":
                            sezioni_da_aggiornare.append(int(id_sez))
                    else:
                        info_prev = stato_precedente[id_sez_str]
                        if num_voti != info_prev["voti"] or stato != info_prev["stato"]:
                            if num_voti > 0 or str(stato) == "-1":
                                sezioni_da_aggiornare.append(int(id_sez))
                                
            # Aggiorna il file di cache sul disco
            with open(CACHE_SEZIONI_FILE, 'w') as f:
                json.dump(stato_corrente, f, indent=4)
                
        else:
            print(f"⚠️ Errore lettura semaforo: {risposta.status_code}")
    except Exception as e:
        print(f"⚠️ Errore nel controllo differenziale: {e}")
        
    return sezioni_da_aggiornare, stato_corrente

def estrai_dati_sezione(id_sezione):
    anti_cache = random.randint(100000, 999999)
    url_sezione = f"https://elezioni.comune.venezia.it/risultati/amministrative-sindaco-2026/567/S/{id_sezione}?d={anti_cache}"
    headers = {'User-Agent': 'Mozilla/5.0'}
    
    voti_sezione = {}
    try:
        risposta = requests.get(url_sezione, headers=headers, timeout=5)
        if risposta.status_code != 200:
            return None
        soup = BeautifulSoup(risposta.text, 'html.parser')
        tabella_sindaco = soup.find('table')
        if not tabella_sindaco:
            return None
            
        righe = tabella_sindaco.find_all('tr')
        for riga in righe[1:]:
            celle = [cella.get_text(strip=True) for cella in riga.find_all(['td', 'th'])]
            if len(celle) >= 4:
                nome_candidato = celle[2]
                voti_str = celle[3].replace('.', '')
                if nome_candidato and not any(x in nome_candidato.lower() for x in ['totale', 'validi']):
                    try:
                        voti_sezione[nome_candidato] = int(voti_str)
                    except ValueError:
                        voti_sezione[nome_candidato] = 0
        return voti_sezione
    except:
        return None

# ==========================================
# NOVITÀ: FUNZIONE DI ESPORTAZIONE JSON DASHBOARD
# ==========================================
def esporta_dati_dashboard(sezioni_pervenute, totale_sezioni, stime_candidati, swing_candidati, file_output="dati_dashboard.json"):
    """Genera il file JSON strutturato con attendibilità statistica non lineare"""
    pct_scrutinio = (sezioni_pervenute / totale_sezioni) * 100 if totale_sezioni > 0 else 0
    
    # Calcolo attendibilità non lineare (Curva Sigmoide)
    # Al 10% di spoglio -> ~25% attendibilità
    # Al 30% di spoglio -> ~73% attendibilità
    # Al 50% di spoglio -> ~95% attendibilità
    # Al 70% di spoglio -> ~99.5% attendibilità
    if pct_scrutinio == 0:
        attendibilita_modello = 0.0
    elif pct_scrutinio == 100:
        attendibilita_modello = 100.0
    else:
        # Funzione logistica scalata tra 0 e 100
        attendibilita_modello = round(100 / (1 + np.exp(-0.1 * (pct_scrutinio - 20))), 2)
        # Un piccolo safe check per evitare balzi strani all'inizio
        attendibilita_modello = max(round(pct_scrutinio, 2), attendibilita_modello)
        attendibilita_modello = min(100.0, attendibilita_modello)

    dati = {
        "ultimo_aggiornamento": time.strftime("%Y-%m-%d %H:%M:%S"),
        "scrutinio": {
            "sezioni_pervenute": int(sezioni_pervenute),
            "totale_sezioni": int(totale_sezioni),
            "percentuale_completamento": round(pct_scrutinio, 2),
            "attendibilita_statistica": round(attendibilita_modello, 2)  # <--- NUOVA CHIAVE
        },
        "stime_finali": [
            {
                "candidato": cand,
                "percentuale_stata": round(val, 2),
                "swing_rispetto_storico": round(swing_candidati.get(cand, 0.0), 2)
            }
            for cand, val in stime_candidati.items()
        ]
    }
    
    dati["stime_finali"] = sorted(dati["stime_finali"], key=lambda x: x["percentuale_stata"], reverse=True)
    
    try:
        # 1. Scrittura del file principale per la dashboard live
        with open(file_output, 'w', encoding='utf-8') as f:
            json.dump(dati, f, indent=4, ensure_ascii=False)
        
        # 2. STORICIZZAZIONE: Crea una copia numerata/temporale nella cartella 'storico'
        os.makedirs("storico", exist_ok=True)
        timestamp_file = time.strftime("%H%M%S") # Es: 154230 (ore, minuti, secondi)
        file_storico = f"storico/snapshot_{timestamp_file}.json"
        
        with open(file_storico, 'w', encoding='utf-8') as f:
            json.dump(dati, f, indent=4, ensure_ascii=False)
            
        print(f"✅ Dashboard aggiornata ({attendibilita_modello}%). Snapshot storicizzato in '{file_storico}'.")
    except Exception as e:
        print(f"⚠️ Errore durante la scrittura dei file JSON: {e}")
        
# ==========================================
# 3. MOTORE DI CALCOLO E PROIEZIONE VARIABILE
# ==========================================
def elabora_proiezioni(df_storico, configurazione_candidati):
    mappa_config = configurazione_candidati.get("mappatura_storica", {})
    candidati_2026 = list(configurazione_candidati.get("candidati_2026", {}).keys())
    
    DATABASE_LIVE_FILE = "database_voti_live.json"
    database_voti_live = {}
    if os.path.exists(DATABASE_LIVE_FILE):
        with open(DATABASE_LIVE_FILE, 'r') as f:
            try: database_voti_live = json.load(f)
            except: pass

    sezioni_mutate, stato_totale_semaforo = analizza_semaforo_e_scopri_variazioni()
    
    if sezioni_mutate:
        print(f"🔄 Rilevate {len(sezioni_mutate)} sezioni con NUOVI dati rispetto all'ultimo controllo.")
        print(f"Avvio scaricamento mirato dei soli seggi variati...")
        
        dati_nuovi = {}
        with ThreadPoolExecutor(max_workers=15) as executor:
            futuri = {executor.submit(estrai_dati_sezione, sez): sez for sez in sezioni_mutate}
            for futuro in futuri:
                sez = futuri[futuro]
                try:
                    res = futuro.result()
                    if res and sum(res.values()) > 0:
                        dati_nuovi[str(sez)] = res
                except:
                    pass
        
        database_voti_live.update(dati_nuovi)
        with open(DATABASE_LIVE_FILE, 'w') as f:
            json.dump(database_voti_live, f, indent=4)
    else:
        print("☕ Nessuna variazione rilevata nei seggi. Uso i dati pronti in memoria.")

    for c in candidati_2026:
        df_storico[f'voti_live_{c}'] = 0
    df_storico['sezione_pervenuta'] = False
    
    sezioni_pervenute_count = 0
    for idx, row in df_storico.iterrows():
        sez_str = str(int(row['Sezione']))
        if sez_str in database_voti_live:
            df_storico.at[idx, 'sezione_pervenuta'] = True
            sezioni_pervenute_count += 1
            for c in candidati_2026:
                df_storico.at[idx, f'voti_live_{c}'] = database_voti_live[sez_str].get(c, 0)
                    
    print(f"📊 Analisi statistica basata su {sezioni_pervenute_count} sezioni reali attive.")
    
    df_storico['tot_voti_live_2026'] = df_storico[[f'voti_live_{c}' for c in candidati_2026]].sum(axis=1)
    df_storico['pct_cdx_live_2026'] = 0.0
    df_storico['pct_csx_live_2026'] = 0.0
    
    for idx, row in df_storico.iterrows():
        if row['sezione_pervenuta'] and row['tot_voti_live_2026'] > 0:
            voti_cdx = sum(row[f'voti_live_{c}'] for c in candidati_2026 if 'cdx' in mappa_config.get(c, {}).get('tipo_blocco', ''))
            voti_csx = sum(row[f'voti_live_{c}'] for c in candidati_2026 if 'csx' in mappa_config.get(c, {}).get('tipo_blocco', ''))
            df_storico.at[idx, 'pct_cdx_live_2026'] = voti_cdx / row['tot_voti_live_2026']
            df_storico.at[idx, 'pct_csx_live_2026'] = voti_csx / row['tot_voti_live_2026']

    df_storico['swing_cdx_2020'] = df_storico['pct_cdx_live_2026'] - df_storico['pct_cdx_2020']
    df_storico['swing_csx_2020'] = df_storico['pct_csx_live_2026'] - df_storico['pct_csx_2020']
    df_storico['swing_cdx_2025'] = df_storico['pct_cdx_live_2026'] - df_storico['pct_cdx_2025']
    df_storico['swing_csx_2025'] = df_storico['pct_csx_live_2026'] - df_storico['pct_csx_2025']
    
    # ========================================================
    # NUOVO MOTORE: SWING PESATO SULLA SIGNIFICATIVITÀ DELLE ROCCAFORTI
    # ========================================================
    df_storico['peso_swing_sezione'] = 1.0

    if sezioni_pervenute_count > 0:
        for idx, row in df_storico[df_storico['sezione_pervenuta']].iterrows():
            base_sez_cdx = (row['pct_cdx_2020'] * PESO_STORICO_2020) + (row['pct_cdx_2025'] * PESO_STORICO_2025)
            base_sez_csx = (row['pct_csx_2020'] * PESO_STORICO_2020) + (row['pct_csx_2025'] * PESO_STORICO_2025)
            
            if base_sez_cdx > 0.55 and row['swing_csx_2025'] > 0.01:
                df_storico.at[idx, 'peso_swing_sezione'] = 2.0
            elif base_sez_csx > 0.55 and row['swing_cdx_2025'] > 0.01:
                df_storico.at[idx, 'peso_swing_sezione'] = 2.0
                
        sez_prev = df_storico['sezione_pervenuta']
        p_swing = df_storico[sez_prev]['peso_swing_sezione']
        
        swing_globale_cdx_2020 = np.average(df_storico[sez_prev]['swing_cdx_2020'], weights=p_swing)
        swing_globale_csx_2020 = np.average(df_storico[sez_prev]['swing_csx_2020'], weights=p_swing)
        swing_globale_cdx_2025 = np.average(df_storico[sez_prev]['swing_cdx_2025'], weights=p_swing)
        swing_globale_csx_2025 = np.average(df_storico[sez_prev]['swing_csx_2025'], weights=p_swing)
    else:
        swing_globale_cdx_2020 = swing_globale_csx_2020 = 0.0
        swing_globale_cdx_2025 = swing_globale_csx_2025 = 0.0

    # Calcolo lo Swing di Municipalità
    swing_muni = df_storico[df_storico['sezione_pervenuta']].groupby('Municipalità').agg(
        m_swing_cdx_2020=('swing_cdx_2020', 'mean'),
        m_swing_csx_2020=('swing_csx_2020', 'mean'),
        m_swing_cdx_2025=('swing_cdx_2025', 'mean'),
        m_swing_csx_2025=('swing_csx_2025', 'mean')
    ).fillna(0.0)
    
    cols_to_drop = [c for c in ['m_swing_cdx_2020', 'm_swing_csx_2020', 'm_swing_cdx_2025', 'm_swing_csx_2025'] if c in df_storico.columns]
    df_storico = df_storico.drop(columns=cols_to_drop).join(swing_muni, on='Municipalità')
    df_storico['m_swing_cdx_2020'] = df_storico['m_swing_cdx_2020'].fillna(0.0)
    df_storico['m_swing_csx_2020'] = df_storico['m_swing_csx_2020'].fillna(0.0)
    df_storico['m_swing_cdx_2025'] = df_storico['m_swing_cdx_2025'].fillna(0.0)
    df_storico['m_swing_csx_2025'] = df_storico['m_swing_csx_2025'].fillna(0.0)

    # ========================================================
    # APPLICAZIONE DINAMICA DEI PESI STORICI (DAMPING FACTOR)
    # ========================================================
    percentuale_scrutinio = sezioni_pervenute_count / len(df_storico)
    
    ATTENUAZIONE_2020 = max(0.0, 1.0 - (percentuale_scrutinio * 2.0))
    PESO_DINA_2020 = PESO_STORICO_2020 * ATTENUAZIONE_2020
    PESO_DINA_2025 = 1.0 - PESO_DINA_2020

    proiezioni_candidati = {c: 0.0 for c in candidati_2026}
    PESO_SWING_LOCALE = 0.60
    PESO_SWING_GLOBALE = 0.40
    
    for idx, row in df_storico.iterrows():
        peso = row['peso_sezione']
        
        if row['sezione_pervenuta']:
            tot_sez = row['tot_voti_live_2026']
            for c in candidati_2026:
                pct_effettiva = row[f'voti_live_{c}'] / tot_sez if tot_sez > 0 else 0.0
                proiezioni_candidati[c] += pct_effettiva * peso
        else:
            effettivo_swing_cdx_2020 = (row['m_swing_cdx_2020'] * PESO_SWING_LOCALE) + (swing_globale_cdx_2020 * PESO_SWING_GLOBALE)
            effettivo_swing_csx_2020 = (row['m_swing_csx_2020'] * PESO_SWING_LOCALE) + (swing_globale_csx_2020 * PESO_SWING_GLOBALE)
            effettivo_swing_cdx_2025 = (row['m_swing_cdx_2025'] * PESO_SWING_LOCALE) + (swing_globale_cdx_2025 * PESO_SWING_GLOBALE)
            effettivo_swing_csx_2025 = (row['m_swing_csx_2025'] * PESO_SWING_LOCALE) + (swing_globale_csx_2025 * PESO_SWING_GLOBALE)

            stima_pct_cdx_2020 = np.clip(row['pct_cdx_2020'] + effettivo_swing_cdx_2020, 0, 1)
            stima_pct_cdx_2025 = np.clip(row['pct_cdx_2025'] + effettivo_swing_cdx_2025, 0, 1)
            stima_pct_cdx = (stima_pct_cdx_2020 * PESO_DINA_2020) + (stima_pct_cdx_2025 * PESO_DINA_2025)
            
            stima_pct_csx_2020 = np.clip(row['pct_csx_2020'] + effettivo_swing_csx_2020, 0, 1)
            stima_pct_csx_2025 = np.clip(row['pct_csx_2025'] + effettivo_swing_csx_2025, 0, 1)
            stima_pct_csx = (stima_pct_csx_2020 * PESO_DINA_2020) + (stima_pct_csx_2025 * PESO_DINA_2025)
            
            for c in candidati_2026:
                tipo = mappa_config.get(c, {}).get('tipo_blocco', '')
                if 'cdx_principale' in tipo:
                    proiezioni_candidati[c] += stima_pct_cdx * 0.90 * peso
                elif 'cdx_minore' in tipo:
                    proiezioni_candidati[c] += stima_pct_cdx * 0.025 * peso
                elif 'csx_principale' in tipo:
                    proiezioni_candidati[c] += stima_pct_csx * 0.85 * peso
                elif 'csx_minore' in tipo:
                    proiezioni_candidati[c] += stima_pct_csx * 0.075 * peso
                    
    somma_pesi = sum(proiezioni_candidati.values())
    if somma_pesi > 0:
        for c in proiezioni_candidati:
            proiezioni_candidati[c] = (proiezioni_candidati[c] / somma_pesi) * 100
            
    # Restituiamo anche le variabili di controllo utili alla dashboard
    info_controllo = {
        "sezioni_pervenute": sezioni_pervenute_count,
        "totale_sezioni": len(df_storico),
        "swing_globale_cdx_2025": swing_globale_cdx_2025 * 100,
        "swing_globale_csx_2025": swing_globale_csx_2025 * 100
    }
            
    return proiezioni_candidati, info_controllo

# ==========================================
# 4. MAIN LOOP
# ==========================================
if __name__ == "__main__":
    print("=== ELETTORANDO 2026: MOTORE DI PROIEZIONE DIFFERENZIALE ===")
    df_storico = carica_e_prepara_storico("storico_elezioni.xlsx")
    
    if os.path.exists('candidati_config.json'):
        with open('candidati_config.json', 'r', encoding='utf-8') as f:
            config_candidati = json.load(f)
            
        inizio_elaborazione = time.time()
        # Modificato l'unpacking per ricevere anche i metadati di controllo
        risultati_proiettati, info_cnt = elabora_proiezioni(df_storico, config_candidati)
        fine_elaborazione = time.time()
        
        print("\n========================================================")
        print("   PROIEZIONE RISULTATI FINALI STIMATI (60% 2025 - 40% 2020)")
        print(f"   Tempo di calcolo loop: {fine_elaborazione - inizio_elaborazione:.4f} secondi")
        print("========================================================")
        
        classifica = sorted(risultati_proiettati.items(), key=lambda x: x[1], reverse=True)
        for cand, percentuale in classifica:
            print(f"  {cand.ljust(30)}: {percentuale:.2f}%")
        print("========================================================")
        
        # --------------------------------------------------------
        # INIEZIONE FUNZIONE DI ESPORTAZIONE (PUNTO 1)
        # --------------------------------------------------------
        # Mappiamo lo swing calcolato dal modello sui singoli candidati per blocchi di appartenenza
        mappa_blocchi = config_candidati.get("mappatura_storica", {})
        swing_per_candidato = {}
        for c in risultati_proiettati.keys():
            tipo_blocco = mappa_blocchi.get(c, {}).get('tipo_blocco', '')
            if 'cdx' in tipo_blocco:
                swing_per_candidato[c] = info_cnt["swing_globale_cdx_2025"]
            elif 'csx' in tipo_blocco:
                swing_per_candidato[c] = info_cnt["swing_globale_csx_2025"]
            else:
                swing_per_candidato[c] = 0.0
        
        # Lancio l'esportazione verso la dashboard
        esporta_dati_dashboard(
            sezioni_pervenute=info_cnt["sezioni_pervenute"],
            totale_sezioni=info_cnt["totale_sezioni"],
            stime_candidati=risultati_proiettati,
            swing_candidati=swing_per_candidato
        )
        
        # --------------------------------------------------------
        # AUTOMAZIONE UPLOAD CON LFTP
        # --------------------------------------------------------
        print("📤 Avvio trasferimento dati sul server remoto...")
        try:
            # Esegue lo script bash creato in precedenza
            subprocess.run(["./upload.sh"], check=True)
        except subprocess.CalledProcessError as e:
            print(f"⚠️ Errore durante l'esecuzione di upload.sh: {e}")
        except Exception as e:
            print(f"⚠️ Impossibile avviare lo script di upload: {e}")