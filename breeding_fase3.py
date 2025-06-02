# breeding_fase3.py
from dataclasses import dataclass, field
from typing import List, Dict, Optional, Any, Callable

# --- Strutture Dati per la Fase 3 (Spostate da breeding_gui.py) ---
@dataclass
class PokemonBaseRichiestoF3:
    """
    Rappresenta un singolo tipo di Pokémon base teorico necessario per un piano,
    con i dettagli dei costi per procurarselo.
    """
    descrizione: str  # Descrizione testuale (es. "Solo IV: ATT (Blu)")
    stat_o_natura: str # La statistica IV specifica o la Natura
    tipo: str          # "IV" o "Natura"
    colore_ruolo_legenda: Optional[str] = None # Colore/ruolo dalla legenda (es. "Blu")
    quantita_necessaria: int = 0
    costo_femmina_target: Optional[float] = None
    costo_maschio_egg_group: Optional[float] = None
    costo_ditto: Optional[float] = None
    scelta_migliore: Optional[str] = None # Es. "Femmina Target", "Maschio Egg Group", "Ditto"
    costo_scelta_migliore: Optional[float] = None
    id_univoco_base: str = "" # ID generato per l'abbinamento con i prezzi

    def __post_init__(self):
        """
        Genera un ID univoco per questo tipo di Pokémon base, utile per l'abbinamento
        con i prezzi inseriti dall'utente.
        """
        if self.tipo == "IV":
            self.id_univoco_base = f"IV_{self.stat_o_natura}" + (f"_{self.colore_ruolo_legenda}" if self.colore_ruolo_legenda else "")
        elif self.tipo == "Natura":
            self.id_univoco_base = f"Natura_{self.stat_o_natura}"
        else:
            # Fallback per descrizioni non standard, anche se idealmente non dovrebbe accadere
            # con una corretta interpretazione delle descrizioni base.
            self.id_univoco_base = self.descrizione.replace(" ", "_").replace(":", "").replace("(", "").replace(")", "")

@dataclass
class PianoAnalizzatoF3:
    """
    Rappresenta un piano di breeding candidato dopo la Fase 2, arricchito con
    i dettagli dei costi stimati per i Pokémon base necessari (Fase 3).
    Permette l'ordinamento dei piani per trovare il migliore.
    """
    id_piano_fase1: int
    legenda_usata: Dict[str, str]
    punteggio_fase2: float
    match_fase2: int
    posseduti_usati_fase2: List[str] # Lista di ID utente dei pokemon posseduti usati
    pokemon_target_finale: Dict[str, Any] # Dati del Pokémon target finale del piano
    natura_target_globale: str
    pokemon_base_necessari_calcolati: Dict[str, int] # Conteggio dei Pokémon base teorici {desc_base: quantita}
    mappa_richiesto_a_posseduto: Dict[str, str] # Mappa {nome_formattato_richiesto: id_utente_posseduto}
    
    specie_target_piano: Optional[str] = None # Specie base del Pokémon target (per i costi)
    dettaglio_base_richiesti_con_costi: List[PokemonBaseRichiestoF3] = field(default_factory=list)
    costo_totale_stimato_base: float = 0.0
    note_compatibilita: List[str] = field(default_factory=list) # Note aggiuntive (es. prezzi mancanti)

    # Dettagli opzionali dei percorsi, se necessari per la visualizzazione finale
    percorso_A_dettagli: Optional[Dict[str, Any]] = None
    percorso_B_dettagli: Optional[Dict[str, Any]] = None


    def __lt__(self, other: 'PianoAnalizzatoF3') -> bool:
        """
        Logica di ordinamento per i piani:
        1. Punteggio Fase 2 (decrescente)
        2. Numero di Match Fase 2 (decrescente)
        3. Numero di Pokémon Posseduti Usati (decrescente - preferisce usare più posseduti se gli altri criteri sono pari)
        4. Costo Totale Stimato Base (crescente - preferisce il più economico)
        """
        if self.punteggio_fase2 != other.punteggio_fase2:
            return self.punteggio_fase2 > other.punteggio_fase2
        if self.match_fase2 != other.match_fase2:
            return self.match_fase2 > other.match_fase2
        if len(self.posseduti_usati_fase2) != len(other.posseduti_usati_fase2):
            # Preferisce piani che usano PIÙ Pokémon posseduti (quindi meno da comprare)
            # se punteggio e match sono uguali.
            return len(self.posseduti_usati_fase2) > len(other.posseduti_usati_fase2)
        return self.costo_totale_stimato_base < other.costo_totale_stimato_base

# --- Funzioni Logiche per la Fase 3 ---

def _parse_desc_base_f3(desc_base: str) -> tuple[Optional[str], str, Optional[str]]:
    """
    Interpreta la descrizione di un Pokémon base teorico per estrarne tipo, statistica/natura e colore/ruolo.
    Es: "Solo IV: ATT (Blu)" -> ("IV", "ATT", "Blu")
        "Solo Natura: Decisa" -> ("Natura", "Decisa", None)
    """
    tipo = None
    stat_o_natura = desc_base # Default
    colore = None
    try:
        if "Solo Natura:" in desc_base:
            tipo = "Natura"
            stat_o_natura = desc_base.split(": ")[1].strip()
        elif "Solo IV:" in desc_base:
            tipo = "IV"
            parts = desc_base.split(": ")[1].split("(")
            stat_o_natura = parts[0].strip()
            if len(parts) > 1:
                colore = parts[1].replace(")", "").strip()
        elif "Da Procurare" in desc_base: # Gestisce i casi di fallback
            tipo = "Da Procurare"
            # Tenta di estrarre una definizione più specifica se presente
            if "(Definizione:" in desc_base:
                 stat_o_natura = desc_base.split("(Definizione:")[1].split(")")[0].strip()
            elif "(nome:" in desc_base: # Potrebbe essere un nome formattato
                 stat_o_natura = desc_base.split("(nome:")[1].split(")")[0].strip()
            else:
                stat_o_natura = desc_base # Lascia la descrizione completa
    except IndexError:
        print(f"Avviso: Potenziale errore nel parsing della descrizione base (F3): {desc_base}")
        stat_o_natura = desc_base # Fallback
    return tipo, stat_o_natura, colore

def analizza_e_calcola_costi_piano_ottimale(
    piani_candidati_data: List[Dict[str, Any]],
    prezzi_base_raccolti_gui: Dict[str, Dict[str, Optional[float]]],
    specie_target_globale_gui: str,
    pokemon_names_list_globale: List[str],
    fn_get_base_specie: Callable[[Optional[str]], Optional[str]]
) -> Optional[PianoAnalizzatoF3]:
    """
    Analizza i piani candidati dalla Fase 2, calcola i costi stimati per i Pokémon base
    necessari utilizzando i prezzi forniti, e restituisce il piano considerato ottimale.

    Args:
        piani_candidati_data: Lista di dizionari, ognuno rappresentante un piano
                                 candidato (output di fase2_output_per_fase3.json).
        prezzi_base_raccolti_gui: Dizionario dei prezzi inseriti dall'utente nella GUI.
                                    Formato: {id_univoco_base: {"femmina_target": costo, ...}}
        specie_target_globale_gui: Nome della specie Pokémon target globale (dalla GUI).
        pokemon_names_list_globale: Lista di tutti i nomi Pokémon validi.
        fn_get_base_specie: Funzione per ottenere la specie base di un Pokémon.

    Returns:
        Un oggetto PianoAnalizzatoF3 rappresentante il piano ottimale, o None se nessun
        piano valido può essere determinato.
    """
    if not piani_candidati_data:
        return None

    piani_analizzati_f3: List[PianoAnalizzatoF3] = []

    for piano_data in piani_candidati_data:
        try:
            piano_obj = PianoAnalizzatoF3(
                id_piano_fase1=piano_data["id_piano_fase1"],
                legenda_usata=piano_data["legenda_usata"],
                punteggio_fase2=piano_data["punteggio_ottenuto"],
                match_fase2=piano_data["pokemon_matchati_count"],
                posseduti_usati_fase2=piano_data["id_pokemon_posseduti_usati_unici"],
                pokemon_target_finale=piano_data["pokemon_target_finale_piano"],
                natura_target_globale=piano_data["natura_target_specifica_del_piano_globale"],
                pokemon_base_necessari_calcolati=piano_data["pokemon_base_necessari_calcolati"],
                mappa_richiesto_a_posseduto=piano_data.get("mappa_richiesto_a_posseduto", {}),
                percorso_A_dettagli=piano_data.get("percorso_A_dettagli"),
                percorso_B_dettagli=piano_data.get("percorso_B_dettagli")
            )
        except KeyError as e:
            print(f"Errore: Chiave mancante nei dati del piano candidato durante la creazione di PianoAnalizzatoF3: {e}")
            print(f"Dati del piano problematico: {piano_data}")
            continue # Salta questo piano se i dati sono incompleti

        # Determina la specie target per questo specifico piano (per i costi)
        specie_target_effettiva = specie_target_globale_gui
        if not specie_target_effettiva: # Prova a dedurla dal piano se non inserita globalmente
            nome_target_dal_piano = piano_obj.pokemon_target_finale.get("nome_formattato_dal_piano", 
                                     piano_obj.pokemon_target_finale.get("nome_formattato", "Sconosciuta"))
            
            if "[" in nome_target_dal_piano:
                specie_potenziale = nome_target_dal_piano.split("[")[0].strip()
            else:
                specie_potenziale = nome_target_dal_piano.strip()

            colori_comuni_prefisso = ["Verde", "Blu", "Rosso", "Giallo", "Grigio", "Arancione", 
                                      "Natura", "IV"] 
            for colore_prefix in colori_comuni_prefisso:
                if specie_potenziale.startswith(colore_prefix):
                    test_specie = specie_potenziale[len(colore_prefix):]
                    if test_specie in pokemon_names_list_globale or \
                       any(test_specie.startswith(cp) for cp in colori_comuni_prefisso):
                        specie_potenziale = test_specie

            if specie_potenziale in pokemon_names_list_globale:
                specie_target_effettiva = specie_potenziale
            else: 
                specie_target_effettiva = "Sconosciuta"
        
        piano_obj.specie_target_piano = fn_get_base_specie(specie_target_effettiva)


        piano_obj.costo_totale_stimato_base = 0.0
        piano_obj.dettaglio_base_richiesti_con_costi = []
        piano_obj.note_compatibilita = []

        for desc_base_teorico, quantita in piano_obj.pokemon_base_necessari_calcolati.items():
            if quantita <= 0: 
                continue

            tipo_base, stat_nat_base, colore_ruolo_base = _parse_desc_base_f3(desc_base_teorico)
            
            if tipo_base == "IV":
                id_base_prezzo = f"IV_{stat_nat_base}" + (f"_{colore_ruolo_base}" if colore_ruolo_base else "")
            elif tipo_base == "Natura":
                id_base_prezzo = f"Natura_{stat_nat_base}"
            else: 
                id_base_prezzo = desc_base_teorico.replace(" ", "_").replace(":", "").replace("(", "").replace(")", "")


            prezzi_opzioni_per_base = prezzi_base_raccolti_gui.get(id_base_prezzo, {})
            
            dettaglio_pkmn_base = PokemonBaseRichiestoF3(
                descrizione=desc_base_teorico, 
                stat_o_natura=stat_nat_base, 
                tipo=tipo_base or "Sconosciuto", 
                colore_ruolo_legenda=colore_ruolo_base, 
                quantita_necessaria=quantita,
                id_univoco_base=id_base_prezzo 
            )

            if tipo_base == "Da Procurare": 
                dettaglio_pkmn_base.scelta_migliore = "Da Procurare Manualmente"
                dettaglio_pkmn_base.costo_scelta_migliore = 0 
                piano_obj.note_compatibilita.append(f"'{desc_base_teorico}' deve essere procurato/analizzato manualmente.")
            else: 
                opzioni_costo_valide = []
                costo_f = prezzi_opzioni_per_base.get("femmina_target")
                if costo_f is not None:
                    opzioni_costo_valide.append({"costo": costo_f, "tipo": f"Femmina {piano_obj.specie_target_piano}"})
                    dettaglio_pkmn_base.costo_femmina_target = costo_f
                
                costo_m = prezzi_opzioni_per_base.get("maschio_egg")
                if costo_m is not None:
                    opzioni_costo_valide.append({"costo": costo_m, "tipo": "Maschio Egg Group"})
                    dettaglio_pkmn_base.costo_maschio_egg_group = costo_m

                costo_d = prezzi_opzioni_per_base.get("ditto")
                if costo_d is not None:
                    opzioni_costo_valide.append({"costo": costo_d, "tipo": "Ditto"})
                    dettaglio_pkmn_base.costo_ditto = costo_d
                
                if opzioni_costo_valide:
                    opzioni_costo_valide.sort(key=lambda x: x["costo"])
                    dettaglio_pkmn_base.costo_scelta_migliore = opzioni_costo_valide[0]["costo"]
                    dettaglio_pkmn_base.scelta_migliore = opzioni_costo_valide[0]["tipo"]
                    # CORREZIONE: Controlla se costo_scelta_migliore è valido prima di moltiplicare
                    if dettaglio_pkmn_base.costo_scelta_migliore is not None:
                        piano_obj.costo_totale_stimato_base += dettaglio_pkmn_base.costo_scelta_migliore * quantita
                else:
                    dettaglio_pkmn_base.scelta_migliore = "Non Prezzato"
                    piano_obj.note_compatibilita.append(f"ATTENZIONE: Nessun prezzo per '{desc_base_teorico}' (ID: {id_base_prezzo}). Costo non calcolato per questo componente.")
            
            piano_obj.dettaglio_base_richiesti_con_costi.append(dettaglio_pkmn_base)
        
        piani_analizzati_f3.append(piano_obj)

    if not piani_analizzati_f3:
        return None

    piani_analizzati_f3.sort() 
    
    return piani_analizzati_f3[0]
