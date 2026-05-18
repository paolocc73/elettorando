import pandas as pd
import numpy as np

def carica_e_prepara_storico(file_excel):
    # 1. Carica il file Excel
    df = pd.read_excel(file_excel)
    
    # Rinominiamo le colonne per chiarezza interna dello script
    df = df.rename(columns={
        'Tot altri cdx.1': 'Stefani_altri_cdx',
        'Tot altri csx.1': 'Manildo_altri_csx'
    })
    
    # Rimozione di colonne vuote o non necessarie se presenti
    if 'Unnamed: 6' in df.columns:
        df = df.drop(columns=['Unnamed: 6'])
        
    # Pulizia: eliminiamo righe dove la sezione non è un numero valido (es. righe di totale in fondo)
    df = df.dropna(subset=['Sezione'])
    df['Sezione'] = df['Sezione'].astype(int)
    
    # 2. Calcolo dei voti validi totali per sezione nelle due elezioni
    df['voti_tot_2020'] = df['Brugnaro'] + df['Tot altri cdx'] + df['Baretta'] + df['Tot altri csx']
    df['voti_tot_2025'] = df['Stefani'] + df['Stefani_altri_cdx'] + df['Manildo'] + df['Manildo_altri_csx']
    
    # Evitiamo divisioni per zero se qualche sezione speciale avesse 0 voti
    df['voti_tot_2020'] = df['voti_tot_2020'].replace(0, 1)
    df['voti_tot_2025'] = df['voti_tot_2025'].replace(0, 1)

    # 3. Calcolo delle percentuali storiche per candidati principali
    df['pct_brugnaro_2020'] = df['Brugnaro'] / df['voti_tot_2020']
    df['pct_baretta_2020'] = df['Baretta'] / df['voti_tot_2020']
    
    df['pct_stefani_2025'] = df['Stefani'] / df['voti_tot_2025']
    df['pct_manildo_2025'] = df['Manildo'] / df['voti_tot_2025']
    
    # 4. Calcolo del peso demografico relativo di ciascuna sezione (media tra 2020 e 2025)
    totale_comune_2020 = df['voti_tot_2020'].sum()
    totale_comune_2025 = df['voti_tot_2025'].sum()
    
    df['peso_2020'] = df['voti_tot_2020'] / totale_comune_2020
    df['peso_2025'] = df['voti_tot_2025'] / totale_comune_2025
    df['peso_sezione'] = (df['peso_2020'] + df['peso_2025']) / 2

    return df

if __name__ == "__main__":
    file_storico = "storico_elezioni.xlsx"
    print(f"Elaborazione del file {file_storico} in corso...")
    
    # Questa è la riga che era saltata o disallineata:
    df_storico = carica_e_prepara_storico(file_storico)
    
    print("\n=== STATISTICHE DI BASE CALCOLATE ===")
    print(f"Sezioni elaborate: {len(df_storico)}")
    
    # Raggruppamento e calcolo pesi
    municipalita_info = df_storico.groupby('Municipalità').agg(
        numero_sezioni=('Sezione', 'count'),
        peso_totale=('peso_sezione', 'sum')
    )
    
    municipalita_info['peso_totale'] = (municipalita_info['peso_totale'] * 100).round(2)
    
    print("\n=== PESO DEMOGRAFICO MEDIO PER MUNICIPALITÀ ===")
    print(municipalita_info)