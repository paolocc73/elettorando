import json
import time
import random
import numpy as np

print("🚀 Simulatore di spoglio con Attendibilità Logistica avviato.")
print("Premi CTRL+C per interrompere la simulazione.\n")

sezioni_totali = 256

# Incrementiamo a passi di 5 sezioni per volta
for sezioni_pervenute in range(1, sezioni_totali + 1, 5):
    pct_scrutinio = (sezioni_pervenute / sezioni_totali) * 100
    
    # --------------------------------------------------------
    # CALCOLO ATTENDIBILITÀ NON LINEARE (STESSA LOGICA DEL MOTORE)
    # --------------------------------------------------------
    if sezioni_pervenute == sezioni_totali:
        attendibilita_modello = 100.0
    else:
        # Funzione logistica scalata tra 0 e 100
        attendibilita_modello = round(100 / (1 + np.exp(-0.1 * (pct_scrutinio - 20))), 2)
        # Safe check per evitare che all'inizio l'attendibilità sia inferiore allo scrutinio stesso
        attendibilita_modello = max(round(pct_scrutinio, 2), attendibilita_modello)
        attendibilita_modello = min(100.0, attendibilita_modello)
    
    # Genera oscillazioni plausibili dei candidati per il test grafico
    v_perc = round(random.uniform(43.5, 46.5), 2)
    m_perc = round(random.uniform(41.0, 43.5), 2)
    resto = round(100.0 - v_perc - m_perc, 2)
    
    dati_test = {
        "ultimo_aggiornamento": time.strftime("%H:%M:%S"),
        "scrutinio": {
            "sezioni_pervenute": sezioni_pervenute,
            "totale_sezioni": sezioni_totali,
            "percentuale_completamento": round(pct_scrutinio, 2),
            "attendibilita_statistica": attendibilita_modello  # Nuova chiave allineata
        },
        "stime_finali": [
            {
                "candidato": "Simone Venturini", 
                "percentuale_stata": v_perc, 
                "swing_rispetto_storico": round(v_perc - 45.0, 2)
            },
            {
                "candidato": "Andrea Martella", 
                "percentuale_stata": m_perc, 
                "swing_rispetto_storico": round(m_perc - 42.0, 2)
            },
            {
                "candidato": "Altri Candidati", 
                "percentuale_stata": resto, 
                "swing_rispetto_storico": 0.0
            }
        ]
    }
    
    # Scrive lo snapshot simulato su disco
    with open("dati_dashboard.json", "w", encoding="utf-8") as f:
        json.dump(dati_test, f, indent=4, ensure_ascii=False)
        
    print(f"📦 Sezioni: {sezioni_pervenute}/{sezioni_totali} ({pct_scrutinio:.1f}%) ➔ Attendibilità Modello: {attendibilita_modello}%")
    
    # Aspetta 3 secondi prima del prossimo blocco di sezioni
    time.sleep(3)

print("\n🏁 Simulazione completata con successo!")