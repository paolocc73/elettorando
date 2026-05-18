import pandas as pd
import os

# Definisci il percorso del file (modifica il nome se diverso)
file_excel = "storico_elezioni.xlsx"

if not os.path.exists(file_excel):
    print(f"Errore: Il file {file_excel} non è stato trovato nella cartella!")
else:
    try:
        # Carica il foglio Excel
        df = pd.read_excel(file_excel)
        
        print("=== CONNESSIONE RIUSCITA ===")
        print(f"Numero totale di righe (sezioni): {len(df)}")
        print("\n=== COLONNE TROVATE NEL FILE ===")
        for i, col in enumerate(df.columns):
            print(f"{i+1}. {col}")
            
        print("\n=== ANTEPRIMA DELLE PRIME 3 RIGHE ===")
        print(df.head(3))
        
    except Exception as e:
        print(f"Si è verificato un errore durante la lettura: {e}")
