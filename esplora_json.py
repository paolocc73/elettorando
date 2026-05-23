import requests

url_2020 = "https://elezioni2020.comune.venezia.it/data/json/ComunaliCoalizioni.json?quando=1778759488844"

try:
    risposta = requests.get(url_2020, timeout=10)
    dati = risposta.json()
    
    features = dati.get('features', [])
    if features:
        prima_sezione = features[0]
        print("=== STRUTTURA DI UNA SINGOLA SEZIONE ===")
        print("Chiavi della sezione:", list(prima_sezione.keys()))
        
        # Esploriamo le proprietà (dove risiedono i dati dello spoglio)
        if 'properties' in prima_sezione:
            proprieta = prima_sezione['properties']
            print("\n=== CAMPI DATI (PROPERTIES) DISPONIBILI ===")
            print(f"Numero di campi: {len(proprieta)}")
            print("\nElenco chiavi e valori d'esempio della Sezione 1:")
            for k, v in proprieta.items():
                # Stampiamo tutto per capire dove sono i voti di Brugnaro e Baretta nel 2020
                print(f"  {k}: {v}")
        else:
            print("\nNessuna chiave 'properties' trovata nella feature.")
            
except Exception as e:
    print(f"Errore: {e}")