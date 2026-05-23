import json
import time
import random

print("🚀 Simulatore di spoglio avviato. Premi CTRL+C per interrompere.")

sezioni_totali = 256
for sezioni_pervenute in range(1, sezioni_totali + 1, 5):
    percentuale = round((sezioni_pervenute / sezioni_totali) * 100, 2)
    
    # Genera percentuali plausibili che oscillano leggermente
    v_perc = round(random.uniform(43.0, 47.0), 2)
    m_perc = round(random.uniform(40.0, 44.0), 2)
    resto = 100.0 - v_perc - m_perc
    
    dati_test = {
        "ultimo_aggiornamento": time.strftime("%H:%M:%S"),
        "scrutinio": {
            "sezioni_pervenute": sezioni_pervenute,
            "totale_sezioni": sezioni_totali,
            "percentuale_completamento": percentuale
        },
        "stime_finali": [
            {"candidato": "Simone Venturini", "percentuale_stata": v_perc, "swing_rispetto_storico": round(v_perc - 45.0, 2)},
            {"candidato": "Andrea Martella", "percentuale_stata": m_perc, "swing_rispetto_storico": round(m_perc - 42.0, 2)},
            {"candidato": "Altri Candidati", "percentuale_stata": resto, "swing_rispetto_storico": 0.0}
        ]
    }
    
    # Scrive lo snapshot simulato
    with open("dati_dashboard.json", "w", encoding="utf-8") as f:
        json.dump(dati_test, f, indent=4)
        
    print(f"📦 Scritto snapshot: {sezioni_pervenute}/{sezioni_totali} sezioni ({percentuale}%)")
    time.sleep(3)  # Aggiorna ogni 3 secondi