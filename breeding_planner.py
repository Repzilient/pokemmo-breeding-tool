import json
import itertools
import math
import os
from dataclasses import dataclass, field
from typing import List, Dict, Optional, Tuple, Any, Set
import sys
from collections import Counter

# --- Costanti per i colori nel terminale ---
GREEN_TERMINAL = '\033[32m'
YELLOW_BOLD_TERMINAL = '\033[1;33m'
GREEN_BOLD_TERMINAL = '\033[1;32m'
RESET_TERMINAL = '\033[0m'

# --- Strutture Dati Fase 1 ---
@dataclass
class PokemonJsonF1:
    nome_formattato: str = ""
    ivs: List[str] = field(default_factory=list)
    natura: str = ""

    def to_dict(self) -> Dict[str, Any]:
        return {
            "nome_formattato": self.nome_formattato,
            "ivs": sorted(list(set(self.ivs))),
            "natura": self.natura
        }

@dataclass
class AccoppiamentoJsonF1:
    genitore1_richiesto: PokemonJsonF1 = field(default_factory=PokemonJsonF1)
    genitore2_richiesto: PokemonJsonF1 = field(default_factory=PokemonJsonF1)
    figlio_generato: PokemonJsonF1 = field(default_factory=PokemonJsonF1)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "genitore1_richiesto": self.genitore1_richiesto.to_dict(),
            "genitore2_richiesto": self.genitore2_richiesto.to_dict(),
            "figlio_generato": self.figlio_generato.to_dict()
        }

@dataclass
class LivelloJsonF1:
    livello_id: int = 0
    accoppiamenti: List[AccoppiamentoJsonF1] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "livello_id": self.livello_id,
            "accoppiamenti": [acc.to_dict() for acc in self.accoppiamenti]
        }

@dataclass
class PercorsoJsonF1:
    tipo_percorso: str = ""
    risultato_percorso: PokemonJsonF1 = field(default_factory=PokemonJsonF1)
    livelli: List[LivelloJsonF1] = field(default_factory=list)
    valido: bool = False

    def to_dict(self) -> Optional[Dict[str, Any]]:
        if not self.valido:
            return None
        return {
            "tipo_percorso": self.tipo_percorso,
            "risultato_percorso": self.risultato_percorso.to_dict(),
            "livelli": [liv.to_dict() for liv in self.livelli]
        }

@dataclass
class PianoJsonF1:
    id_piano_fase1: int = 0
    legenda_usata: Dict[str, str] = field(default_factory=dict)
    percorso_A: PercorsoJsonF1 = field(default_factory=PercorsoJsonF1)
    percorso_B: PercorsoJsonF1 = field(default_factory=PercorsoJsonF1)
    pokemon_target_finale_piano: PokemonJsonF1 = field(default_factory=PokemonJsonF1)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id_piano_fase1": self.id_piano_fase1,
            "legenda_usata": self.legenda_usata,
            "percorso_A": self.percorso_A.to_dict(),
            "percorso_B": self.percorso_B.to_dict(),
            "pokemon_target_finale_piano": self.pokemon_target_finale_piano.to_dict()
        }

# --- Funzioni Helper Fase 1 ---
def colore_ruolo_per_stat_iv_f1(stat_iv: str, legenda_stat_to_colore_ruolo: Dict[str, str]) -> str:
    return legenda_stat_to_colore_ruolo.get(stat_iv, "COL_ND")

def crea_pokemon_json_f1(
    iv_stats: List[str],
    specific_nature: str,
    legenda_stat_to_colore_ruolo: Dict[str, str],
    nome_formattato_override: str = ""
) -> PokemonJsonF1:
    p = PokemonJsonF1()
    unique_sorted_ivs = sorted(list(set(iv_stats)))
    p.ivs = unique_sorted_ivs
    p.natura = specific_nature

    if nome_formattato_override:
        p.nome_formattato = nome_formattato_override
        return p

    nomi_colori_aggregati = ""
    desc_caratteristiche_aggregata = ""
    prima_caratteristica_testuale = True

    if p.natura:
        nomi_colori_aggregati += "Verde"
        desc_caratteristiche_aggregata += p.natura
        prima_caratteristica_testuale = False

    ivs_ordinate_per_desc = []
    if legenda_stat_to_colore_ruolo:
        colori_legenda_ordinati = ["Blu", "Rosso", "Giallo", "Grigio", "Arancione", "Viola"]
        iv_colore_map_temp = {iv: colore_ruolo_per_stat_iv_f1(iv, legenda_stat_to_colore_ruolo) for iv in unique_sorted_ivs}
        def sort_key_iv(iv_stat):
            colore = iv_colore_map_temp.get(iv_stat)
            try:
                return colori_legenda_ordinati.index(colore) if colore in colori_legenda_ordinati else float('inf')
            except ValueError:
                return float('inf')
        ivs_ordinate_per_desc = sorted(unique_sorted_ivs, key=sort_key_iv)
    else:
        ivs_ordinate_per_desc = unique_sorted_ivs

    for iv_stat in ivs_ordinate_per_desc:
        colore_stat = colore_ruolo_per_stat_iv_f1(iv_stat, legenda_stat_to_colore_ruolo)
        if colore_stat != "COL_ND":
             nomi_colori_aggregati += colore_stat
        if not prima_caratteristica_testuale:
            desc_caratteristiche_aggregata += "/"
        desc_caratteristiche_aggregata += iv_stat
        prima_caratteristica_testuale = False

    etichetta_statistica = ""
    if p.ivs:
        etichetta_statistica += f"{len(p.ivs)}iv"
    if p.natura:
        if p.ivs:
            etichetta_statistica += " + "
        etichetta_statistica += "n"
    if not etichetta_statistica:
        etichetta_statistica = "base"

    if not nomi_colori_aggregati and not desc_caratteristiche_aggregata:
        p.nome_formattato = f"[VUOTO ({etichetta_statistica})]"
    elif not nomi_colori_aggregati:
         p.nome_formattato = f"[{desc_caratteristiche_aggregata} ({etichetta_statistica})]"
    else:
        p.nome_formattato = f"{nomi_colori_aggregati} [{desc_caratteristiche_aggregata} ({etichetta_statistica})]"
    return p

def genera_percorso_a_fase1(
    outfile_text,
    percorso_a_json: PercorsoJsonF1,
    legenda_corrente_stat_to_colore_ruolo: Dict[str, str],
    iv_target_specifiche_per_path_a: List[str],
    num_iv_output_percorso_a: int
) -> PokemonJsonF1:
    percorso_a_json.valido = True
    percorso_a_json.tipo_percorso = "A"
    percorso_a_json.livelli = []

    # Ruoli colore standard per il percorso A (massimo 5 IV)
    color_roles_path_a = ["Blu", "Rosso", "Giallo", "Grigio", "Arancione"]
    
    # Mappa i ruoli colore alle IV specifiche di questa permutazione
    iv_map = {role_color: iv_target_specifiche_per_path_a[i] for i, role_color in enumerate(color_roles_path_a) if i < len(iv_target_specifiche_per_path_a)}

    outfile_text.write("--- Percorso A: \"Albero solo statistiche\" ---\n")
    if 0 < num_iv_output_percorso_a < 5:
        outfile_text.write(f"(Troncato per produrre {num_iv_output_percorso_a} IVs)\n")

    ref_str_list = [f"{color}={iv_map[color]}" for i, color in enumerate(color_roles_path_a) if i < num_iv_output_percorso_a]
    outfile_text.write(f"(Riferimento IV ruoli usati: {', '.join(ref_str_list)})\n\n")

    # Funzione per ottenere le IV reali basate sui ruoli colore
    def safe_iv_list(*iv_role_names: str) -> List[str]:
        return [iv_map[name] for name in iv_role_names if name in iv_map]

    # Livello 0: Pokémon base con 1 IV
    l0_pkmn = {
        role_color: crea_pokemon_json_f1([iv_stat], "", legenda_corrente_stat_to_colore_ruolo)
        for role_color, iv_stat in iv_map.items()
    }

    # Livello 1: Creazione dei Pokémon 2 IV
    l1_pkmn: Dict[Tuple[str, ...], PokemonJsonF1] = {} # CORREZIONE QUI
    if num_iv_output_percorso_a >= 2:
        liv1_json = LivelloJsonF1(livello_id=1)
        outfile_text.write("**Livello 1 (Percorso A): Accoppiamenti di Base**\n")
        # Struttura fissa per 5IV -> 4IV
        pairings_l1 = [
            ("Blu", "Rosso"), ("Blu", "Giallo"), ("Blu", "Grigio"), ("Blu", "Arancione"),
            ("Rosso", "Giallo"), ("Rosso", "Grigio"),
            ("Giallo", "Grigio"), ("Giallo", "Arancione")
        ]
        
        count = 0
        for r1, r2 in pairings_l1:
            if color_roles_path_a.index(r1) >= num_iv_output_percorso_a or color_roles_path_a.index(r2) >= num_iv_output_percorso_a:
                continue
            g1, g2 = l0_pkmn[r1], l0_pkmn[r2]
            figlio_ivs = safe_iv_list(r1, r2)
            figlio = crea_pokemon_json_f1(figlio_ivs, "", legenda_corrente_stat_to_colore_ruolo)
            l1_pkmn[tuple(sorted((r1, r2)))] = figlio
            liv1_json.accoppiamenti.append(AccoppiamentoJsonF1(g1, g2, figlio))
            count += 1
            outfile_text.write(f"{count}. {g1.nome_formattato} + {g2.nome_formattato} -> genera {figlio.nome_formattato}\n")
        
        if liv1_json.accoppiamenti:
            percorso_a_json.livelli.append(liv1_json)
        outfile_text.write("\n")

    # Livello 2: Creazione dei Pokémon 3 IV
    l2_pkmn: Dict[Tuple[str, ...], PokemonJsonF1] = {} # CORREZIONE QUI
    if num_iv_output_percorso_a >= 3:
        liv2_json = LivelloJsonF1(livello_id=2)
        outfile_text.write("**Livello 2 (Percorso A): Prime Combinazioni**\n")
        pairings_l2 = [
            (("Blu", "Rosso"), ("Blu", "Giallo")),          # -> BluRossoGiallo
            (("Blu", "Rosso"), ("Blu", "Grigio")),          # -> BluRossoGrigio
            (("Blu", "Giallo"), ("Blu", "Arancione")),      # -> BluGialloArancione
            (("Giallo", "Grigio"), ("Giallo", "Arancione")) # -> GialloGrigioArancione
        ]
        
        count = 0
        for (p1_r1, p1_r2), (p2_r1, p2_r2) in pairings_l2:
            roles_needed = set([p1_r1, p1_r2, p2_r1, p2_r2])
            if any(color_roles_path_a.index(r) >= num_iv_output_percorso_a for r in roles_needed):
                continue
            
            g1 = l1_pkmn[tuple(sorted((p1_r1, p1_r2)))]
            g2 = l1_pkmn[tuple(sorted((p2_r1, p2_r2)))]
            figlio_roles = tuple(sorted(list(roles_needed)))
            figlio_ivs = safe_iv_list(*figlio_roles)

            figlio = crea_pokemon_json_f1(figlio_ivs, "", legenda_corrente_stat_to_colore_ruolo)
            l2_pkmn[figlio_roles] = figlio
            liv2_json.accoppiamenti.append(AccoppiamentoJsonF1(g1, g2, figlio))
            count += 1
            outfile_text.write(f"{count}. {g1.nome_formattato} + {g2.nome_formattato} -> genera {figlio.nome_formattato}\n")
            
        if liv2_json.accoppiamenti:
            percorso_a_json.livelli.append(liv2_json)
        outfile_text.write("\n")

    # Livello 3: Creazione dei Pokémon 4 IV
    l3_pkmn: Dict[Tuple[str, ...], PokemonJsonF1] = {}
    if num_iv_output_percorso_a >= 4:
        liv3_json = LivelloJsonF1(livello_id=3)
        outfile_text.write("**Livello 3 (Percorso A): Combinazioni Avanzate**\n")
        pairings_l3 = [
            (("Blu", "Rosso", "Giallo"), ("Blu", "Rosso", "Grigio")), # -> BluRossoGialloGrigio
            (("Blu", "Giallo", "Arancione"), ("Giallo", "Grigio", "Arancione")) # -> BluGialloGrigioArancione
        ]
        
        count = 0
        for p1_roles, p2_roles in pairings_l3:
            roles_needed = set(p1_roles) | set(p2_roles)
            if any(color_roles_path_a.index(r) >= num_iv_output_percorso_a for r in roles_needed):
                continue

            g1 = l2_pkmn[p1_roles]
            g2 = l2_pkmn[p2_roles]
            figlio_roles = tuple(sorted(list(roles_needed)))
            figlio_ivs = safe_iv_list(*figlio_roles)
            
            figlio = crea_pokemon_json_f1(figlio_ivs, "", legenda_corrente_stat_to_colore_ruolo)
            l3_pkmn[figlio_roles] = figlio
            liv3_json.accoppiamenti.append(AccoppiamentoJsonF1(g1, g2, figlio))
            count += 1
            outfile_text.write(f"{count}. {g1.nome_formattato} + {g2.nome_formattato} -> genera {figlio.nome_formattato}\n")

        if liv3_json.accoppiamenti:
            percorso_a_json.livelli.append(liv3_json)
        outfile_text.write("\n")

    # Livello 4: Creazione del Pokémon 5 IV (Genitore A)
    if num_iv_output_percorso_a >= 5:
        liv4_json = LivelloJsonF1(livello_id=4)
        outfile_text.write("**Livello 4 (Percorso A): Risultato del Percorso A**\n")
        
        p1_roles = ("Blu", "Grigio", "Rosso", "Giallo")
        p2_roles = ("Arancione", "Blu", "Grigio", "Giallo")
        g1 = l3_pkmn[tuple(sorted(p1_roles))]
        g2 = l3_pkmn[tuple(sorted(p2_roles))]

        figlio_roles = tuple(sorted(list(set(p1_roles) | set(p2_roles))))
        figlio_ivs = safe_iv_list(*figlio_roles)

        figlio = crea_pokemon_json_f1(figlio_ivs, "", legenda_corrente_stat_to_colore_ruolo)
        percorso_a_json.risultato_percorso = figlio
        liv4_json.accoppiamenti.append(AccoppiamentoJsonF1(g1, g2, figlio))
        outfile_text.write(f"1. {g1.nome_formattato} + {g2.nome_formattato} -> Genitore A: {figlio.nome_formattato} (TARGET)\n\n")

        if liv4_json.accoppiamenti:
            percorso_a_json.livelli.append(liv4_json)
    
    # Imposta il risultato finale del percorso
    final_results = [l3_pkmn, l2_pkmn, l1_pkmn, l0_pkmn]
    if not percorso_a_json.risultato_percorso.nome_formattato:
        if num_iv_output_percorso_a == 4: percorso_a_json.risultato_percorso = list(l3_pkmn.values())[0]
        elif num_iv_output_percorso_a == 3: percorso_a_json.risultato_percorso = list(l2_pkmn.values())[0]
        elif num_iv_output_percorso_a == 2: percorso_a_json.risultato_percorso = list(l1_pkmn.values())[0]
        elif num_iv_output_percorso_a == 1: percorso_a_json.risultato_percorso = list(l0_pkmn.values())[0]
        else: percorso_a_json.risultato_percorso = PokemonJsonF1()

    return percorso_a_json.risultato_percorso


def genera_percorso_b_fase1(
    outfile_text,
    percorso_b_json: PercorsoJsonF1,
    legenda_corrente_stat_to_colore_ruolo: Dict[str, str],
    natura_obiettivo_specifica: str,
    iv_target_natura: List[str], 
    num_iv_richieste_con_natura: int 
) -> PokemonJsonF1:
    percorso_b_json.valido = True
    percorso_b_json.tipo_percorso = "B"
    percorso_b_json.livelli = []

    # Ruoli colore standard
    color_roles_all = ["Blu", "Rosso", "Giallo", "Grigio", "Arancione"]
    
    # Per il percorso B, usiamo solo le prime N IV della permutazione
    iv_map_b = {color_roles_all[i]: iv_target_natura[i] for i in range(len(iv_target_natura))}
    
    # I ruoli colore usati in questo percorso sono solo quelli associati alle IV necessarie
    color_roles_path_b = [role for role in color_roles_all if role in iv_map_b]

    title_str = f"Albero {num_iv_richieste_con_natura} statistiche e {natura_obiettivo_specifica}"
    outfile_text.write(f"--- Percorso B: \"{title_str}\" ---\n")
    ref_str_list = [f"{color}={iv_map_b[color]}" for color in color_roles_path_b]
    outfile_text.write(f"(Riferimento IV ruoli usati: {', '.join(ref_str_list)})\n\n")
    
    def safe_iv_list_b(*iv_role_names: str) -> List[str]:
        return [iv_map_b[name] for name in iv_role_names if name in iv_map_b]

    # Livello 0: Pokémon base con 1 IV e Pokémon con Natura
    l0_pkmn_b = {
        role_color: crea_pokemon_json_f1([iv_stat], "", legenda_corrente_stat_to_colore_ruolo)
        for role_color, iv_stat in iv_map_b.items()
    }
    l0_pkmn_b["Verde"] = crea_pokemon_json_f1([], natura_obiettivo_specifica, legenda_corrente_stat_to_colore_ruolo)

    # Livello 1: Accoppiamenti
    l1_pkmn_b: Dict[Tuple, PokemonJsonF1] = {}
    if num_iv_richieste_con_natura >= 1:
        liv1_json = LivelloJsonF1(livello_id=1)
        outfile_text.write("**Livello 1 (Percorso B): Accoppiamenti di Base**\n")
        
        # Struttura fissa simmetrica al percorso A
        pairings_l1 = [
            ("Verde", "Blu"), # Introduce la natura
            ("Blu", "Rosso"), ("Blu", "Giallo"), ("Blu", "Grigio"),
            ("Rosso", "Giallo"), ("Rosso", "Grigio"),
            ("Giallo", "Grigio"),
        ]
        
        count = 0
        for r1, r2 in pairings_l1:
            # Salta gli accoppiamenti se i ruoli non sono necessari per questo piano
            if (r1 != "Verde" and r1 not in color_roles_path_b) or \
               (r2 != "Verde" and r2 not in color_roles_path_b):
                continue

            g1, g2 = l0_pkmn_b[r1], l0_pkmn_b[r2]
            
            figlio_ivs = safe_iv_list_b(*[r for r in [r1, r2] if r != "Verde"])
            figlio_nat = natura_obiettivo_specifica if "Verde" in [r1, r2] else ""
            
            figlio = crea_pokemon_json_f1(figlio_ivs, figlio_nat, legenda_corrente_stat_to_colore_ruolo)
            l1_pkmn_b[tuple(sorted((r1, r2)))] = figlio
            liv1_json.accoppiamenti.append(AccoppiamentoJsonF1(g1, g2, figlio))
            count += 1
            outfile_text.write(f"{count}. {g1.nome_formattato} + {g2.nome_formattato} -> genera {figlio.nome_formattato}\n")
        
        if liv1_json.accoppiamenti:
            percorso_b_json.livelli.append(liv1_json)
        outfile_text.write("\n")

    # Livello 2
    l2_pkmn_b: Dict[Tuple, PokemonJsonF1] = {}
    if num_iv_richieste_con_natura >= 2:
        liv2_json = LivelloJsonF1(livello_id=2)
        outfile_text.write("**Livello 2 (Percorso B): Prime Combinazioni**\n")
        pairings_l2 = [
            (("Verde", "Blu"), ("Blu", "Rosso")),       # -> VerdeBluRosso
            (("Blu", "Rosso"), ("Blu", "Giallo")),      # -> BluRossoGiallo
            (("Blu", "Rosso"), ("Blu", "Grigio")),      # -> BluRossoGrigio
            (("Rosso", "Giallo"), ("Rosso", "Grigio")), # -> RossoGialloGrigio
        ]

        count = 0
        for (p1_r1, p1_r2), (p2_r1, p2_r2) in pairings_l2:
            roles_needed = set([p1_r1, p1_r2, p2_r1, p2_r2])
            if any((r != "Verde" and r not in color_roles_path_b) for r in roles_needed):
                continue
            
            g1 = l1_pkmn_b[tuple(sorted((p1_r1, p1_r2)))]
            g2 = l1_pkmn_b[tuple(sorted((p2_r1, p2_r2)))]
            
            figlio_roles_iv = tuple(sorted([r for r in roles_needed if r != "Verde"]))
            figlio_ivs = safe_iv_list_b(*figlio_roles_iv)
            figlio_nat = natura_obiettivo_specifica if "Verde" in roles_needed else ""

            figlio = crea_pokemon_json_f1(figlio_ivs, figlio_nat, legenda_corrente_stat_to_colore_ruolo)
            figlio_roles_key = ("Verde",) + figlio_roles_iv if figlio_nat else figlio_roles_iv
            l2_pkmn_b[figlio_roles_key] = figlio

            liv2_json.accoppiamenti.append(AccoppiamentoJsonF1(g1, g2, figlio))
            count += 1
            outfile_text.write(f"{count}. {g1.nome_formattato} + {g2.nome_formattato} -> genera {figlio.nome_formattato}\n")
            
        if liv2_json.accoppiamenti:
            percorso_b_json.livelli.append(liv2_json)
        outfile_text.write("\n")

    # Livello 3
    l3_pkmn_b: Dict[Tuple, PokemonJsonF1] = {}
    if num_iv_richieste_con_natura >= 3:
        liv3_json = LivelloJsonF1(livello_id=3)
        outfile_text.write("**Livello 3 (Percorso B): Combinazioni Avanzate**\n")
        pairings_l3 = [
            (("Verde", "Blu", "Rosso"), ("Blu", "Rosso", "Giallo")), # -> VerdeBluRossoGiallo
            (("Blu", "Rosso", "Giallo"), ("Blu", "Rosso", "Grigio"))  # -> BluRossoGialloGrigio
        ]
        
        count = 0
        for p1_roles, p2_roles in pairings_l3:
            roles_needed = set(p1_roles) | set(p2_roles)
            if any((r != "Verde" and r not in color_roles_path_b) for r in roles_needed):
                continue

            g1 = l2_pkmn_b[p1_roles]
            g2 = l2_pkmn_b[p2_roles]
            
            figlio_roles_iv = tuple(sorted([r for r in roles_needed if r != "Verde"]))
            figlio_ivs = safe_iv_list_b(*figlio_roles_iv)
            figlio_nat = natura_obiettivo_specifica if "Verde" in roles_needed else ""

            figlio = crea_pokemon_json_f1(figlio_ivs, figlio_nat, legenda_corrente_stat_to_colore_ruolo)
            figlio_roles_key = ("Verde",) + figlio_roles_iv if figlio_nat else figlio_roles_iv
            l3_pkmn_b[figlio_roles_key] = figlio

            liv3_json.accoppiamenti.append(AccoppiamentoJsonF1(g1, g2, figlio))
            count += 1
            outfile_text.write(f"{count}. {g1.nome_formattato} + {g2.nome_formattato} -> genera {figlio.nome_formattato}\n")

        if liv3_json.accoppiamenti:
            percorso_b_json.livelli.append(liv3_json)
        outfile_text.write("\n")

    # Livello 4 (Genitore B)
    if num_iv_richieste_con_natura >= 4:
        liv4_json = LivelloJsonF1(livello_id=4)
        outfile_text.write("**Livello 4 (Percorso B): Risultato del Percorso B**\n")
        
        p1_roles = ("Verde", "Blu", "Rosso", "Giallo")
        p2_roles = ("Blu", "Rosso", "Giallo", "Grigio")
        g1 = l3_pkmn_b[p1_roles]
        g2 = l3_pkmn_b[p2_roles]

        roles_needed = set(p1_roles) | set(p2_roles)
        figlio_roles_iv = tuple(sorted([r for r in roles_needed if r != "Verde"]))
        figlio_ivs = safe_iv_list_b(*figlio_roles_iv)
        figlio_nat = natura_obiettivo_specifica

        figlio = crea_pokemon_json_f1(figlio_ivs, figlio_nat, legenda_corrente_stat_to_colore_ruolo)
        percorso_b_json.risultato_percorso = figlio
        liv4_json.accoppiamenti.append(AccoppiamentoJsonF1(g1, g2, figlio))
        outfile_text.write(f"1. {g1.nome_formattato} + {g2.nome_formattato} -> Genitore B: {figlio.nome_formattato} (TARGET)\n\n")

        if liv4_json.accoppiamenti:
            percorso_b_json.livelli.append(liv4_json)
    
    # Imposta il risultato finale del percorso B
    if not percorso_b_json.risultato_percorso.nome_formattato:
        if num_iv_richieste_con_natura == 3: percorso_b_json.risultato_percorso = list(l3_pkmn_b.values())[0]
        elif num_iv_richieste_con_natura == 2: percorso_b_json.risultato_percorso = list(l2_pkmn_b.values())[0]
        elif num_iv_richieste_con_natura == 1: percorso_b_json.risultato_percorso = list(l1_pkmn_b.values())[0]
        else: percorso_b_json.risultato_percorso = PokemonJsonF1()


    return percorso_b_json.risultato_percorso


def run_fase1(
    modalita_op_base: str,
    con_natura_obiettivo: bool,
    natura_obiettivo_spec: str,
    stats_target_config: Optional[List[str]] = None
    ):
    tutte_le_stat_iv_possibili = ["PS", "ATT", "DEF", "SP.DEF", "SP.ATT", "Velocità"]
    colori_disponibili_per_iv_base = ["Blu", "Rosso", "Giallo", "Grigio", "Arancione"]
    nome_file_out_json = "piani_dati.json"
    modalita_operativa = modalita_op_base + ("+N" if con_natura_obiettivo else "_noN")

    if not con_natura_obiettivo:
        natura_obiettivo_spec = ""

    stats_per_modalita: List[str] = stats_target_config if stats_target_config is not None else []
    num_iv_target_globale = int(modalita_op_base.replace("IV", ""))

    num_iv_output_percorso_a = 0
    num_iv_output_percorso_b = 0

    # Determina IV per ogni percorso in base alla modalità 5IV+N
    if modalita_operativa == "5IV+N":
        num_iv_output_percorso_a = 5
        num_iv_output_percorso_b = 4
    elif modalita_operativa == "4IV+N":
        num_iv_output_percorso_a = 4
        num_iv_output_percorso_b = 3
    elif modalita_operativa == "3IV+N":
        num_iv_output_percorso_a = 3
        num_iv_output_percorso_b = 2
    elif modalita_operativa == "2IV+N":
        num_iv_output_percorso_a = 2
        num_iv_output_percorso_b = 1
    elif modalita_operativa == "0IV+N":
        num_iv_output_percorso_a = 0
        num_iv_output_percorso_b = 0
    elif "_noN" in modalita_operativa:
        num_iv_output_percorso_a = num_iv_target_globale
        num_iv_output_percorso_b = 0 # Percorso B non usato se non c'è natura
    else:
        print(f"Modalita' operativa non riconosciuta: {modalita_operativa}", file=sys.stderr)
        return

    # Validazione input
    if len(stats_per_modalita) != num_iv_target_globale:
        print(f"Errore: Il numero di IVs ({len(stats_per_modalita)}) non corrisponde alla modalità ({num_iv_target_globale}IV).", file=sys.stderr)
        return
    if len(set(stats_per_modalita)) != len(stats_per_modalita):
        print("Errore: Le statistiche IV target devono essere uniche.", file=sys.stderr)
        return

    nat_suffix = natura_obiettivo_spec if con_natura_obiettivo and natura_obiettivo_spec else "noNatura"
    nome_file_out_text = f"piani_{modalita_op_base}_{nat_suffix}_StatPerm.txt"
    
    stats_per_modalita_ordinate_per_permutazioni = sorted(list(set(stats_per_modalita)))
    permutazioni_da_usare = list(itertools.permutations(stats_per_modalita_ordinate_per_permutazioni))
    
    print(f"Generazione piani per {modalita_op_base} {natura_obiettivo_spec}...")
    
    tutti_piani_json: List[PianoJsonF1] = []
    piano_count = 0

    with open(nome_file_out_text, "w", encoding="utf-8") as outfile_text_stream:
        # Codice principale per generare i piani
        for current_permutation_tuple in permutazioni_da_usare:
            current_permutation_list = list(current_permutation_tuple)
            piano_count += 1
            piano_corrente_json = PianoJsonF1(id_piano_fase1=piano_count)
            
            legenda_corrente_stat_to_colore_ruolo: Dict[str, str] = {
                stat: colori_disponibili_per_iv_base[i] 
                for i, stat in enumerate(current_permutation_list) 
                if i < len(colori_disponibili_per_iv_base)
            }
            piano_corrente_json.legenda_usata = legenda_corrente_stat_to_colore_ruolo

            outfile_text_stream.write("="*58 + f"\n                     PIANO #{piano_count}\n" + "="*58 + "\n\n")
            
            # Scrivi legenda
            outfile_text_stream.write("### Legenda del Piano Corrente (Statistiche Permutate in Ruoli Colorati Fissi)\n")
            for stat, colore in legenda_corrente_stat_to_colore_ruolo.items():
                outfile_text_stream.write(f"* **{colore}:** {stat}\n")
            if con_natura_obiettivo:
                outfile_text_stream.write(f"* **Verde:** {natura_obiettivo_spec} (rimane invariato)\n")
            outfile_text_stream.write("\n")

            # Genera Percorso A
            if num_iv_output_percorso_a > 0:
                genera_percorso_a_fase1(outfile_text_stream, piano_corrente_json.percorso_A,
                                        legenda_corrente_stat_to_colore_ruolo,
                                        current_permutation_list,
                                        num_iv_output_percorso_a)
            else:
                piano_corrente_json.percorso_A.valido = False

            # Genera Percorso B
            if con_natura_obiettivo:
                ivs_per_percorso_b = current_permutation_list[:num_iv_output_percorso_b]
                genera_percorso_b_fase1(outfile_text_stream, piano_corrente_json.percorso_B,
                                        legenda_corrente_stat_to_colore_ruolo,
                                        natura_obiettivo_spec,
                                        ivs_per_percorso_b,
                                        num_iv_output_percorso_b)
            else:
                piano_corrente_json.percorso_B.valido = False

            # Determina e scrivi il target finale
            target_ivs_finali_piano = current_permutation_list
            natura_target_finale_json = natura_obiettivo_spec if con_natura_obiettivo else ""
            piano_corrente_json.pokemon_target_finale_piano = crea_pokemon_json_f1(
                target_ivs_finali_piano, natura_target_finale_json, legenda_corrente_stat_to_colore_ruolo
            )

            outfile_text_stream.write(f"--- Fine: L'Accoppiamento Finale del Piano ---\n")
            if piano_corrente_json.percorso_A.valido and piano_corrente_json.percorso_B.valido:
                outfile_text_stream.write(f"* Genitore A (IVs): {piano_corrente_json.percorso_A.risultato_percorso.nome_formattato}\n")
                outfile_text_stream.write("    +\n")
                outfile_text_stream.write(f"* Genitore B (Natura): {piano_corrente_json.percorso_B.risultato_percorso.nome_formattato}\n")
            elif piano_corrente_json.percorso_A.valido:
                 piano_corrente_json.pokemon_target_finale_piano = piano_corrente_json.percorso_A.risultato_percorso
            
            outfile_text_stream.write(f"    -> Pokémon Target: {piano_corrente_json.pokemon_target_finale_piano.nome_formattato}\n\n")
            tutti_piani_json.append(piano_corrente_json)

    # Scrivi JSON
    json_output_data = {
        "versione_formato": "1.1",
        "modalita_operativa_base": modalita_operativa,
        "stats_target_set": stats_per_modalita,
        "natura_target_specifica": natura_obiettivo_spec,
        "piani": [p.to_dict() for p in tutti_piani_json]
    }
    with open(nome_file_out_json, "w", encoding="utf-8") as outfile_json_stream:
        json.dump(json_output_data, outfile_json_stream, indent=2)

    print(f"Output JSON scritto su '{nome_file_out_json}'.")
    print(f"Generazione Fase 1 completata. {piano_count} piani scritti su '{nome_file_out_text}'.\n")

# --- Il resto del file (da PokemonPossedutoF2 in poi) rimane invariato ---
# ... (copia e incolla il resto del file breeding_planner.py originale da qui in poi)
# --- Strutture Dati Fase 2 ---
@dataclass
class PokemonDefF2:
    nome_formattato_dal_piano: str = ""
    ivs: List[str] = field(default_factory=list)
    natura: str = ""
    soddisfatto_da_posseduto: bool = False
    soddisfatto_da_id_utente: Optional[str] = None
    sesso_determinato: Optional[str] = None 

    def __post_init__(self):
        self.ivs.sort()

    def print_pokemon(self, indent="  ", stream=sys.stdout, show_match_details=True):
        iv_str = "/".join(self.ivs) if self.ivs else "Nessuna"
        nat_str = f", Natura: {self.natura}" if self.natura and self.natura.lower() != "null" and self.natura != '""' else ""
        match_info = ""
        if show_match_details and self.soddisfatto_da_posseduto and self.soddisfatto_da_id_utente:
            match_info = f" {GREEN_TERMINAL}[MATCHED con {self.soddisfatto_da_id_utente}]{RESET_TERMINAL}"
        elif show_match_details and self.soddisfatto_da_posseduto :
             match_info = f" {GREEN_TERMINAL}[MATCHED]{RESET_TERMINAL}"
        print(f"{indent}\"{self.nome_formattato_dal_piano}\" (IVs: {iv_str}{nat_str}){match_info}", file=stream)

    def log_str(self) -> str:
        iv_str = "/".join(self.ivs) if self.ivs else "Nessuna"
        nat_str = f", Natura: {self.natura}" if self.natura and self.natura.lower() != "null" and self.natura != '""' else ""
        match_str_log = f" [MATCHED con {self.soddisfatto_da_id_utente}]" if self.soddisfatto_da_posseduto and self.soddisfatto_da_id_utente else (" [MATCHED]" if self.soddisfatto_da_posseduto else "")
        return f"\"{self.nome_formattato_dal_piano}\" (IVs: {iv_str}{nat_str}){match_str_log}"

    def to_dict(self) -> Dict[str, Any]: 
        return {
            "nome_formattato_dal_piano": self.nome_formattato_dal_piano,
            "ivs": self.ivs,
            "natura": self.natura,
            "soddisfatto_da_posseduto": self.soddisfatto_da_posseduto,
            "soddisfatto_da_id_utente": self.soddisfatto_da_id_utente,
            "sesso_determinato": self.sesso_determinato 
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'PokemonDefF2':
        return cls(
            nome_formattato_dal_piano=data.get("nome_formattato_dal_piano", ""),
            ivs=data.get("ivs", []),
            natura=data.get("natura", ""),
            soddisfatto_da_posseduto=data.get("soddisfatto_da_posseduto", False),
            soddisfatto_da_id_utente=data.get("soddisfatto_da_id_utente"),
            sesso_determinato=data.get("sesso_determinato") 
        )

@dataclass
class AccoppiamentoDefF2:
    genitore1_richiesto: PokemonDefF2 = field(default_factory=PokemonDefF2)
    genitore2_richiesto: PokemonDefF2 = field(default_factory=PokemonDefF2)
    figlio_generato: PokemonDefF2 = field(default_factory=PokemonDefF2)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "genitore1_richiesto": self.genitore1_richiesto.to_dict(),
            "genitore2_richiesto": self.genitore2_richiesto.to_dict(),
            "figlio_generato": self.figlio_generato.to_dict()
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'AccoppiamentoDefF2':
        return cls(
            genitore1_richiesto=PokemonDefF2.from_dict(data.get("genitore1_richiesto", {})),
            genitore2_richiesto=PokemonDefF2.from_dict(data.get("genitore2_richiesto", {})),
            figlio_generato=PokemonDefF2.from_dict(data.get("figlio_generato", {}))
        )

@dataclass
class LivelloDefF2:
    livello_id: int = 0
    accoppiamenti: List[AccoppiamentoDefF2] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "livello_id": self.livello_id,
            "accoppiamenti": [acc.to_dict() for acc in self.accoppiamenti]
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'LivelloDefF2':
        return cls(
            livello_id=data.get("livello_id", 0),
            accoppiamenti=[AccoppiamentoDefF2.from_dict(acc_data) for acc_data in data.get("accoppiamenti", [])]
        )

@dataclass
class PercorsoDefF2:
    tipo_percorso: str = ""
    risultato_percorso: PokemonDefF2 = field(default_factory=PokemonDefF2)
    livelli: List[LivelloDefF2] = field(default_factory=list)
    valido: bool = False

    def to_dict(self) -> Optional[Dict[str, Any]]:
        if not self.valido: return None
        return {
            "tipo_percorso": self.tipo_percorso,
            "risultato_percorso": self.risultato_percorso.to_dict(),
            "livelli": [liv.to_dict() for liv in self.livelli],
            "valido": self.valido
        }

    @classmethod
    def from_dict(cls, data: Optional[Dict[str, Any]]) -> 'PercorsoDefF2':
        if data is None: return cls(valido=False)
        return cls(
            tipo_percorso=data.get("tipo_percorso", ""),
            risultato_percorso=PokemonDefF2.from_dict(data.get("risultato_percorso", {})),
            livelli=[LivelloDefF2.from_dict(liv_data) for liv_data in data.get("livelli", [])],
            valido=data.get("valido", False)
        )

@dataclass
class PianoCompletoF2:
    id_piano_fase1: int = 0
    legenda_usata: Dict[str, str] = field(default_factory=dict)
    percorso_A: PercorsoDefF2 = field(default_factory=PercorsoDefF2)
    percorso_B: PercorsoDefF2 = field(default_factory=PercorsoDefF2)
    pokemon_target_finale_piano: PokemonDefF2 = field(default_factory=PokemonDefF2)
    natura_target_specifica_del_piano_globale: str = ""
    punteggio_ottenuto: float = 0.0
    pokemon_matchati_count: int = 0
    id_pokemon_posseduti_usati_unici: Set[str] = field(default_factory=set)
    mappa_richiesto_a_posseduto: Dict[str, str] = field(default_factory=dict)
    pokemon_base_necessari_calcolati: Dict[str, int] = field(default_factory=dict)

    def to_dict_per_fase3(self) -> Dict[str, Any]:
        return {
            "id_piano_fase1": self.id_piano_fase1,
            "legenda_usata": self.legenda_usata,
            "punteggio_ottenuto": self.punteggio_ottenuto,
            "pokemon_matchati_count": self.pokemon_matchati_count,
            "id_pokemon_posseduti_usati_unici": sorted(list(self.id_pokemon_posseduti_usati_unici)),
            "pokemon_target_finale_piano": self.pokemon_target_finale_piano.to_dict(),
            "natura_target_specifica_del_piano_globale": self.natura_target_specifica_del_piano_globale,
            "percorso_A_dettagli": self.percorso_A.to_dict() if self.percorso_A.valido else None,
            "percorso_B_dettagli": self.percorso_B.to_dict() if self.percorso_B.valido else None,
            "pokemon_base_necessari_calcolati": self.pokemon_base_necessari_calcolati,
            "mappa_richiesto_a_posseduto": self.mappa_richiesto_a_posseduto 
        }

@dataclass
class PokemonPossedutoF2:
    id_utente: str = ""
    ivs: List[str] = field(default_factory=list)
    natura: str = ""
    specie: Optional[str] = None
    sesso: Optional[str] = None
    egg_groups: List[str] = field(default_factory=list)

    def __post_init__(self):
        self.ivs.sort()

# --- Funzioni Deserializzazione Fase 2 ---
def deserialize_pokemon_def_f2(pkmn_data: Optional[Dict]) -> PokemonDefF2:
    if not pkmn_data: return PokemonDefF2()
    nome = pkmn_data.get("nome_formattato_dal_piano", pkmn_data.get("nome_formattato", ""))
    ivs = sorted(list(set(pkmn_data.get("ivs", []))))
    natura = pkmn_data.get("natura", "")
    if natura is None or natura.lower() == "null": natura = ""
    return PokemonDefF2(
        nome_formattato_dal_piano=nome,
        ivs=ivs,
        natura=natura,
        soddisfatto_da_posseduto=pkmn_data.get("soddisfatto_da_posseduto", False), 
        soddisfatto_da_id_utente=pkmn_data.get("soddisfatto_da_id_utente")       
    )

def deserialize_accoppiamento_def_f2(acc_data: Dict) -> AccoppiamentoDefF2:
    return AccoppiamentoDefF2(
        genitore1_richiesto=deserialize_pokemon_def_f2(acc_data.get("genitore1_richiesto")),
        genitore2_richiesto=deserialize_pokemon_def_f2(acc_data.get("genitore2_richiesto")),
        figlio_generato=deserialize_pokemon_def_f2(acc_data.get("figlio_generato"))
    )

def deserialize_livello_def_f2(liv_data: Dict) -> LivelloDefF2:
    return LivelloDefF2(
        livello_id=liv_data.get("livello_id", 0),
        accoppiamenti=[deserialize_accoppiamento_def_f2(acc) for acc in liv_data.get("accoppiamenti", [])]
    )

def deserialize_percorso_def_f2(perc_data: Optional[Dict]) -> PercorsoDefF2:
    if not perc_data:
        return PercorsoDefF2(valido=False)
    return PercorsoDefF2(
        tipo_percorso=perc_data.get("tipo_percorso", ""),
        risultato_percorso=deserialize_pokemon_def_f2(perc_data.get("risultato_percorso")),
        livelli=[deserialize_livello_def_f2(liv) for liv in perc_data.get("livelli", [])],
        valido=True 
    )

# --- Funzioni Logica Fase 2 ---
def ivs_match_fase2(possedute_param: List[str], richieste_param: List[str]) -> bool:
    if not richieste_param: return True 
    return all(req_iv in possedute_param for req_iv in richieste_param) and len(possedute_param) >= len(richieste_param)

def natura_match_fase2(posseduta_nat: str, richiesta_nat_dal_pokemon_del_piano: str, natura_target_specifica_del_piano_globale: str) -> bool:
    req_trimmed = richiesta_nat_dal_pokemon_del_piano.strip() if richiesta_nat_dal_pokemon_del_piano else ""
    poss_trimmed = posseduta_nat.strip() if posseduta_nat else ""
    
    if not req_trimmed or req_trimmed.lower() == "null" or req_trimmed == '""': 
        return True
        
    if req_trimmed == "NATURA": 
        if not natura_target_specifica_del_piano_globale: 
            return bool(poss_trimmed) 
        return poss_trimmed == natura_target_specifica_del_piano_globale

    return poss_trimmed == req_trimmed

def calcola_punteggio_pokemon_fase2(pokemon_richiesto: PokemonDefF2) -> float:
    punteggio = 0.0
    punteggio += len(pokemon_richiesto.ivs) * 2.0  

    if pokemon_richiesto.natura and pokemon_richiesto.natura.lower() != "null" and pokemon_richiesto.natura != '""':
        punteggio += 3.0 

    if len(pokemon_richiesto.ivs) > 0 and (pokemon_richiesto.natura and pokemon_richiesto.natura.lower() != "null" and pokemon_richiesto.natura != '""'):
        punteggio += float(len(pokemon_richiesto.ivs)) 

    if len(pokemon_richiesto.ivs) >= 4: punteggio += 2.0
    if len(pokemon_richiesto.ivs) == 5: punteggio += 2.0 

    return punteggio

def reset_soddisfazione_piano(piano: PianoCompletoF2):
    piano.mappa_richiesto_a_posseduto.clear()
    elementi_da_resettare: List[PokemonDefF2] = [] 
    
    if piano.percorso_A and piano.percorso_A.valido:
        if piano.percorso_A.risultato_percorso:
            elementi_da_resettare.append(piano.percorso_A.risultato_percorso)
        for livello in piano.percorso_A.livelli:
            for accoppiamento in livello.accoppiamenti:
                if accoppiamento.genitore1_richiesto: elementi_da_resettare.append(accoppiamento.genitore1_richiesto)
                if accoppiamento.genitore2_richiesto: elementi_da_resettare.append(accoppiamento.genitore2_richiesto)
                if accoppiamento.figlio_generato: elementi_da_resettare.append(accoppiamento.figlio_generato)
    
    if piano.percorso_B and piano.percorso_B.valido:
        if piano.percorso_B.risultato_percorso:
            elementi_da_resettare.append(piano.percorso_B.risultato_percorso)
        for livello in piano.percorso_B.livelli:
            for accoppiamento in livello.accoppiamenti:
                if accoppiamento.genitore1_richiesto: elementi_da_resettare.append(accoppiamento.genitore1_richiesto)
                if accoppiamento.genitore2_richiesto: elementi_da_resettare.append(accoppiamento.genitore2_richiesto)
                if accoppiamento.figlio_generato: elementi_da_resettare.append(accoppiamento.figlio_generato)

    if piano.pokemon_target_finale_piano:
        elementi_da_resettare.append(piano.pokemon_target_finale_piano)

    for pkmn_def in elementi_da_resettare:
        if pkmn_def: 
            pkmn_def.soddisfatto_da_posseduto = False
            pkmn_def.soddisfatto_da_id_utente = None

def calcola_pokemon_base_necessari_f2(
    piano_valutato: PianoCompletoF2
    ) -> Counter:
    necessari_base = Counter() 
    ricette_pokedex_piano: Dict[str, Tuple[Optional[PokemonDefF2], Optional[PokemonDefF2]]] = {}
    definizione_pkmn_nel_piano: Dict[str, PokemonDefF2] = {}

    def popola_definizioni_e_ricette(percorso: PercorsoDefF2):
        if not percorso or not percorso.valido: return
        for livello in percorso.livelli:
            for acc in livello.accoppiamenti:
                for gen_slot_key in ["genitore1_richiesto", "genitore2_richiesto", "figlio_generato"]:
                    current_pkmn_def = getattr(acc, gen_slot_key)
                    if current_pkmn_def and current_pkmn_def.nome_formattato_dal_piano:
                         definizione_pkmn_nel_piano[current_pkmn_def.nome_formattato_dal_piano] = current_pkmn_def
                if acc.figlio_generato and acc.figlio_generato.nome_formattato_dal_piano:
                    ricette_pokedex_piano[acc.figlio_generato.nome_formattato_dal_piano] = \
                        (acc.genitore1_richiesto, acc.genitore2_richiesto)
        if percorso.risultato_percorso and percorso.risultato_percorso.nome_formattato_dal_piano:
            definizione_pkmn_nel_piano[percorso.risultato_percorso.nome_formattato_dal_piano] = percorso.risultato_percorso

    popola_definizioni_e_ricette(piano_valutato.percorso_A)
    popola_definizioni_e_ricette(piano_valutato.percorso_B)
    if piano_valutato.pokemon_target_finale_piano and piano_valutato.pokemon_target_finale_piano.nome_formattato_dal_piano:
        definizione_pkmn_nel_piano[piano_valutato.pokemon_target_finale_piano.nome_formattato_dal_piano] = piano_valutato.pokemon_target_finale_piano

    cache_decomposizione: Dict[str, Counter] = {}

    def decomponi_in_base_ricorsivo(nome_pkmn_da_decomporre: Optional[str]) -> Counter:
        if not nome_pkmn_da_decomporre: return Counter() 
        if nome_pkmn_da_decomporre in cache_decomposizione: 
            return cache_decomposizione[nome_pkmn_da_decomporre].copy()

        pkmn_def = definizione_pkmn_nel_piano.get(nome_pkmn_da_decomporre)
        if not pkmn_def: 
            cache_decomposizione[nome_pkmn_da_decomporre] = Counter({f"Da Procurare (Definizione Mancante: {nome_pkmn_da_decomporre})": 1})
            return cache_decomposizione[nome_pkmn_da_decomporre].copy()

        if pkmn_def.soddisfatto_da_posseduto:
            cache_decomposizione[nome_pkmn_da_decomporre] = Counter() 
            return Counter()

        is_base = False
        base_key = "" 
        if not pkmn_def.ivs and pkmn_def.natura and pkmn_def.natura.lower() != "null" and pkmn_def.natura != '""':
            base_key = f"Solo Natura: {pkmn_def.natura}"
            is_base = True
        elif len(pkmn_def.ivs) == 1 and (not pkmn_def.natura or pkmn_def.natura.lower() == "null" or pkmn_def.natura == '""'):
            iv_stat = pkmn_def.ivs[0]
            colore_ruolo = next((col for stat, col in piano_valutato.legenda_usata.items() if stat == iv_stat), "Sconosciuto")
            base_key = f"Solo IV: {iv_stat} ({colore_ruolo})"
            is_base = True
        
        if is_base: 
            cache_decomposizione[nome_pkmn_da_decomporre] = Counter({base_key: 1})
            return cache_decomposizione[nome_pkmn_da_decomporre].copy()

        if nome_pkmn_da_decomporre in ricette_pokedex_piano:
            genitore1_def, genitore2_def = ricette_pokedex_piano[nome_pkmn_da_decomporre]
            req_g1 = decomponi_in_base_ricorsivo(genitore1_def.nome_formattato_dal_piano if genitore1_def else None)
            req_g2 = decomponi_in_base_ricorsivo(genitore2_def.nome_formattato_dal_piano if genitore2_def else None)
            risultato_decomposizione = req_g1 + req_g2
            cache_decomposizione[nome_pkmn_da_decomporre] = risultato_decomposizione
            return risultato_decomposizione.copy()

        cache_decomposizione[nome_pkmn_da_decomporre] = Counter({f"Da Procurare (Def: {pkmn_def.log_str()})": 1})
        return cache_decomposizione[nome_pkmn_da_decomporre].copy()

    if piano_valutato.pokemon_target_finale_piano and piano_valutato.pokemon_target_finale_piano.nome_formattato_dal_piano:
        necessari_base.update(decomponi_in_base_ricorsivo(piano_valutato.pokemon_target_finale_piano.nome_formattato_dal_piano))
    
    return necessari_base

# --- Logica Principale Fase 2 ---
def run_fase2(file_piani_json: str, owned_pokemon_list: List[PokemonPossedutoF2], file_debug_log: str, file_output_fase3: str):
    log_debug_lines: List[str] = [] 
    def log_debug(message: Any): 
        pass

    print("--- Fase 2: Valutazione Piani di Breeding ---")

    pokemon_posseduti_originali: List[PokemonPossedutoF2] = list(owned_pokemon_list)

    piani_da_analizzare: List[PianoCompletoF2] = []
    natura_target_globale_letta_dal_json = ""
    try:
        with open(file_piani_json, "r", encoding="utf-8") as f_piani:
            piani_file_data = json.load(f_piani)
            natura_target_globale_letta_dal_json = piani_file_data.get("natura_target_specifica", "")

            for piano_data_item in piani_file_data.get("piani", []):
                piano_obj = PianoCompletoF2(
                    id_piano_fase1=piano_data_item.get("id_piano_fase1", 0),
                    legenda_usata=piano_data_item.get("legenda_usata", {}),
                    percorso_A=deserialize_percorso_def_f2(piano_data_item.get("percorso_A")),
                    percorso_B=deserialize_percorso_def_f2(piano_data_item.get("percorso_B")),
                    pokemon_target_finale_piano=deserialize_pokemon_def_f2(piano_data_item.get("pokemon_target_finale_piano")),
                    natura_target_specifica_del_piano_globale=natura_target_globale_letta_dal_json 
                )
                piani_da_analizzare.append(piano_obj)
    except FileNotFoundError:
        print(f"Errore: Impossibile aprire il file dei piani: {file_piani_json}", file=sys.stderr)
        return 
    except json.JSONDecodeError:
        print(f"Errore: Formato JSON non valido in {file_piani_json}", file=sys.stderr)
        return 

    piani_valutati: List[PianoCompletoF2] = []

    if not piani_da_analizzare:
        print("\nNessun piano da analizzare. Esecuzione terminata.")
        return

    for piano_idx, current_piano_obj in enumerate(piani_da_analizzare):
        reset_soddisfazione_piano(current_piano_obj) 
        
        id_pkmn_usati_in_questo_piano_set_temp: Set[str] = set() 
        current_piano_obj.mappa_richiesto_a_posseduto.clear() 
        current_piano_obj.punteggio_ottenuto = 0.0
        current_piano_obj.pokemon_matchati_count = 0
        
        pokemon_da_matchare_nel_piano: List[PokemonDefF2] = []
        percorsi_del_piano_corrente_temp = []
        if current_piano_obj.percorso_A and current_piano_obj.percorso_A.valido: 
            percorsi_del_piano_corrente_temp.append(current_piano_obj.percorso_A)
        if current_piano_obj.percorso_B and current_piano_obj.percorso_B.valido: 
            percorsi_del_piano_corrente_temp.append(current_piano_obj.percorso_B)

        for percorso_attivo_obj in percorsi_del_piano_corrente_temp:
            for livello_obj in percorso_attivo_obj.livelli:
                for accoppiamento_obj in livello_obj.accoppiamenti:
                    if accoppiamento_obj.genitore1_richiesto and accoppiamento_obj.genitore1_richiesto.nome_formattato_dal_piano:
                        pokemon_da_matchare_nel_piano.append(accoppiamento_obj.genitore1_richiesto)
                    if accoppiamento_obj.genitore2_richiesto and accoppiamento_obj.genitore2_richiesto.nome_formattato_dal_piano:
                        pokemon_da_matchare_nel_piano.append(accoppiamento_obj.genitore2_richiesto)
        
        if current_piano_obj.percorso_A and current_piano_obj.percorso_A.valido and current_piano_obj.percorso_A.risultato_percorso and \
           current_piano_obj.percorso_A.risultato_percorso.nome_formattato_dal_piano and \
           current_piano_obj.percorso_A.risultato_percorso not in pokemon_da_matchare_nel_piano:
            pokemon_da_matchare_nel_piano.append(current_piano_obj.percorso_A.risultato_percorso)
        
        if current_piano_obj.percorso_B and current_piano_obj.percorso_B.valido and current_piano_obj.percorso_B.risultato_percorso and \
           current_piano_obj.percorso_B.risultato_percorso.nome_formattato_dal_piano and \
           current_piano_obj.percorso_B.risultato_percorso not in pokemon_da_matchare_nel_piano:
            pokemon_da_matchare_nel_piano.append(current_piano_obj.percorso_B.risultato_percorso)

        pokemon_da_matchare_nel_piano.sort(key=lambda p: (len(p.ivs), bool(p.natura)), reverse=True)
        pokemon_da_matchare_unici = list(dict.fromkeys(pokemon_da_matchare_nel_piano))

        for pkmn_richiesto_obj in pokemon_da_matchare_unici:
            if pkmn_richiesto_obj.soddisfatto_da_posseduto: 
                continue
            best_match_pokemon_info_temp: Optional[PokemonPossedutoF2] = None
            for poss_candidate_obj in pokemon_posseduti_originali:
                if poss_candidate_obj.id_utente in id_pkmn_usati_in_questo_piano_set_temp: continue 
                iv_match_esatto = sorted(poss_candidate_obj.ivs) == sorted(pkmn_richiesto_obj.ivs)
                nat_match_esatto = natura_match_fase2(poss_candidate_obj.natura, pkmn_richiesto_obj.natura, current_piano_obj.natura_target_specifica_del_piano_globale)
                if iv_match_esatto and nat_match_esatto:
                    best_match_pokemon_info_temp = poss_candidate_obj
                    break 
            if not best_match_pokemon_info_temp:
                for poss_candidate_obj in pokemon_posseduti_originali:
                    if poss_candidate_obj.id_utente in id_pkmn_usati_in_questo_piano_set_temp: continue
                    iv_match_sottoinsieme = all(req_iv in poss_candidate_obj.ivs for req_iv in pkmn_richiesto_obj.ivs)
                    nat_match_sottoinsieme = natura_match_fase2(poss_candidate_obj.natura, pkmn_richiesto_obj.natura, current_piano_obj.natura_target_specifica_del_piano_globale)
                    if iv_match_sottoinsieme and nat_match_sottoinsieme:
                        if best_match_pokemon_info_temp is None or \
                           len(poss_candidate_obj.ivs) < len(best_match_pokemon_info_temp.ivs):
                            best_match_pokemon_info_temp = poss_candidate_obj
            if best_match_pokemon_info_temp:
                id_pkmn_usati_in_questo_piano_set_temp.add(best_match_pokemon_info_temp.id_utente)
                pkmn_richiesto_obj.soddisfatto_da_posseduto = True
                pkmn_richiesto_obj.soddisfatto_da_id_utente = best_match_pokemon_info_temp.id_utente
                current_piano_obj.mappa_richiesto_a_posseduto[pkmn_richiesto_obj.nome_formattato_dal_piano] = best_match_pokemon_info_temp.id_utente
                current_piano_obj.punteggio_ottenuto += calcola_punteggio_pokemon_fase2(pkmn_richiesto_obj)
                current_piano_obj.pokemon_matchati_count += 1

        current_piano_obj.id_pokemon_posseduti_usati_unici = id_pkmn_usati_in_questo_piano_set_temp
        piani_valutati.append(current_piano_obj)

    piani_candidati_per_fase3: List[PianoCompletoF2] = []
    if piani_valutati:
        piani_valutati.sort(key=lambda p_sort: (p_sort.punteggio_ottenuto, p_sort.pokemon_matchati_count, -len(p_sort.id_pokemon_posseduti_usati_unici)), reverse=True)
        
        if piani_valutati: 
            miglior_punteggio_assoluto = piani_valutati[0].punteggio_ottenuto
            miglior_match_count_a_parita_punteggio = piani_valutati[0].pokemon_matchati_count
            piani_top_tier = [p_filter for p_filter in piani_valutati if p_filter.punteggio_ottenuto == miglior_punteggio_assoluto and \
                                                           p_filter.pokemon_matchati_count == miglior_match_count_a_parita_punteggio]
            piani_candidati_per_fase3 = piani_top_tier

            if piani_candidati_per_fase3:
                print(f"\n{GREEN_BOLD_TERMINAL}--- {len(piani_candidati_per_fase3)} Piano/i Candidato/i Trovato/i per la Fase 3 ---{RESET_TERMINAL}")
                for i, piano_cand_obj in enumerate(piani_candidati_per_fase3):
                    piano_cand_obj.pokemon_base_necessari_calcolati = dict(calcola_pokemon_base_necessari_f2(piano_cand_obj))
                    if i == 0: 
                        print(f"Dettagli del Primo Candidato (ID Piano Fase 1: {piano_cand_obj.id_piano_fase1}):")
                output_data_fase3_list = [p_final.to_dict_per_fase3() for p_final in piani_candidati_per_fase3]
                try:
                    with open(file_output_fase3, "w", encoding="utf-8") as f_out_f3:
                        json.dump(output_data_fase3_list, f_out_f3, indent=2)
                    print(f"\nDati dei {len(piani_candidati_per_fase3)} piani candidati esportati in '{file_output_fase3}' per la Fase 3.")
                except IOError:
                    print(f"Errore: Impossibile scrivere il file di output per la Fase 3: {file_output_fase3}", file=sys.stderr)
            else: 
                print("\nNessun piano candidato trovato dopo la valutazione e filtraggio.")
        else: 
            print("\nNessun piano valutato disponibile.")
    else: 
        print("\nNessun piano caricato da analizzare.")
