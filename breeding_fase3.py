# breeding_fase3.py
from dataclasses import dataclass, field
from typing import List, Dict, Optional, Any, Callable

# --- Strutture Dati per la Fase 3 (Spostate da breeding_gui.py) ---
@dataclass
class PokemonBaseRichiestoF3:
    descrizione: str
    stat_o_natura: str
    tipo: str
    colore_ruolo_legenda: Optional[str] = None
    quantita_necessaria: int = 0 # Verrà impostato a 1 per istanza, o aggregato successivamente
    costo_femmina_specie_target: Optional[float] = None
    costo_maschio_specie_target: Optional[float] = None
    costo_femmina_egg_group: Optional[float] = None
    costo_maschio_egg_group: Optional[float] = None
    costo_ditto: Optional[float] = None
    scelta_migliore: Optional[str] = None
    costo_scelta_migliore: Optional[float] = None
    id_univoco_base: str = "" # ID per abbinare ai prezzi GUI (es. IV_ATT_Blu, Natura_Decisa)
    sesso_assegnato: Optional[str] = None # Sesso determinato dalla logica di Fase 3

    def __post_init__(self):
        # L'ID univoco ora dovrebbe essere calcolato in base alla descrizione/stat/colore del Pokémon base effettivo
        # Questa logica potrebbe dover essere richiamata quando si crea l'istanza PokemonBaseRichiestoF3
        # basandosi sui dati del pkmn_instance_dict
        if not self.id_univoco_base: # Calcola solo se non già fornito
            if self.tipo == "IV":
                self.id_univoco_base = f"IV_{self.stat_o_natura}" + (f"_{self.colore_ruolo_legenda}" if self.colore_ruolo_legenda else "")
            elif self.tipo == "Natura":
                self.id_univoco_base = f"Natura_{self.stat_o_natura}"
            else:
                # Fallback, potrebbe essere necessario un modo più robusto se la descrizione non è standard
                self.id_univoco_base = self.descrizione.replace(" ", "_").replace(":", "").replace("(", "").replace(")", "")


@dataclass
class PianoAnalizzatoF3:
    id_piano_fase1: int
    legenda_usata: Dict[str, str]
    punteggio_fase2: float
    match_fase2: int
    posseduti_usati_fase2: List[str]
    pokemon_target_finale: Dict[str, Any]
    natura_target_globale: str
    pokemon_base_necessari_calcolati: Dict[str, int] # Può ancora essere utile per la GUI
    mappa_richiesto_a_posseduto: Dict[str, str]

    specie_target_piano: Optional[str] = None
    dettaglio_base_richiesti_con_costi: List[PokemonBaseRichiestoF3] = field(default_factory=list)
    costo_totale_stimato_base: float = 0.0
    note_compatibilita: List[str] = field(default_factory=list)

    percorso_A_dettagli: Optional[Dict[str, Any]] = None
    percorso_B_dettagli: Optional[Dict[str, Any]] = None

    def __lt__(self, other: 'PianoAnalizzatoF3') -> bool:
        if self.punteggio_fase2 != other.punteggio_fase2:
            return self.punteggio_fase2 > other.punteggio_fase2
        if self.match_fase2 != other.match_fase2:
            return self.match_fase2 > other.match_fase2
        if len(self.posseduti_usati_fase2) != len(other.posseduti_usati_fase2):
            return len(self.posseduti_usati_fase2) > len(other.posseduti_usati_fase2)
        return self.costo_totale_stimato_base < other.costo_totale_stimato_base

# --- Funzioni Ausiliarie ---

def _get_all_pokemon_instances(piano_obj: PianoAnalizzatoF3) -> List[Dict[str, Any]]:
    """Estrae tutti i dizionari Pokémon unici dai percorsi del piano."""
    all_instances_map: Dict[str, Dict[str, Any]] = {} # Usa la mappa per unicità basata sul nome

    percorsi_dettagli = []
    if piano_obj.percorso_A_dettagli and piano_obj.percorso_A_dettagli.get('valido'):
        percorsi_dettagli.append(piano_obj.percorso_A_dettagli)
    if piano_obj.percorso_B_dettagli and piano_obj.percorso_B_dettagli.get('valido'):
        percorsi_dettagli.append(piano_obj.percorso_B_dettagli)

    for percorso in percorsi_dettagli:
        for livello in percorso.get('livelli', []):
            for accoppiamento in livello.get('accoppiamenti', []):
                for key in ['genitore1_richiesto', 'genitore2_richiesto', 'figlio_generato']:
                    pkmn_dict = accoppiamento.get(key)
                    if pkmn_dict and isinstance(pkmn_dict, dict):
                        nome_formattato = pkmn_dict.get('nome_formattato_dal_piano')
                        if nome_formattato and nome_formattato not in all_instances_map:
                             all_instances_map[nome_formattato] = pkmn_dict

    # Anche il target finale del piano è un'istanza
    target_finale_dict = piano_obj.pokemon_target_finale
    if target_finale_dict and isinstance(target_finale_dict, dict):
        nome_formattato = target_finale_dict.get('nome_formattato_dal_piano')
        if nome_formattato and nome_formattato not in all_instances_map:
            all_instances_map[nome_formattato] = target_finale_dict

    return list(all_instances_map.values())


def _is_pokemon_ditto(pokemon_dict: Dict[str, Any]) -> bool:
    if not pokemon_dict: return False
    nome = pokemon_dict.get('nome_formattato_dal_piano', '')
    return "ditto" in nome.lower()

def _determine_id_base_prezzo_e_tipo(pkmn_instance_dict: Dict[str, Any], legenda: Dict[str,str]) -> tuple[Optional[str], Optional[str], Optional[str], Optional[str]]:
    """Determina id_base_prezzo e tipo_base per un Pokémon istanza."""
    ivs = pkmn_instance_dict.get('ivs', [])
    natura = pkmn_instance_dict.get('natura', '')

    is_base_iv = len(ivs) == 1 and not natura
    is_base_natura = not ivs and natura

    stat_o_natura_val = None
    tipo_base_val = None
    colore_ruolo_val = None
    id_base_prezzo = None

    if is_base_iv:
        stat_o_natura_val = ivs[0]
        tipo_base_val = "IV"
        colore_ruolo_val = next((col for stat, col in legenda.items() if stat == stat_o_natura_val), None)
        id_base_prezzo = f"IV_{stat_o_natura_val}" + (f"_{colore_ruolo_val}" if colore_ruolo_val else "")
    elif is_base_natura:
        stat_o_natura_val = natura
        tipo_base_val = "Natura"
        id_base_prezzo = f"Natura_{stat_o_natura_val}"

    return id_base_prezzo, tipo_base_val, stat_o_natura_val, colore_ruolo_val


def analizza_e_calcola_costi_piano_ottimale(
    piani_candidati_data: List[Dict[str, Any]],
    prezzi_base_raccolti_gui: Dict[str, Dict[str, Optional[float]]],
    specie_target_globale_gui: str,
    pokemon_names_list_globale: List[str],
    fn_get_base_specie: Callable[[Optional[str]], Optional[str]]
) -> Optional[PianoAnalizzatoF3]:
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
                pokemon_target_finale=piano_data["pokemon_target_finale_piano"], # Questo è un Dict
                natura_target_globale=piano_data["natura_target_specifica_del_piano_globale"],
                pokemon_base_necessari_calcolati=piano_data["pokemon_base_necessari_calcolati"],
                mappa_richiesto_a_posseduto=piano_data.get("mappa_richiesto_a_posseduto", {}),
                percorso_A_dettagli=piano_data.get("percorso_A_dettagli"), # Questo è un Dict
                percorso_B_dettagli=piano_data.get("percorso_B_dettagli")  # Questo è un Dict
            )
        except KeyError as e:
            print(f"Errore: Chiave mancante nei dati del piano candidato: {e}")
            continue

        specie_target_effettiva = specie_target_globale_gui
        if not specie_target_effettiva:
            nome_target_dal_piano = piano_obj.pokemon_target_finale.get("nome_formattato_dal_piano", "Sconosciuta")
            if "[" in nome_target_dal_piano: specie_potenziale = nome_target_dal_piano.split("[")[0].strip()
            else: specie_potenziale = nome_target_dal_piano.strip()
            colori_comuni_prefisso = ["Verde", "Blu", "Rosso", "Giallo", "Grigio", "Arancione", "Natura", "IV"]
            for cp in colori_comuni_prefisso:
                if specie_potenziale.startswith(cp):
                    ts = specie_potenziale[len(cp):]
                    if ts in pokemon_names_list_globale or any(ts.startswith(c2) for c2 in colori_comuni_prefisso):
                        specie_potenziale = ts
            if specie_potenziale in pokemon_names_list_globale: specie_target_effettiva = specie_potenziale
            else: specie_target_effettiva = "Sconosciuta"
        piano_obj.specie_target_piano = fn_get_base_specie(specie_target_effettiva)

        gender_map: Dict[str, str] = {}
        percorsi_dettagli_validi = []
        if piano_obj.percorso_A_dettagli and piano_obj.percorso_A_dettagli.get('valido'):
            percorsi_dettagli_validi.append(piano_obj.percorso_A_dettagli)
        if piano_obj.percorso_B_dettagli and piano_obj.percorso_B_dettagli.get('valido'):
            percorsi_dettagli_validi.append(piano_obj.percorso_B_dettagli)

        for percorso in percorsi_dettagli_validi:
            for livello in percorso.get('livelli', []):
                for accoppiamento in livello.get('accoppiamenti', []):
                    g1_dict = accoppiamento.get('genitore1_richiesto', {})
                    g2_dict = accoppiamento.get('genitore2_richiesto', {})
                    figlio_dict = accoppiamento.get('figlio_generato', {})
                    if not g1_dict or not g2_dict: continue

                    g1_name = g1_dict.get('nome_formattato_dal_piano')
                    g2_name = g2_dict.get('nome_formattato_dal_piano')
                    figlio_name = figlio_dict.get('nome_formattato_dal_piano')

                    g1_dict.setdefault('sesso_determinato', gender_map.get(g1_name))
                    g2_dict.setdefault('sesso_determinato', gender_map.get(g2_name))

                    is_g1_ditto = _is_pokemon_ditto(g1_dict)
                    is_g2_ditto = _is_pokemon_ditto(g2_dict)

                    is_final_target_child = (figlio_name and piano_obj.pokemon_target_finale and figlio_name == piano_obj.pokemon_target_finale.get('nome_formattato_dal_piano'))

                    if is_final_target_child and piano_obj.specie_target_piano and piano_obj.specie_target_piano != "Sconosciuta":
                        if is_g1_ditto:
                            g1_dict['sesso_determinato'] = "Ditto"; gender_map[g1_name] = "Ditto"
                            g2_dict['sesso_determinato'] = "F"; gender_map[g2_name] = "F"
                        elif is_g2_ditto:
                            g2_dict['sesso_determinato'] = "Ditto"; gender_map[g2_name] = "Ditto"
                            g1_dict['sesso_determinato'] = "F"; gender_map[g1_name] = "F"
                        else:
                            g1_dict['sesso_determinato'] = "F"; gender_map[g1_name] = "F"
                            g2_dict['sesso_determinato'] = "M"; gender_map[g2_name] = "M"
                    else: # General assignment logic
                        if g1_dict['sesso_determinato'] is None and g2_dict['sesso_determinato'] is None:
                            if is_g1_ditto:
                                g1_dict['sesso_determinato'] = "Ditto"; gender_map[g1_name] = "Ditto"
                                g2_dict['sesso_determinato'] = "F"; gender_map[g2_name] = "F"
                            elif is_g2_ditto:
                                g2_dict['sesso_determinato'] = "Ditto"; gender_map[g2_name] = "Ditto"
                                g1_dict['sesso_determinato'] = "F"; gender_map[g1_name] = "F"
                            else:
                                g1_dict['sesso_determinato'] = "F"; gender_map[g1_name] = "F"
                                g2_dict['sesso_determinato'] = "M"; gender_map[g2_name] = "M"
                        elif g1_dict['sesso_determinato'] is None:
                            g1_dict['sesso_determinato'] = "Ditto" if is_g1_ditto else ("M" if g2_dict['sesso_determinato'] == "F" else "F")
                            if g1_name: gender_map[g1_name] = g1_dict['sesso_determinato']
                        elif g2_dict['sesso_determinato'] is None:
                            g2_dict['sesso_determinato'] = "Ditto" if is_g2_ditto else ("M" if g1_dict['sesso_determinato'] == "F" else "F")
                            if g2_name: gender_map[g2_name] = g2_dict['sesso_determinato']

                    if not is_g1_ditto and not is_g2_ditto and g1_dict.get('sesso_determinato') == g2_dict.get('sesso_determinato'):
                        # Conflict: make g2 the opposite gender
                        g2_new_sesso = "M" if g1_dict['sesso_determinato'] == "F" else "F"
                        g2_dict['sesso_determinato'] = g2_new_sesso
                        if g2_name: gender_map[g2_name] = g2_new_sesso

        piano_obj.costo_totale_stimato_base = 0.0
        piano_obj.dettaglio_base_richiesti_con_costi = [] # Re-initialize
        piano_obj.note_compatibilita = [] # Re-initialize

        all_pkmn_instances_in_plan = _get_all_pokemon_instances(piano_obj)
        processed_for_costing = set()

        for pkmn_instance in all_pkmn_instances_in_plan:
            instance_name = pkmn_instance.get('nome_formattato_dal_piano')
            if not instance_name or instance_name in processed_for_costing:
                continue

            if pkmn_instance.get('soddisfatto_da_posseduto', False):
                processed_for_costing.add(instance_name)
                continue

            id_base, tipo_b, stat_nat, colore_r = _determine_id_base_prezzo_e_tipo(pkmn_instance, piano_obj.legenda_usata)

            if not id_base: # Not a base Pokémon that needs buying (e.g. an intermediate with 2+ IVs)
                processed_for_costing.add(instance_name)
                continue

            sesso_assegnato_instance = pkmn_instance.get('sesso_determinato')
            prezzi_opz = prezzi_base_raccolti_gui.get(id_base, {})
            costo_scelta_instance = None
            tipo_scelta_instance = "Non Prezzato"

            # Specific price logic based on sesso_assegnato_instance
            if sesso_assegnato_instance == "F":
                costo_f_st = prezzi_opz.get("femmina_specie_target")
                costo_f_eg = prezzi_opz.get("femmina_egg_group")
                if costo_f_st is not None and (costo_f_eg is None or costo_f_st <= costo_f_eg) and piano_obj.specie_target_piano and piano_obj.specie_target_piano != "Sconosciuta": # Prioritize if target species matches
                    costo_scelta_instance = costo_f_st
                    tipo_scelta_instance = f"Femmina {piano_obj.specie_target_piano}"
                elif costo_f_eg is not None:
                    costo_scelta_instance = costo_f_eg
                    tipo_scelta_instance = "Femmina Egg Group"
            elif sesso_assegnato_instance == "M":
                costo_m_st = prezzi_opz.get("maschio_specie_target")
                costo_m_eg = prezzi_opz.get("maschio_egg_group")
                if costo_m_st is not None and (costo_m_eg is None or costo_m_st <= costo_m_eg) and piano_obj.specie_target_piano and piano_obj.specie_target_piano != "Sconosciuta":
                    costo_scelta_instance = costo_m_st
                    tipo_scelta_instance = f"Maschio {piano_obj.specie_target_piano}"
                elif costo_m_eg is not None:
                    costo_scelta_instance = costo_m_eg
                    tipo_scelta_instance = "Maschio Egg Group"
            elif sesso_assegnato_instance == "Ditto":
                costo_scelta_instance = prezzi_opz.get("ditto")
                tipo_scelta_instance = "Ditto"

            # Fallback if no gender-specific price found or sesso_assegnato_instance is None
            if costo_scelta_instance is None:
                opzioni_fallback = []
                if prezzi_opz.get("femmina_specie_target") is not None: opzioni_fallback.append({"costo": prezzi_opz["femmina_specie_target"], "tipo": f"Femmina {piano_obj.specie_target_piano}"})
                if prezzi_opz.get("maschio_specie_target") is not None: opzioni_fallback.append({"costo": prezzi_opz["maschio_specie_target"], "tipo": f"Maschio {piano_obj.specie_target_piano}"})
                if prezzi_opz.get("femmina_egg_group") is not None: opzioni_fallback.append({"costo": prezzi_opz["femmina_egg_group"], "tipo": "Femmina Egg Group"})
                if prezzi_opz.get("maschio_egg_group") is not None: opzioni_fallback.append({"costo": prezzi_opz["maschio_egg_group"], "tipo": "Maschio Egg Group"})
                if prezzi_opz.get("ditto") is not None: opzioni_fallback.append({"costo": prezzi_opz["ditto"], "tipo": "Ditto"})

                if opzioni_fallback:
                    opzioni_fallback.sort(key=lambda x: x["costo"])
                    costo_scelta_instance = opzioni_fallback[0]["costo"]
                    tipo_scelta_instance = opzioni_fallback[0]["tipo"] + " (Fallback)"
                elif not prezzi_opz: # No prices defined for this ID at all
                    tipo_scelta_instance = "Non Prezzato"
                    piano_obj.note_compatibilita.append(f"ATTENZIONE: Nessun prezzo definito per '{instance_name}' (ID: {id_base}, Sesso Richiesto: {sesso_assegnato_instance}).")
                else: # Prices defined, but none matched and no fallback applicable (e.g. all were None)
                    tipo_scelta_instance = "Nessuna Opzione Valida"
                    piano_obj.note_compatibilita.append(f"INFO: Nessuna opzione di costo valida per '{instance_name}' (ID: {id_base}, Sesso Richiesto: {sesso_assegnato_instance}).")

            if costo_scelta_instance is not None:
                piano_obj.costo_totale_stimato_base += costo_scelta_instance

            # Create PokemonBaseRichiestoF3 entry for this instance
            dettaglio_richiesto = PokemonBaseRichiestoF3(
                descrizione=instance_name, # Use the instance name as description
                stat_o_natura=stat_nat,
                tipo=tipo_b,
                colore_ruolo_legenda=colore_r,
                quantita_necessaria=1, # Each instance is one Pokémon to acquire
                id_univoco_base=id_base,
                sesso_assegnato=sesso_assegnato_instance,
                costo_scelta_migliore=costo_scelta_instance,
                scelta_migliore=tipo_scelta_instance,
                # Store all available prices for this base type for reference
                costo_femmina_specie_target=prezzi_opz.get("femmina_specie_target"),
                costo_maschio_specie_target=prezzi_opz.get("maschio_specie_target"),
                costo_femmina_egg_group=prezzi_opz.get("femmina_egg_group"),
                costo_maschio_egg_group=prezzi_opz.get("maschio_egg_group"),
                costo_ditto=prezzi_opz.get("ditto")
            )
            piano_obj.dettaglio_base_richiesti_con_costi.append(dettaglio_richiesto)
            processed_for_costing.add(instance_name)

        piani_analizzati_f3.append(piano_obj)

    if not piani_analizzati_f3:
        return None

    piani_analizzati_f3.sort()

    return piani_analizzati_f3[0]
