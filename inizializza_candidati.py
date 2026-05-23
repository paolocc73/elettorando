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
    
    print("Estrazione anagrafica completa dei candidati Sindaco 2026...")
    
    try:
        risposta = requests.get(url_sezione_1, headers=headers, timeout=15)
        soup = BeautifulSoup(risposta.text, 'html.parser')
        
        # Prendiamo la prima tabella (Sindaco)
        tabella_sindaco = soup.find('table')
        if not tabella_sindaco:
            print("Errore: Tabella non trovata.")
            return
            
        config_candidati = {
            "candidati_2026": {},
            "mappatura_storica": {}
        }
        
        righe = tabella_sindaco.find_all('tr')
        
        # Saltiamo la prima riga di intestazione e cicliamo su tutte le altre
        for riga in righe[1:]:
            celle = [cella.get_text(strip=True) for cella in riga.find_all(['td', 'th'])]
            
            # Verifichiamo che la riga abbia abbastanza colonne e che il nome non sia vuoto
            if len(celle) >= 4:
                nome_candidato = celle[2]
                
                if nome_candidato and not any(x in nome_candidato.lower() for x in ['totale', 'validi']):
                    # Aggiungiamo alla struttura live
                    config_candidati["candidati_2026"][nome_candidato] = {
                        "voti_live": 0,
                        "percentuale_live": 0.0
                    }
                    
                    # Mappatura automatica con i blocchi del passato per lo swing
                    if "VENTURINI" in nome_candidato:
                        config_candidati["mappatura_storica"][nome_candidato] = "Brugnaro"
                    elif "MARTELLA" in nome_candidato:
                        config_candidati["mappatura_storica"][nome_candidato] = "Baretta"
                    else:
                        config_candidati["mappatura_storica"][nome_candidato] = "Altro"
                        
        print(f"\nTrovati {len(config_candidati['candidati_2026'])} candidati Sindaco.")
        for c in config_candidati["candidati_2026"].keys():
            print(f" - {c} (Mappato su storico: {config_candidati['mappatura_storica'][c]})")
            
        # Scrittura del file di configurazione
        with open('candidati_config.json', 'w', encoding='utf-8') as f:
            json.dump(config_candidati, f, indent=4, ensure_ascii=False)
            
        print("\n✅ File 'candidati_config.json' generato con successo!")
        
    except Exception as e:
        print(f"Errore durante la generazione: {e}")

if __name__ == "__main__":
    genera_configurazione_candidati()