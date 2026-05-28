import json
import random
import requests
from bs4 import BeautifulSoup
from concurrent.futures import ThreadPoolExecutor

FILE_STRUTTURA = "stato_sezioni.json"
FILE_OUTPUT_COMPLETO = "database_voti_reali_finiti.json"

def scarica_singola_sezione(id_sezione):
    anti_cache = random.randint(100000, 999999)
    url_sezione = f"https://elezioni.comune.venezia.it/risultati/amministrative-sindaco-2026/567/S/{id_sezione}?d={anti_cache}"
    headers = {'User-Agent': 'Mozilla/5.0'}
    try:
        risposta = requests.get(url_sezione, headers=headers, timeout=5)
        if risposta.status_code != 200: return None
        soup = BeautifulSoup(risposta.text, 'html.parser')
        tabella_sindaco = soup.find('table')
        if not tabella_sindaco: return None
        
        voti_sezione = {}
        righe = tabella_sindaco.find_all('tr')
        for riga in righe[1:]:
            celle = [cella.get_text(strip=True) for cella in riga.find_all(['td', 'th'])]
            if len(celle) >= 4:
                nome_candidato = celle[2]
                voti_str = celle[3].replace('.', '')
                if nome_candidato and not any(x in nome_candidato.lower() for x in ['totale', 'validi']):
                    try: voti_sezione[nome_candidato] = int(voti_str)
                    except ValueError: voti_sezione[nome_candidato] = 0
        return id_sezione, voti_sezione
    except:
        return None

if __name__ == "__main__":
    with open(FILE_STRUTTURA, 'r') as f:
        struttura = json.load(f)
    
    elenco_sezioni = [int(k) for k in struttura.keys()]
    database_reale = {}
    
    print(f"⏳ Inizio download massivo di {len(elenco_sezioni)} sezioni (20 thread concorrenti)...")
    
    with ThreadPoolExecutor(max_workers=20) as executor:
        futuri = {executor.submit(scarica_singola_sezione, sez): sez for sez in elenco_sezioni}
        for futuro in futuri:
            risultato = futuro.result()
            if risultato:
                id_sez, voti = risultato
                if voti and sum(voti.values()) > 0:
                    database_reale[str(id_sez)] = voti

    with open(FILE_OUTPUT_COMPLETO, 'w', encoding='utf-8') as f:
        json.dump(database_reale, f, indent=4, ensure_ascii=False)
        
    print(f"✅ Fatto! Salvate {len(database_reale)} sezioni reali in '{FILE_OUTPUT_COMPLETO}'.")