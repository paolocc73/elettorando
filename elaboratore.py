import pandas as pd
import numpy as np
import requests
from bs4 import BeautifulSoup
import json
import time
import random

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
    
    # Calcolo dei voti validi totali storici
    df['voti_tot_2020'] = df['Brugnaro'] + df['Tot altri cdx'] + df['Baretta'] + df['Tot altri csx']
    df['voti_tot_2025'] = df['Stefani'] + df['Stefani_altri_cdx'] + df['Manildo'] + df['Manildo_altri_csx']
    
    df['voti_tot_2020'] = df['voti_tot_2020'].replace(0, 1)
    df['voti_tot_2025'] = df['voti_tot_2025'].replace(0, 1)

    # Percentuali storiche
    df['pct_brugnaro_2020'] = df['Brugnaro'] / df['voti_tot_2020']
    df['pct_baretta_2020'] = df['Baretta'] / df['voti_tot_2020']
    df['pct_stefani_2025'] = df['Stefani'] / df['voti_tot_2025']
    df['pct_manildo_2025'] = df['Manildo'] / df['voti_tot_2025']
    
    # Pesi demografici
    totale_comune_2020 = df['voti_tot_2020'].sum()
    totale_comune_2025 = df['voti_tot_2025'].sum()
    df['peso_sezione'] = ((df['voti_tot_2020'] / totale_comune_2020) + (df['voti_tot_2025'] / totale_comune_2025)) / 2

    return df

# ==========================================
# 2. PARTE DINAMICA: SCRAPING LIVE
# ==========================================

def controlla_semaforo_sezioni():
    """Interroga il JSON globale per capire quali sezioni hanno dati pronti"""
    timestamp = int(time.time() * 1000)
    url_semaforo = f"https://elezioni.comune.venezia.it/data/json/ComunaliCoalizioni.json?quando={timestamp}"
    
    sezioni_attive = {}
    try:
        risposta = requests.get(url_semaforo, timeout=10)
        if risposta.status_code == 200:
            dati = risposta.json()
            features = dati.get('features', [])
            for f in features:
                prop = f.get('properties', {})
                id_sez = prop.get('SEZ')
                stato = prop.get('STATO') # -1 significa definitivo, altri valori indicano pervenuto/in scrutinio
                
                if id_sez is not None:
                    # Estraiamo il numero di voti gestendo la possibilità che sia una stringa o None
                    num_voti_raw = prop.get('NUM_VOTI', 0)
                    try:
                        num_voti = int(num_voti_raw) if num_voti_raw is not None else 0
                    except ValueError:
                        num_voti = 0
                        
                    stato = prop.get('STATO')
                    
                    # Una sezione è attiva se ha voti scrutinati > 0 o se lo STATO indica consolidamento
                    # Lo STATO viene forzato a stringa per evitare problemi simili se cambiano i tipi sul server
                    is_attiva = (num_voti > 0 or str(stato) == "-1")
                    
                    sezioni_attive[int(id_sez)] = is_attiva
        else:
            print(f"⚠️ Impossibile leggere il semaforo. Status: {risposta.status_code}")
    except Exception as e:
        print(f"⚠️ Errore nel controllo del semaforo: {e}")
        
    return sezioni_attive

def estrai_dati_sezione(id_sezione):
    """Fa lo scraping HTML della pagina della singola sezione attiva"""
    # Generiamo un parametro casuale per distruggere in modo aggressivo le cache di rete/Aruba/Cloudflare
    anti_cache = random.randint(100000, 999999)
    url_sezione = f"https://elezioni.comune.venezia.it/risultati/amministrative-sindaco-2026/567/S/{id_sezione}?d={anti_cache}"
    
    headers = {
        'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
    }
    
    voti_sezione = {}
    try:
        risposta = requests.get(url_sezione, headers=headers, timeout=10)
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
                voti_str = celle[3].replace('.', '') # Rimuove i punti delle migliaia (es. 1.200 -> 1200)
                
                if nome_candidato and not any(x in nome_candidato.lower() for x in ['totale', 'validi']):
                    try:
                        voti_sezione[nome_candidato] = int(voti_str)
                    except ValueError:
                        voti_sezione[nome_candidato] = 0
                        
        return voti_sezione
    except Exception as e:
        print(f"⚠️ Errore durante lo scraping della sezione {id_sezione}: {e}")
        return None

# ==========================================
# 3. COORDINATORE DI TEST
# ==========================================
if __name__ == "__main__":
    print("Inizializzazione del sistema...")
    df_storico = carica_e_prepara_storico("storico_elezioni.xlsx")
    
    print("\nFase 1: Controllo dello stato del semaforo globale...")
    mappa_semaforo = controlla_semaforo_sezioni()
    print(f"Mappa delle sezioni ricevuta. Totale sezioni censite nel JSON: {len(mappa_semaforo)}")
    
    # Contiamo quante risultano attive in questo istante
    attive = [sez for sez, is_attiva in mappa_semaforo.items() if is_attiva]
    print(f"Sezioni che presentano già dati live: {len(attive)}")
    
    # Test di simulazione dello scraping sulla sezione 1 (che sappiamo avere la struttura dei nomi pronta)
    print("\nFase 2: Test di estrazione dati strutturali sulla Sezione 1...")
    dati_test = estrai_dati_sezione(1)
    if dati_test:
        print("Dati estratti correttamente dalla Sezione 1:")
        for cand, voti in dati_test.items():
            print(f"  - {cand}: {voti} voti")
    else:
        print("❌ Errore: Impossibile fare lo scraping della Sezione 1.")