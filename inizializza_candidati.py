import requests
from bs4 import BeautifulSoup
import json
import time

def genera_configurazione_candidati():
    timestamp = int(time.time() * 1000)
    url_sezione_1 = f"https://elezioni.comune.venezia.it/risultati/amministrative-sindaco-2026/567/S/1?d={timestamp}"
    
    headers = {
        'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
    }
    
    print("Estrazione anagrafica e mappatura blocchi storici (Comunali 2020 + Regionali 2025)...")
    
    try:
        risposta = requests.get(url_sezione_1, headers=headers, timeout=15)
        soup = BeautifulSoup(risposta.text, 'html.parser')
        tabella_sindaco = soup.find('table')
        
        config_candidati = {
            "candidati_2026": {},
            "mappatura_storica": {}
        }
        
        righe = tabella_sindaco.find_all('tr')
        
        for riga in righe[1:]:
            celle = [cella.get_text(strip=True) for cella in riga.find_all(['td', 'th'])]
            if len(celle) >= 4:
                nome_candidato = celle[2]
                
                if nome_candidato and not any(x in nome_candidato.lower() for x in ['totale', 'validi']):
                    config_candidati["candidati_2026"][nome_candidato] = {
                        "voti_live": 0,
                        "percentuale_live": 0.0
                    }
                    
                    # --- MAPPATURA STRATEGICA RIGIDA ---
                    
                    # 1. I due contendenti principali
                    if "VENTURINI" in nome_candidato:
                        config_candidati["mappatura_storica"][nome_candidato] = {
                            "tipo_blocco": "cdx_principale",
                            "ancora_2020": "Brugnaro",
                            "ancora_2025": "Stefani"
                        }
                    elif "MARTELLA" in nome_candidato:
                        config_candidati["mappatura_storica"][nome_candidato] = {
                            "tipo_blocco": "csx_principale",
                            "ancora_2020": "Baretta",
                            "ancora_2025": "Manildo"
                        }
                    
                    # 2. Area Centrodestra (cdx)
                    elif any(x in nome_candidato for x in ["DEL ZOTTO", "CORO'", "BOLDRIN", "AGIRMO"]):
                        config_candidati["mappatura_storica"][nome_candidato] = {
                            "tipo_blocco": "cdx_minore",
                            "ancora_2020": "Tot altri cdx",
                            "ancora_2025": "Tot altri cdx.1"
                        }
                    
                    # 3. Area Centrosinistra (csx)
                    elif any(x in nome_candidato for x in ["VERNIER", "MARTINI"]):
                        config_candidati["mappatura_storica"][nome_candidato] = {
                            "tipo_blocco": "csx_minore",
                            "ancora_2020": "Tot altri csx",
                            "ancora_2025": "Tot altri csx.1"
                        }
                    
                    # Fallback di sicurezza per eventuali sorprese sulla scheda
                    else:
                        config_candidati["mappatura_storica"][nome_candidato] = {
                            "tipo_blocco": "csx_minore",
                            "ancora_2020": "Tot altri csx",
                            "ancora_2025": "Tot altri csx.1"
                        }
                        
        with open('candidati_config.json', 'w', encoding='utf-8') as f:
            json.dump(config_candidati, f, indent=4, ensure_ascii=False)
            
        print(f"\nGenerata configurazione per {len(config_candidati['candidati_2026'])} candidati.")
        for c, mappa in config_candidati["mappatura_storica"].items():
            print(f" - {c} -> Blocco: {mappa['tipo_blocco']} (Ancore: {mappa['ancora_2020']} / {mappa['ancora_2025']})")
            
        print("\n✅ Configurazione salvata in 'candidati_config.json'!")
        
    except Exception as e:
        print(f"Errore: {e}")

if __name__ == "__main__":
    genera_configurazione_candidati()