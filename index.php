<!DOCTYPE html>
<html lang="it">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Control Room Elettorale - Sindaco di Venezia 2026</title>
    <script src="https://cdn.jsdelivr.net/npm/@tailwindcss/browser@4"></script>
    <link href="https://fonts.googleapis.com/icon?family=Material+Icons+Round" rel="stylesheet">
</head>
<body class="bg-slate-50 text-slate-800 font-sans antialiased">

    <!-- TOP APP BAR -->
    <header class="bg-white shadow-xs border-b border-slate-200 sticky top-0 z-50 px-4 py-3.5 flex justify-between items-center">
        <div class="flex items-center gap-3">
            <button class="p-2 hover:bg-slate-100 rounded-full transition cursor-pointer" onclick="toggleMenu()">
                <span class="material-icons-round text-slate-600">menu</span>
            </button>
            <div>
                <h1 class="text-xl font-bold tracking-tight text-slate-900">Elettorando <span class="text-indigo-600">2026</span></h1>
                <p class="text-xs text-slate-500 font-medium tracking-wide uppercase">Elezione del Sindaco di Venezia • Live Spoglio</p>
            </div>
        </div>
        <div id="status-badge" class="flex items-center gap-2 text-sm text-slate-600 bg-slate-100 px-3.5 py-1.5 rounded-full font-medium">
            <span class="w-2 h-2 rounded-full bg-emerald-500 animate-pulse"></span>
            Dati Live Aggiornati
        </div>
    </header>

    <!-- ARCHIVIO SIDEBAR -->
    <div id="sidebar" class="fixed inset-y-0 left-0 w-80 bg-white shadow-2xl transform -translate-x-full transition-transform duration-300 ease-in-out z-50 border-r border-slate-200 pt-24">
        <div class="px-5 mb-4 flex justify-between items-center">
            <h2 class="font-bold text-lg text-slate-800 tracking-tight">Archivio Storico Previsioni</h2>
            <button onclick="toggleMenu()" class="p-1 hover:bg-slate-100 rounded-full cursor-pointer"><span class="material-icons-round">close</span></button>
        </div>
        <nav class="space-y-1.5 px-3">
            <a href="index.php" class="flex items-center justify-between p-3.5 rounded-xl bg-indigo-50 text-indigo-700 font-semibold text-sm">
                <span class="flex items-center gap-2"><span class="material-icons-round text-base">analytics</span>Previsione Attuale</span>
                <span class="text-[10px] bg-indigo-200 text-indigo-800 px-2 py-0.5 rounded-md font-bold uppercase tracking-wider">Live</span>
            </a>
            
            <!-- PHP SCRUTA LA CARTELLA STORICO E GENERA I LINK DINAMICAMENTE -->
            <?php
            $dir = 'storico/';
            if (is_dir($dir)) {
                $files = glob($dir . 'snapshot_*.json');
                rsort($files); // Mostra i più recenti in alto
                
                foreach ($files as $file) {
                    // Estrae l'orario dal nome del file per renderlo leggibile (es: snapshot_163012.json -> 16:30:12)
                    preg_match('/snapshot_(\d{2})(\d{2})(\d{2})\.json/', $file, $matches);
                    if ($matches) {
                        $ora_formattata = "Proiezione delle {$matches[1]}:{$matches[2]}:{$matches[3]}";
                        $nome_file_pulito = basename($file);
                        
                        echo "<a href='#' onclick=\"caricaSnapshotStorico('$nome_file_pulito'); toggleMenu(); return false;\" class='flex items-center gap-2 p-3 text-sm rounded-xl text-slate-600 hover:bg-slate-50 transition border border-transparent hover:border-slate-100'>";
                        echo "<span class='material-icons-round text-slate-400 text-base'>history</span> $ora_formattata";
                        echo "</a>";
                    }
                }
            }
            ?>
        </nav>
    </div>

    <!-- MAIN CONTAINER -->
    <!-- MAIN CONTAINER -->
    <main class="max-w-5xl mx-auto p-4 md:p-8 space-y-8 relative">

        <!-- SCHERMATA DI ATTESA SOGLIA MINIMA SEZIONI -->
        <div id="blocco-sezioni" class="hidden bg-slate-50/95 backdrop-blur-xs absolute inset-0 z-40 flex flex-col items-center justify-center text-center p-6 min-h-[60vh]">
            <div class="bg-white p-8 rounded-2xl shadow-xl border border-slate-200 max-w-md space-y-4">
                <span class="material-icons-round text-5xl text-indigo-500 animate-spin">hourglass_top</span>
                <h3 class="text-xl font-bold text-slate-900">Dati insufficienti per la proiezione</h3>
                <p class="text-sm text-slate-600 leading-relaxed">
                    Il modello statistico richiede l'afflusso di almeno <b>5 sezioni scrutinate</b> per elaborare la prima proiezione affidabile dello swing comunale.
                </p>
                <div class="bg-slate-100 px-4 py-2 rounded-xl text-xs font-bold text-slate-700 inline-block" id="conteggio-attesa">
                    Sezioni attuali: 0 / 5
                </div>
            </div>
        </div>

        <!-- BANNER STATO ELEZIONI E ATTENDIBILITÀ -->
        <div class="bg-white rounded-2xl shadow-xs border border-slate-200 p-6 flex flex-col md:flex-row md:items-center justify-between gap-6">
            <div class="space-y-1.5">
                <div class="text-[11px] font-bold uppercase tracking-wider text-indigo-600 bg-indigo-50 px-2.5 py-1 rounded-md inline-block">Proiezione Algoritmica</div>
                <div class="text-lg font-bold text-slate-800 flex items-center gap-2" id="aggiornamento">
                    <span class="material-icons-round text-slate-400">calendar_today</span>
                    In attesa di dati...
                </div>
                <p class="text-sm text-slate-500" id="sottotitolo-sezioni">Caricamento del flusso sezionale in corso.</p>
            </div>
            
            <!-- Barra Attendibilità Statistica -->
            <div class="w-full md:w-64 space-y-2">
                <div class="flex justify-between text-sm font-semibold">
                    <span class="text-slate-600">Attendibilità Modello</span>
                    <span class="text-indigo-600 font-bold" id="attendibilita-valore">0%</span>
                </div>
                <div class="w-full bg-slate-100 rounded-full h-2.5">
                    <div id="attendibilita-barra" class="bg-indigo-600 h-2.5 rounded-full transition-all duration-500" style="width: 0%"></div>
                </div>
            </div>

            <!-- Box Scenario Sintetico -->
            <div class="bg-amber-50 border border-amber-200 rounded-xl p-4 flex items-center gap-3.5 md:w-64">
                <span class="material-icons-round text-amber-500 text-3xl">hourglass_empty</span>
                <div>
                    <div class="text-[10px] font-bold text-amber-800 uppercase tracking-wider">Esito Più Probabile</div>
                    <div class="text-base font-bold text-slate-800" id="scenario-testo">Calcolo...</div>
                </div>
            </div>
        </div>

        <!-- IL BOX DELLA "CALL" (ATTIVATO AUTOMATICAMENTE DA COSTRUTTO JSON) -->
        <div id="box-call" class="bg-linear-to-r from-red-600 to-red-700 text-white rounded-2xl shadow-md p-6 flex flex-col md:flex-row items-center justify-between gap-4 animate-pulse hidden">
            <div class="flex items-center gap-4 text-center md:text-left flex-col md:flex-row">
                <span class="material-icons-round text-4xl bg-white/20 p-2 rounded-full">campaign</span>
                <div>
                    <h3 class="text-xl font-black tracking-tight uppercase">PROJECTED WINNER (CALL)</h3>
                    <p class="text-sm opacity-90 font-medium">L'intervallo di confidenza statistica ha isolato l'esito finale escludendo scenari alternativi.</p>
                </div>
            </div>
            <div class="text-center">
                <div id="testo-call" class="text-xl font-black bg-white text-red-700 px-5 py-2.5 rounded-xl shadow-xs uppercase tracking-wider">
                    -
                </div>
            </div>
        </div>

        <!-- SEZIONE GRAFICI DI SFONDAMENTO SOGLIA PRINCIPALE (PRIME DUE FORZE) -->
        <div class="grid grid-cols-1 md:grid-cols-2 gap-6">
            <!-- Widget Sfidante Centrosinistra -->
            <div class="bg-white p-6 rounded-2xl shadow-xs border border-slate-200 space-y-4">
                <div class="flex justify-between items-end">
                    <div>
                        <h4 class="text-xs font-bold text-slate-400 uppercase tracking-wider">Andrea Martella</h4>
                        <div class="text-xs font-semibold text-red-600 bg-red-50 px-2 py-0.5 rounded-md inline-block mt-1">Centrosinistra</div>
                    </div>
                    <div class="text-4xl font-black text-slate-800 tracking-tight" id="martella-perc">0.00%</div>
                </div>
                <div class="relative pt-3">
                    <div class="w-full bg-slate-100 h-4 rounded-full overflow-hidden">
                        <div id="martella-barra" class="bg-red-500 h-4 rounded-full transition-all duration-500" style="width: 0%"></div>
                    </div>
                    <div class="absolute top-0 bottom-0 left-1/2 w-0.5 bg-slate-400 border-dashed border-l"></div>
                </div>
                <div class="flex justify-between text-xs text-slate-500 font-medium">
                    <span>Soglia 1° Turno (50%)</span>
                    <span id="martella-notifica" class="text-red-600 font-bold">-</span>
                </div>
            </div>

            <!-- Widget Candidato Centrodestra -->
            <div class="bg-white p-6 rounded-2xl shadow-xs border border-slate-200 space-y-4">
                <div class="flex justify-between items-end">
                    <div>
                        <h4 class="text-xs font-bold text-slate-400 uppercase tracking-wider">Simone Venturini</h4>
                        <div class="text-xs font-semibold text-blue-600 bg-blue-50 px-2 py-0.5 rounded-md inline-block mt-1">Centrodestra</div>
                    </div>
                    <div class="text-4xl font-black text-slate-800 tracking-tight" id="venturini-perc">0.00%</div>
                </div>
                <div class="relative pt-3">
                    <div class="w-full bg-slate-100 h-4 rounded-full overflow-hidden">
                        <div id="venturini-barra" class="bg-blue-500 h-4 rounded-full transition-all duration-500" style="width: 0%"></div>
                    </div>
                    <div class="absolute top-0 bottom-0 left-1/2 w-0.5 bg-slate-400 border-dashed border-l"></div>
                </div>
                <div class="flex justify-between text-xs text-slate-500 font-medium">
                    <span>Soglia 1° Turno (50%)</span>
                    <span id="venturini-notifica" class="text-blue-600 font-bold">-</span>
                </div>
            </div>
        </div>

        <!-- TABELLA DETTAGLIATA MULTI-CANDIDATO -->
        <div class="bg-white rounded-2xl shadow-xs border border-slate-200 overflow-hidden">
            <div class="px-6 py-4.5 border-b border-slate-100 bg-slate-50/70">
                <h3 class="font-bold text-slate-800 tracking-tight">Quadro Analitico su base Comunale (8 Candidati)</h3>
            </div>
            <div class="overflow-x-auto">
                <table class="w-full text-left border-collapse">
                    <thead>
                        <tr class="text-[11px] font-bold text-slate-400 uppercase tracking-wider bg-slate-50/40 border-b border-slate-100">
                            <th class="p-4 pl-6">Candidato Sindaco</th>
                            <th class="p-4 text-right">Stima Proiettata</th>
                            <th class="p-4 text-right pr-6">Swing Live (vs Storico)</th>
                        </tr>
                    </thead>
                    <tbody id="tabella-corpo" class="divide-y divide-slate-100 text-sm font-medium">
                        <!-- Generato dinamicamente da JS -->
                    </tbody>
                </table>
            </div>
        </div>

        <!-- NOTA TECNICA -->
        <section class="bg-white rounded-2xl shadow-xs border border-slate-200 p-6 md:p-8 space-y-6">
            <div class="flex flex-col md:flex-row md:items-center justify-between gap-4 border-b border-slate-100 pb-4">
                <div class="flex items-center gap-3">
                    <span class="material-icons-round text-indigo-600 text-2xl">menu_book</span>
                    <h3 class="text-lg font-bold text-slate-800 tracking-tight">Nota di Documentazione Tecnica</h3>
                </div>
                <div class="flex items-center gap-2 text-xs font-semibold text-slate-500 bg-slate-100 px-3 py-1.5 rounded-lg">
                    <span class="material-icons-round text-sm text-indigo-500">cloud_download</span>
                    Fonte dati scrutinio grezzo: <a href="https://elezioni.comune.venezia.it" target="_blank" class="text-indigo-600 hover:underline ml-0.5">elezioni.comune.venezia.it</a>
                </div>
            </div>
            <p class="text-sm text-slate-600 leading-relaxed">
                Questo portale applica modelli statistici di inferenza geopolitica ed estrapolazione dello <i>swing</i> per interpretare lo scrutinio in tempo reale delle elezioni comunali di Venezia del <b>24-25 maggio 2026</b>. L'obiettivo è superare la distorsione ottica dei primi dati parziali affluiti, offrendo una proiezione stabilizzata del risultato finale cittadino.
            </p>
        </section>
    </main>

    <!-- FOOTER -->
    <footer class="max-w-5xl mx-auto px-4 md:px-8 pb-12 text-center text-xs text-slate-400 font-medium space-y-1">
        <p>Copyleft 2026 pcc soft • Tutti i diritti di riproduzione e modifica sono liberi.</p>
    </footer>

    <!-- INTERAZIONE LOGICA LIVE DINAMICA (AJAX FETCH) -->
    <script>
let intervalloPolling; // Variabile globale per gestire il timer del live

function toggleMenu() {
    document.getElementById('sidebar').classList.toggle('-translate-x-full');
}

// ========================================================
// 1. FUNZIONE CORE: AGGIORNA GLI ELEMENTI GRAFICI SULLA PAGINA
// ========================================================
function aggiornaInterfacciaGrafica(dati) {
    if (!dati || !dati.scrutinio || !dati.stime_finali) {
        console.error("Struttura dati JSON non valida.");
        return;
    }

    const sezioni = dati.scrutinio.sezioni_pervenute;
    const bloccoSezioni = document.getElementById('blocco-sezioni');
    const conteggioAttesa = document.getElementById('conteggio-attesa');

    // CONTROLLO SOGLIA MINIMA: 5 SEZIONI
    if (sezioni < 5) {
        // 1. Mostra la schermata di attesa blocca-interfaccia
        if (bloccoSezioni) bloccoSezioni.classList.remove('hidden');
        if (conteggioAttesa) conteggioAttesa.innerText = `Sezioni pervenute attualmente: ${sezioni} / 5`;

        // 2. Aggiorna comunque le informazioni minime nella barra in alto per far capire che il sistema è vivo
        document.getElementById('aggiornamento').innerHTML = `<span class="material-icons-round text-slate-400">calendar_today</span> Lunedì 25 Maggio 2026 — ${dati.ultimo_aggiornamento}`;
        document.getElementById('sottotitolo-sezioni').innerText = `Flusso parziale insufficiente (${sezioni} sezioni ricevute).`;
        document.getElementById('attendibilita-valore').innerText = "0.0%";
        document.getElementById('attendibilita-barra').style.width = "0%";
        document.getElementById('scenario-testo').innerText = "In attesa di quorum...";
        return; // Interrompe l'aggiornamento dei grafici sottostanti
    } else {
        // Se le sezioni sono >= 5, nasconde l'overlay e procede normalmente
        if (bloccoSezioni) bloccoSezioni.classList.add('hidden');
    }

    // A. Aggiorna Informazioni di Stato...
    document.getElementById('aggiornamento').innerHTML = `<span class="material-icons-round text-slate-400">calendar_today</span> Lunedì 25 Maggio 2026 — ${dati.ultimo_aggiornamento}`;
    document.getElementById('sottotitolo-sezioni').innerText = `Stima basata sul flusso di ${dati.scrutinio.sezioni_pervenute} sezioni su ${dati.scrutinio.totale_sezioni} (${dati.scrutinio.percentuale_completamento}%).`;
    
    // B. Legge l'attendibilità statistica logistica
    const attendibilita = dati.scrutinio.attendibilita_statistica;
    document.getElementById('attendibilita-valore').innerText = attendibilita.toFixed(1) + "%";
    
    // Forziamo il rendering della transizione CSS con un mini-timeout
    setTimeout(() => {
        document.getElementById('attendibilita-barra').style.width = attendibilita + "%";
    }, 50);
    
    // C. Determina lo scenario testuale basandosi sulla vera attendibilità del modello
    let scenarioTesto = "In attesa di dati...";
    if (attendibilita > 0) {
        if (attendibilita < 25) scenarioTesto = "Primi dati (Instabile)";
        else if (attendibilita < 55) scenarioTesto = "Consolidamento proiezioni: media attendibilità";
        else if (attendibilita < 75) scenarioTesto = "Buona attendibilità";
        else scenarioTesto = "Modello altamente stabile";
    }
    document.getElementById('scenario-testo').innerText = scenarioTesto;

    // D. Gestione Logica della "CALL"
    const boxCall = document.getElementById('box-call');
    const primo = dati.stime_finali[0];
    const secondo = dati.stime_finali[1];
    
    if (attendibilita >= 15.0 && primo && secondo && (primo.percentuale_stata >= 50.0 || (primo.percentuale_stata - secondo.percentuale_stata) > 8.0)) {
        document.getElementById('testo-call').innerText = primo.candidato + " PROIETTATO VINCENTE";
        boxCall.classList.remove('hidden');
    } else {
        boxCall.classList.add('hidden');
    }

    // E. Aggiorna i due candidati principali (Case-Insensitive per evitare bug di battitura)
    const martella = dati.stime_finali.find(c => c.candidato.toLowerCase().includes("martella")) || { percentuale_stata: 0 };
    const venturini = dati.stime_finali.find(c => c.candidato.toLowerCase().includes("venturini")) || { percentuale_stata: 0 };

    document.getElementById('martella-perc').innerText = martella.percentuale_stata.toFixed(2) + "%";
    document.getElementById('venturini-perc').innerText = venturini.percentuale_stata.toFixed(2) + "%";
    
    setTimeout(() => {
        document.getElementById('martella-barra').style.width = Math.min(martella.percentuale_stata, 100) + "%";
        document.getElementById('venturini-barra').style.width = Math.min(venturini.percentuale_stata, 100) + "%";
    }, 50);

    document.getElementById('martella-notifica').innerText = martella.percentuale_stata >= 50 ? "Vittoria al primo turno proiettata" : `${(50 - martella.percentuale_stata).toFixed(2)}% per evitare il ballottaggio`;
    document.getElementById('venturini-notifica').innerText = venturini.percentuale_stata >= 50 ? "Vittoria al primo turno proiettata" : `${(50 - venturini.percentuale_stata).toFixed(2)}% per evitare il ballottaggio`;

    // F. Generazione dinamica delle righe della tabella per tutti gli 8 candidati
    const corpoTabella = document.getElementById('tabella-corpo');
    corpoTabella.innerHTML = "";

    dati.stime_finali.forEach(cand => {
        const swing = cand.swing_rispetto_storico;
        const segnoSwing = swing >= 0 ? "+" : "";
        const coloreSwing = swing >= 0 ? "text-emerald-500" : "text-red-500";
        const testoSwing = swing === 0 ? "= 0.00%" : `${segnoSwing}${swing.toFixed(2)}%`;
        
        const riga = `
            <tr class="hover:bg-slate-50/50 transition">
                <td class="p-4 pl-6 font-bold text-slate-900">${cand.candidato}</td>
                <td class="p-4 text-right font-black text-slate-900 text-base">${cand.percentuale_stata.toFixed(2)}%</td>
                <td class="p-4 text-right pr-6 ${coloreSwing} text-xs font-bold">${testoSwing}</td>
            </tr>
        `;
        corpoTabella.innerHTML += riga;
    });
}

// ========================================================
// 2. RECUPERO LIVE DATI (POLLING STANDARD)
// ========================================================
async function caricaDatiLive() {
    try {
        const risposta = await fetch('dati_dashboard.json?t=' + new Date().getTime());
        if (!risposta.ok) throw new Error("File JSON non trovato");
        const dati = await risposta.json();

        // Esegue il rendering grafico dei dati appena scaricati
        aggiornaInterfacciaGrafica(dati);

        // Ripristina lo stato visivo del badge su Live
        document.getElementById('status-badge').className = "flex items-center gap-2 text-sm text-emerald-700 bg-emerald-50 px-3.5 py-1.5 rounded-full font-medium";
        document.getElementById('status-badge').innerHTML = `<span class="w-2 h-2 rounded-full bg-emerald-500 animate-pulse"></span> Dati Live Aggiornati`;

    } catch (errore) {
        console.error("Errore nel caricamento dei dati live:", errore);
        document.getElementById('status-badge').className = "flex items-center gap-2 text-sm text-red-700 bg-red-50 px-3.5 py-1.5 rounded-full font-medium";
        document.getElementById('status-badge').innerHTML = `<span class="w-2 h-2 rounded-full bg-red-500"></span> Errore di sincronizzazione`;
    }
}

// ========================================================
// 3. FUNZIONE DI NAVIGAZIONE NEL TEMPO (MENU STORICO)
// ========================================================
async function caricaSnapshotStorico(nomeFile) {
    // 1. Blocchiamo il caricamento automatico live in background per non sovrascrivere lo storico
    clearInterval(intervalloPolling); 
    
    try {
        const risposta = await fetch('storico/' + nomeFile + '?t=' + new Date().getTime());
        if (!risposta.ok) throw new Error("Snapshot storico non trovato");
        const dati = await risposta.json();
        
        // 2. Ridisegna l'interfaccia usando il JSON del passato
        aggiornaInterfacciaGrafica(dati); 
        
        // 3. Modifica il badge in alto per ricordare all'utente che è "nel passato"
        document.getElementById('status-badge').className = "flex items-center gap-2 text-sm text-amber-700 bg-amber-50 px-3.5 py-1.5 rounded-full font-medium";
        document.getElementById('status-badge').innerHTML = `
            <span class="w-2 h-2 rounded-full bg-amber-500"></span> 
            Consultazione Archivio 
            <a href="index.php" class="ml-2 underline text-amber-900 font-bold hover:text-black">Torna al Live</a>
        `;
        
    } catch (e) {
        console.error("Errore nel recupero dello snapshot:", e);
    }
}

// ========================================================
// INITIALIZATION
// ========================================================
document.addEventListener("DOMContentLoaded", () => {
    caricaDatiLive();
    intervalloPolling = setInterval(caricaDatiLive, 30000);
});
</script>
</body>
</html>