import json
import itertools
import math
import os
from dataclasses import dataclass, field
from typing import List, Dict, Optional, Tuple, Any, Set
import sys
from collections import Counter # Utile per contare i Pokémon base

# --- Costanti per i colori nel terminale ---
GREEN_TERMINAL = '\033[32m'
YELLOW_BOLD_TERMINAL = '\033[1;33m'
GREEN_BOLD_TERMINAL = '\033[1;32m'
RESET_TERMINAL = '\033[0m'

# --- Strutture Dati Fase 1 (Invariate) ---
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

# --- Funzioni Helper Fase 1 (Invariate) ---
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
        colori_ordinati_legenda = list(legenda_stat_to_colore_ruolo.values())
        temp_iv_colore_map = {iv: colore_ruolo_per_stat_iv_f1(iv, legenda_stat_to_colore_ruolo) for iv in unique_sorted_ivs}
        try:
            ivs_ordinate_per_desc = sorted(unique_sorted_ivs, key=lambda iv: colori_ordinati_legenda.index(temp_iv_colore_map[iv]) if temp_iv_colore_map[iv] in colori_ordinati_legenda else float('inf'))
        except ValueError:
            ivs_ordinate_per_desc = unique_sorted_ivs
    else:
        ivs_ordinate_per_desc = unique_sorted_ivs


    for iv_stat in ivs_ordinate_per_desc:
        nomi_colori_aggregati += colore_ruolo_per_stat_iv_f1(iv_stat, legenda_stat_to_colore_ruolo)
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
    legenda_stat_to_colore_ruolo: Dict[str, str],
    iv_target_specifiche_per_path_a: List[str],
    num_iv_output_percorso_a: int
) -> PokemonJsonF1:
    percorso_a_json.valido = True
    percorso_a_json.tipo_percorso = "A"
    percorso_a_json.livelli = []

    color_roles_path_a = ["Blu", "Rosso", "Giallo", "Grigio", "Arancione"]
    iv_map = {}
    for i, role_color in enumerate(color_roles_path_a):
        if i < len(iv_target_specifiche_per_path_a):
            iv_map[role_color] = iv_target_specifiche_per_path_a[i]
        else:
            iv_map[role_color] = f"PH_{role_color}_A"

    outfile_text.write("--- Percorso A: \"Albero solo statistiche\" ---\n")
    if 0 < num_iv_output_percorso_a < 5 :
         outfile_text.write(f"(Troncato per produrre {num_iv_output_percorso_a} IVs)\n")

    ref_str_list = []
    for i in range(min(num_iv_output_percorso_a, 5)):
        color = color_roles_path_a[i]
        if not iv_map[color].startswith("PH_"):
            ref_str_list.append(f"{color}={iv_map[color]}")
    outfile_text.write(f"(Riferimento IV ruoli usati: {', '.join(ref_str_list)})\n\n")

    def safe_iv_list(*iv_role_names):
        return [iv_map[name] for name in iv_role_names if not iv_map[name].startswith("PH_")]

    l0_pkmn = {role: crea_pokemon_json_f1(safe_iv_list(role), "", legenda_stat_to_colore_ruolo)
               for i, role in enumerate(color_roles_path_a) if i < num_iv_output_percorso_a and not iv_map[role].startswith("PH_")}

    l1_pkmn = {}
    if num_iv_output_percorso_a >= 2:
        liv1_json = LivelloJsonF1(livello_id=1)
        outfile_text.write("**Livello 1 (Percorso A): Accoppiamenti di Base**\n")

        accoppiamenti_l1_def = [("Blu", "Rosso"), ("Blu", "Giallo"), ("Rosso", "Giallo"),
                                ("Rosso", "Grigio"), ("Giallo", "Grigio"), ("Giallo", "Arancione")]

        count = 0
        for r1_name, r2_name in accoppiamenti_l1_def:
            idx1 = color_roles_path_a.index(r1_name)
            idx2 = color_roles_path_a.index(r2_name)
            if idx1 < num_iv_output_percorso_a and idx2 < num_iv_output_percorso_a:
                g1 = l0_pkmn.get(r1_name)
                g2 = l0_pkmn.get(r2_name)
                if g1 and g1.ivs and g2 and g2.ivs:
                    figlio_ivs = sorted(list(set(g1.ivs + g2.ivs)))
                    figlio = crea_pokemon_json_f1(figlio_ivs, "", legenda_stat_to_colore_ruolo)
                    l1_pkmn[f"{r1_name}{r2_name}"] = figlio

                    is_target_l1 = (len(figlio_ivs) == num_iv_output_percorso_a and num_iv_output_percorso_a == 2)
                    liv1_json.accoppiamenti.append(AccoppiamentoJsonF1(g1, g2, figlio))
                    count += 1
                    outfile_text.write(f"{count}. {g1.nome_formattato if g1 else 'N/A'} + {g2.nome_formattato if g2 else 'N/A'} -> genera {figlio.nome_formattato}{' (TARGET)' if is_target_l1 else ''}\n")
        if liv1_json.accoppiamenti: percorso_a_json.livelli.append(liv1_json)
        outfile_text.write("\n")
        if num_iv_output_percorso_a == 2 and l1_pkmn:
            percorso_a_json.risultato_percorso = list(l1_pkmn.values())[0] if l1_pkmn else PokemonJsonF1()
            return percorso_a_json.risultato_percorso
    elif num_iv_output_percorso_a == 1 and l0_pkmn:
        percorso_a_json.risultato_percorso = list(l0_pkmn.values())[0] if l0_pkmn else PokemonJsonF1()
        return percorso_a_json.risultato_percorso
    elif num_iv_output_percorso_a == 0:
        percorso_a_json.risultato_percorso = PokemonJsonF1()
        return percorso_a_json.risultato_percorso

    l2_pkmn = {}
    if num_iv_output_percorso_a >= 3:
        liv2_json = LivelloJsonF1(livello_id=2)
        outfile_text.write("**Livello 2 (Percorso A): Prime Combinazioni**\n")
        accoppiamenti_l2_def = [
            (("Blu", "Rosso"), ("Blu", "Giallo"), ("Blu", "Rosso", "Giallo")),
            (("Rosso", "Giallo"), ("Rosso", "Grigio"), ("Rosso", "Giallo", "Grigio")),
            (("Giallo", "Grigio"), ("Giallo", "Arancione"), ("Giallo", "Grigio", "Arancione"))
        ]
        count = 0
        for (g1_r1, g1_r2), (g2_r1, g2_r2), figlio_roles_tuple in accoppiamenti_l2_def:
            figlio_iv_set = safe_iv_list(*figlio_roles_tuple)
            if len(figlio_iv_set) == 3 and max(color_roles_path_a.index(r) for r in figlio_roles_tuple) < num_iv_output_percorso_a:
                g1 = l1_pkmn.get(f"{g1_r1}{g1_r2}")
                g2 = l1_pkmn.get(f"{g2_r1}{g2_r2}")
                if g1 and g2:
                    figlio = crea_pokemon_json_f1(figlio_iv_set, "", legenda_stat_to_colore_ruolo)
                    l2_pkmn["".join(sorted(figlio_roles_tuple))] = figlio
                    is_target_l2 = (len(figlio_iv_set) == num_iv_output_percorso_a and num_iv_output_percorso_a == 3)
                    liv2_json.accoppiamenti.append(AccoppiamentoJsonF1(g1,g2,figlio))
                    count+=1
                    outfile_text.write(f"{count}. {g1.nome_formattato} + {g2.nome_formattato} -> genera {figlio.nome_formattato}{' (TARGET)' if is_target_l2 else ''}\n")
        if liv2_json.accoppiamenti: percorso_a_json.livelli.append(liv2_json)
        outfile_text.write("\n")
        if num_iv_output_percorso_a == 3 and l2_pkmn:
            percorso_a_json.risultato_percorso = list(l2_pkmn.values())[0] if l2_pkmn else PokemonJsonF1()
            return percorso_a_json.risultato_percorso

    l3_pkmn = {}
    if num_iv_output_percorso_a >= 4:
        liv3_json = LivelloJsonF1(livello_id=3)
        outfile_text.write("**Livello 3 (Percorso A): Combinazioni Avanzate**\n")
        accoppiamenti_l3_def = [
            (("Blu", "Rosso", "Giallo"), ("Rosso", "Giallo", "Grigio"), ("Blu", "Rosso", "Giallo", "Grigio")),
            (("Rosso", "Giallo", "Grigio"), ("Giallo", "Grigio", "Arancione"), ("Rosso", "Giallo", "Grigio", "Arancione"))
        ]
        count = 0
        for g1_roles_tuple, g2_roles_tuple, figlio_roles_tuple in accoppiamenti_l3_def:
            figlio_iv_set = safe_iv_list(*figlio_roles_tuple)
            if len(figlio_iv_set) == 4 and max(color_roles_path_a.index(r) for r in figlio_roles_tuple) < num_iv_output_percorso_a:
                g1 = l2_pkmn.get("".join(sorted(g1_roles_tuple)))
                g2 = l2_pkmn.get("".join(sorted(g2_roles_tuple)))
                if g1 and g2:
                    figlio = crea_pokemon_json_f1(figlio_iv_set, "", legenda_stat_to_colore_ruolo)
                    l3_pkmn["".join(sorted(figlio_roles_tuple))] = figlio
                    is_target_l3 = (len(figlio_iv_set) == num_iv_output_percorso_a and num_iv_output_percorso_a == 4)
                    liv3_json.accoppiamenti.append(AccoppiamentoJsonF1(g1,g2,figlio))
                    count+=1
                    outfile_text.write(f"{count}. {g1.nome_formattato} + {g2.nome_formattato} -> genera {figlio.nome_formattato}{' (TARGET)' if is_target_l3 else ''}\n")
        if liv3_json.accoppiamenti: percorso_a_json.livelli.append(liv3_json)
        outfile_text.write("\n")
        if num_iv_output_percorso_a == 4 and l3_pkmn:
            percorso_a_json.risultato_percorso = list(l3_pkmn.values())[0] if l3_pkmn else PokemonJsonF1()
            return percorso_a_json.risultato_percorso

    l4_pkmn = {}
    figlio_l4_roles_tuple = ("Blu", "Rosso", "Giallo", "Grigio", "Arancione")
    if num_iv_output_percorso_a >= 5:
        liv4_json = LivelloJsonF1(livello_id=4)
        outfile_text.write("**Livello 4 (Percorso A): Risultato del Percorso A**\n")
        g1_roles_tuple = ("Blu", "Rosso", "Giallo", "Grigio")
        g2_roles_tuple = ("Rosso", "Giallo", "Grigio", "Arancione")

        figlio_iv_set = safe_iv_list(*figlio_l4_roles_tuple)

        if len(figlio_iv_set) == 5:
            g1 = l3_pkmn.get("".join(sorted(g1_roles_tuple)))
            g2 = l3_pkmn.get("".join(sorted(g2_roles_tuple)))
            if g1 and g2:
                figlio = crea_pokemon_json_f1(figlio_iv_set, "", legenda_stat_to_colore_ruolo)
                l4_pkmn["".join(sorted(figlio_l4_roles_tuple))] = figlio
                is_target_l4 = (len(figlio_iv_set) == num_iv_output_percorso_a and num_iv_output_percorso_a == 5)
                liv4_json.accoppiamenti.append(AccoppiamentoJsonF1(g1,g2,figlio))
                outfile_text.write(f"1. {g1.nome_formattato} + {g2.nome_formattato} -> Genitore A: {figlio.nome_formattato}{' (TARGET)' if is_target_l4 else ''}\n\n")
                percorso_a_json.risultato_percorso = figlio
                if liv4_json.accoppiamenti: percorso_a_json.livelli.append(liv4_json)
                return figlio

    keys_l4 = list(l4_pkmn.keys())
    keys_l3 = list(l3_pkmn.keys())
    keys_l2 = list(l2_pkmn.keys())
    keys_l1 = list(l1_pkmn.keys())

    if num_iv_output_percorso_a == 5 and keys_l4: percorso_a_json.risultato_percorso = l4_pkmn[keys_l4[0]]
    elif num_iv_output_percorso_a == 4 and keys_l3: percorso_a_json.risultato_percorso = l3_pkmn[keys_l3[0]]
    elif num_iv_output_percorso_a == 3 and keys_l2: percorso_a_json.risultato_percorso = l2_pkmn[keys_l2[0]]
    elif num_iv_output_percorso_a == 2 and keys_l1: percorso_a_json.risultato_percorso = l1_pkmn[keys_l1[0]]
    elif num_iv_output_percorso_a == 1 and l0_pkmn: percorso_a_json.risultato_percorso = list(l0_pkmn.values())[0]
    elif num_iv_output_percorso_a == 0: percorso_a_json.risultato_percorso = PokemonJsonF1()
    else:
        if l4_pkmn and keys_l4 : percorso_a_json.risultato_percorso = l4_pkmn[keys_l4[-1]]
        elif l3_pkmn and keys_l3 : percorso_a_json.risultato_percorso = l3_pkmn[keys_l3[-1]]
        elif l2_pkmn and keys_l2: percorso_a_json.risultato_percorso = l2_pkmn[keys_l2[-1]]
        elif l1_pkmn and keys_l1: percorso_a_json.risultato_percorso = l1_pkmn[keys_l1[-1]]
        elif l0_pkmn: percorso_a_json.risultato_percorso = list(l0_pkmn.values())[0]
        else: percorso_a_json.risultato_percorso = PokemonJsonF1()

    return percorso_a_json.risultato_percorso

def genera_percorso_b_fase1(
    outfile_text,
    percorso_b_json: PercorsoJsonF1,
    legenda_stat_to_colore_ruolo: Dict[str, str],
    natura_obiettivo_specifica: str,
    iv_target_natura: List[str],
    num_iv_richieste_con_natura: int
) -> PokemonJsonF1:
    percorso_b_json.valido = True
    percorso_b_json.tipo_percorso = "B"
    percorso_b_json.livelli = []

    path_b_iv_roles = ["R1", "R2", "R3", "R4"]
    iv_map_b = {}
    for i, role_name in enumerate(path_b_iv_roles):
        if i < len(iv_target_natura):
            iv_map_b[role_name] = iv_target_natura[i]
        else:
            iv_map_b[role_name] = f"PH_B_{role_name}"

    iv_count_for_title = num_iv_richieste_con_natura
    iv_count_str = f"{iv_count_for_title} statistiche" if iv_count_for_title > 0 else "0 statistiche"
    outfile_text.write(f"--- Percorso B: \"Albero {iv_count_str} e {natura_obiettivo_specifica}\" ---\n")
    if 0 <= num_iv_richieste_con_natura < 4 :
         outfile_text.write(f"(Troncato per target {natura_obiettivo_specifica} + {num_iv_richieste_con_natura}iv)\n")

    ref_b_str_list = []
    for i in range(min(num_iv_richieste_con_natura, 4)):
        role_name = path_b_iv_roles[i]
        stat_iv_for_role = iv_map_b[role_name]
        if not stat_iv_for_role.startswith("PH_"):
            colore_reale_stat = colore_ruolo_per_stat_iv_f1(stat_iv_for_role, legenda_stat_to_colore_ruolo)
            ref_b_str_list.append(f"Ruolo{i+1}({colore_reale_stat})={stat_iv_for_role}")

    outfile_text.write(f"(Riferimento IV ruoli usati: {', '.join(ref_b_str_list)})\n\n")

    def safe_iv_list_b(*iv_role_keys):
        return [iv_map_b[key] for key in iv_role_keys if not iv_map_b[key].startswith("PH_")]

    l0b_natura = crea_pokemon_json_f1([], natura_obiettivo_specifica, legenda_stat_to_colore_ruolo)
    l0b_iv_pkmn = {role: crea_pokemon_json_f1(safe_iv_list_b(role), "", legenda_stat_to_colore_ruolo)
                   for i,role in enumerate(path_b_iv_roles) if i < num_iv_richieste_con_natura and not iv_map_b[role].startswith("PH_")}

    l1_pkmn = {}
    if num_iv_richieste_con_natura >= 0:
        liv1_json = LivelloJsonF1(livello_id=1)
        outfile_text.write("**Livello 1 (Percorso B): Accoppiamenti di Base**\n")
        num_acc_l1 = 0

        if num_iv_richieste_con_natura >= 1 and "R1" in l0b_iv_pkmn:
            g1, g2 = l0b_natura, l0b_iv_pkmn["R1"]
            figlio = crea_pokemon_json_f1(g2.ivs, natura_obiettivo_specifica, legenda_stat_to_colore_ruolo)
            l1_pkmn["N+R1"] = figlio
            is_target = (num_iv_richieste_con_natura == 1)
            liv1_json.accoppiamenti.append(AccoppiamentoJsonF1(g1,g2,figlio))
            num_acc_l1+=1
            outfile_text.write(f"{num_acc_l1}. {g1.nome_formattato} + {g2.nome_formattato} -> genera {figlio.nome_formattato}{' (TARGET)' if is_target else ''}\n")
        elif num_iv_richieste_con_natura == 0:
            l1_pkmn["N+R1"] = l0b_natura
            liv1_json.accoppiamenti.append(AccoppiamentoJsonF1(l0b_natura, PokemonJsonF1(nome_formattato="(qualsiasi)"), l0b_natura))
            num_acc_l1+=1
            outfile_text.write(f"{num_acc_l1}. {l0b_natura.nome_formattato} + (qualsiasi) -> genera {l0b_natura.nome_formattato} (TARGET)\n")
            percorso_b_json.risultato_percorso = l0b_natura
            if liv1_json.accoppiamenti: percorso_b_json.livelli.append(liv1_json); outfile_text.write("\n")
            return l0b_natura

        accoppiamenti_l1_iv_roles = [("R1","R2"), ("R1","R3"), ("R2","R3"), ("R2","R4")]
        for r1_key, r2_key in accoppiamenti_l1_iv_roles:
            idx1 = path_b_iv_roles.index(r1_key)
            idx2 = path_b_iv_roles.index(r2_key)
            if idx1 < num_iv_richieste_con_natura and idx2 < num_iv_richieste_con_natura:
                g1 = l0b_iv_pkmn.get(r1_key)
                g2 = l0b_iv_pkmn.get(r2_key)
                if g1 and g1.ivs and g2 and g2.ivs:
                    figlio_ivs = sorted(list(set(g1.ivs + g2.ivs)))
                    if len(figlio_ivs) == 2:
                        figlio = crea_pokemon_json_f1(figlio_ivs, "", legenda_stat_to_colore_ruolo)
                        l1_pkmn[f"{r1_key}+{r2_key}"] = figlio
                        liv1_json.accoppiamenti.append(AccoppiamentoJsonF1(g1,g2,figlio))
                        num_acc_l1+=1
                        outfile_text.write(f"{num_acc_l1}. {g1.nome_formattato} + {g2.nome_formattato} -> genera {figlio.nome_formattato}\n")

        if liv1_json.accoppiamenti: percorso_b_json.livelli.append(liv1_json); outfile_text.write("\n")
        if num_iv_richieste_con_natura == 1 and "N+R1" in l1_pkmn:
            percorso_b_json.risultato_percorso = l1_pkmn["N+R1"]
            return l1_pkmn["N+R1"]

    l2_pkmn = {}
    if num_iv_richieste_con_natura >= 2:
        liv2_json = LivelloJsonF1(livello_id=2)
        outfile_text.write("**Livello 2 (Percorso B): Prime Combinazioni**\n")
        num_acc_l2 = 0
        if "N+R1" in l1_pkmn and "R1+R2" in l1_pkmn:
            g1, g2 = l1_pkmn["N+R1"], l1_pkmn["R1+R2"]
            figlio_ivs = sorted(list(set(g1.ivs + g2.ivs)))
            if len(figlio_ivs) == 2:
                figlio = crea_pokemon_json_f1(figlio_ivs, natura_obiettivo_specifica, legenda_stat_to_colore_ruolo)
                l2_pkmn["N+R1R2"] = figlio
                is_target = (num_iv_richieste_con_natura == 2)
                liv2_json.accoppiamenti.append(AccoppiamentoJsonF1(g1,g2,figlio))
                num_acc_l2+=1
                outfile_text.write(f"{num_acc_l2}. {g1.nome_formattato} + {g2.nome_formattato} -> genera {figlio.nome_formattato}{' (TARGET)' if is_target else ''}\n")

        accoppiamenti_3iv_def = [("R1+R2", "R1+R3", "R1R2R3"), ("R2+R3", "R2+R4", "R2R3R4")]
        for g1_key, g2_key, figlio_key_base in accoppiamenti_3iv_def:
            max_role_idx_figlio = -1
            if figlio_key_base == "R1R2R3": max_role_idx_figlio = path_b_iv_roles.index("R3")
            elif figlio_key_base == "R2R3R4": max_role_idx_figlio = path_b_iv_roles.index("R4")

            if max_role_idx_figlio != -1 and max_role_idx_figlio < num_iv_richieste_con_natura :
                g1 = l1_pkmn.get(g1_key)
                g2 = l1_pkmn.get(g2_key)
                if g1 and g2:
                    figlio_ivs = sorted(list(set(g1.ivs+g2.ivs)))
                    if len(figlio_ivs) == 3:
                        figlio = crea_pokemon_json_f1(figlio_ivs, "", legenda_stat_to_colore_ruolo)
                        l2_pkmn[figlio_key_base] = figlio
                        liv2_json.accoppiamenti.append(AccoppiamentoJsonF1(g1,g2,figlio))
                        num_acc_l2+=1
                        g1_display = f"({g1.nome_formattato} duplicato)" if num_acc_l2 > 1 and liv2_json.accoppiamenti[-2].genitore2_richiesto.nome_formattato == g1.nome_formattato else g1.nome_formattato
                        outfile_text.write(f"{num_acc_l2}. {g1_display} + {g2.nome_formattato} -> genera {figlio.nome_formattato}\n")

        if liv2_json.accoppiamenti: percorso_b_json.livelli.append(liv2_json); outfile_text.write("\n")
        if num_iv_richieste_con_natura == 2 and "N+R1R2" in l2_pkmn:
            percorso_b_json.risultato_percorso = l2_pkmn["N+R1R2"]
            return l2_pkmn["N+R1R2"]

    l3_pkmn = {}
    if num_iv_richieste_con_natura >= 3:
        liv3_json = LivelloJsonF1(livello_id=3)
        outfile_text.write("**Livello 3 (Percorso B): Combinazioni Avanzate**\n")
        num_acc_l3 = 0
        if "N+R1R2" in l2_pkmn and "R1R2R3" in l2_pkmn:
            g1, g2 = l2_pkmn["N+R1R2"], l2_pkmn["R1R2R3"]
            figlio_ivs = sorted(list(set(g1.ivs + g2.ivs)))
            if len(figlio_ivs) == 3:
                figlio = crea_pokemon_json_f1(figlio_ivs, natura_obiettivo_specifica, legenda_stat_to_colore_ruolo)
                l3_pkmn["N+R1R2R3"] = figlio
                is_target = (num_iv_richieste_con_natura == 3)
                liv3_json.accoppiamenti.append(AccoppiamentoJsonF1(g1,g2,figlio))
                num_acc_l3+=1
                outfile_text.write(f"{num_acc_l3}. {g1.nome_formattato} + {g2.nome_formattato} -> genera {figlio.nome_formattato}{' (TARGET)' if is_target else ''}\n")

        if num_iv_richieste_con_natura >=4 and "R1R2R3" in l2_pkmn and "R2R3R4" in l2_pkmn:
            g1, g2 = l2_pkmn["R1R2R3"], l2_pkmn["R2R3R4"]
            figlio_ivs = sorted(list(set(g1.ivs + g2.ivs)))
            if len(figlio_ivs) == 4:
                figlio = crea_pokemon_json_f1(figlio_ivs, "", legenda_stat_to_colore_ruolo)
                l3_pkmn["R1R2R3R4"] = figlio
                liv3_json.accoppiamenti.append(AccoppiamentoJsonF1(g1,g2,figlio))
                num_acc_l3+=1
                g1_display = f"({g1.nome_formattato} duplicato)" if num_acc_l3 > 1 and liv3_json.accoppiamenti[-2].genitore2_richiesto.nome_formattato == g1.nome_formattato else g1.nome_formattato
                outfile_text.write(f"{num_acc_l3}. {g1_display} + {g2.nome_formattato} -> genera {figlio.nome_formattato}\n")

        if liv3_json.accoppiamenti: percorso_b_json.livelli.append(liv3_json); outfile_text.write("\n")
        if num_iv_richieste_con_natura == 3 and "N+R1R2R3" in l3_pkmn:
            percorso_b_json.risultato_percorso = l3_pkmn["N+R1R2R3"]
            return l3_pkmn["N+R1R2R3"]

    l4_pkmn = {}
    if num_iv_richieste_con_natura >= 4:
        liv4_json = LivelloJsonF1(livello_id=4)
        outfile_text.write("**Livello 4 (Percorso B): Risultato del Percorso B**\n")
        if "N+R1R2R3" in l3_pkmn and "R1R2R3R4" in l3_pkmn:
            g1, g2 = l3_pkmn["N+R1R2R3"], l3_pkmn["R1R2R3R4"]
            figlio_ivs = sorted(list(set(g1.ivs + g2.ivs)))
            if len(figlio_ivs) == 4:
                figlio = crea_pokemon_json_f1(figlio_ivs, natura_obiettivo_specifica, legenda_stat_to_colore_ruolo)
                l4_pkmn["N+R1R2R3R4"] = figlio
                is_target = (num_iv_richieste_con_natura == 4)
                liv4_json.accoppiamenti.append(AccoppiamentoJsonF1(g1,g2,figlio))
                outfile_text.write(f"1. {g1.nome_formattato} + {g2.nome_formattato} -> Genitore B: {figlio.nome_formattato}{' (TARGET)' if is_target else ''}\n\n")
        if liv4_json.accoppiamenti: percorso_b_json.livelli.append(liv4_json)
        if num_iv_richieste_con_natura == 4 and "N+R1R2R3R4" in l4_pkmn:
            percorso_b_json.risultato_percorso = l4_pkmn["N+R1R2R3R4"]
            return l4_pkmn["N+R1R2R3R4"]

    final_result_map_b = {
        0: l0b_natura, 1: l1_pkmn.get("N+R1"), 2: l2_pkmn.get("N+R1R2"),
        3: l3_pkmn.get("N+R1R2R3"), 4: l4_pkmn.get("N+R1R2R3R4")
    }
    result_pkmn_b = final_result_map_b.get(num_iv_richieste_con_natura)
    if result_pkmn_b is None: result_pkmn_b = PokemonJsonF1()

    percorso_b_json.risultato_percorso = result_pkmn_b
    return result_pkmn_b

# --- Logica Principale Fase 1 (Invariata) ---
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

    stats_per_modalita = []
    num_iv_target_per_colori = 0
    num_iv_output_percorso_a = 0
    num_iv_output_percorso_b = 0


    if modalita_operativa == "5IV+N":
        stats_per_modalita = stats_target_config if stats_target_config else ["PS", "ATT", "DEF", "SP.DEF", "Velocità"]
        num_iv_target_per_colori = 5
        num_iv_output_percorso_a = 5
        num_iv_output_percorso_b = 4
    elif modalita_operativa == "4IV+N":
        stats_per_modalita = stats_target_config if stats_target_config else ["SP.ATT", "DEF", "SP.DEF", "Velocità"]
        num_iv_target_per_colori = 4
        num_iv_output_percorso_a = 4
        num_iv_output_percorso_b = 3
    elif modalita_operativa == "3IV+N":
        stats_per_modalita = stats_target_config if stats_target_config else ["ATT", "DEF", "SP.DEF"]
        num_iv_target_per_colori = 3
        num_iv_output_percorso_a = 3
        num_iv_output_percorso_b = 2
    elif modalita_operativa == "2IV+N":
        stats_per_modalita = stats_target_config if stats_target_config else ["ATT", "DEF"]
        num_iv_target_per_colori = 2
        num_iv_output_percorso_a = 2
        num_iv_output_percorso_b = 1
    elif modalita_operativa == "0IV+N":
        stats_per_modalita = []
        num_iv_target_per_colori = 0
        num_iv_output_percorso_a = 0
        num_iv_output_percorso_b = 0
    elif modalita_operativa == "5IV_noN":
        stats_per_modalita = stats_target_config if stats_target_config else ["PS", "ATT", "DEF", "SP.DEF", "Velocità"]
        num_iv_target_per_colori = 5
        num_iv_output_percorso_a = 5
        num_iv_output_percorso_b = 0
    elif modalita_operativa == "4IV_noN":
        stats_per_modalita = stats_target_config if stats_target_config else ["PS", "ATT", "DEF", "SP.DEF"]
        num_iv_target_per_colori = 4
        num_iv_output_percorso_a = 4
        num_iv_output_percorso_b = 0
    else:
        print(f"Modalita' operativa non riconosciuta: {modalita_operativa}", file=sys.stderr)
        return

    nat_suffix = natura_obiettivo_spec if con_natura_obiettivo and natura_obiettivo_spec else ("Natura" if con_natura_obiettivo else "noNatura")
    nome_file_out_text = f"piani_{modalita_op_base}_{nat_suffix}_StatPerm.txt"
    stats_originali_per_titolo = list(stats_per_modalita)

    if len(stats_per_modalita) != num_iv_target_per_colori:
        print("Errore: discordanza tra numero IV target e dimensione statsPerModalita.", file=sys.stderr)
        return

    for stat in stats_per_modalita:
        if stat not in tutte_le_stat_iv_possibili:
            print(f"Errore: Statistica IV '{stat}' non valida.", file=sys.stderr)
            return
    if len(set(stats_per_modalita)) != len(stats_per_modalita) and num_iv_target_per_colori > 0 :
        print("Errore: Le statistiche IV target devono essere uniche.", file=sys.stderr)
        return

    colori_fissi_per_ruolo_iv = []
    if num_iv_target_per_colori > len(colori_disponibili_per_iv_base):
        print("Errore: Non ci sono abbastanza colori base per il numero di IV target.", file=sys.stderr)
        return
    for i in range(num_iv_target_per_colori):
        colori_fissi_per_ruolo_iv.append(colori_disponibili_per_iv_base[i])

    stats_per_modalita_ordinate_per_permutazioni = sorted(list(stats_per_modalita))
    num_piani_attesi_calc = math.factorial(num_iv_target_per_colori) if num_iv_target_per_colori > 0 else 1

    print(f"Modalita': {modalita_op_base} "
          f"{'+ ' + natura_obiettivo_spec if con_natura_obiettivo else 'senza Natura'}. "
          f"Stats target: {', '.join(stats_originali_per_titolo) if stats_originali_per_titolo else 'Nessuna IV'}. "
          f"Piani attesi (permutando STATISTICHE IV): {num_piani_attesi_calc}.")
    print(f"L'output testuale verra' scritto nel file '{nome_file_out_text}'...")
    print(f"L'output JSON verra' scritto nel file '{nome_file_out_json}'...")

    tutti_piani_json = []
    piano_count = 0

    with open(nome_file_out_text, "w", encoding="utf-8") as outfile_text_stream:
        title_ivs_str = "/".join(stats_originali_per_titolo) if stats_originali_per_titolo else "Nessuna IV"
        title_nat_str = f" + {natura_obiettivo_spec} (Verde)" if con_natura_obiettivo else ""
        outfile_text_stream.write(f"Piani di Accoppiamento per il set di IV Target: {title_ivs_str}{title_nat_str}\n")
        outfile_text_stream.write("(In questi piani, le STATISTICHE IV vengono permutate tra RUOLI COLORATI Fissi)\n\n")

        if num_iv_target_per_colori == 0 and con_natura_obiettivo:
            piano_count += 1
            piano_solo_natura_json = PianoJsonF1(id_piano_fase1=piano_count)
            pkmn_solo_natura = crea_pokemon_json_f1([], natura_obiettivo_spec, {})
            piano_solo_natura_json.percorso_B.valido = True
            piano_solo_natura_json.percorso_B.tipo_percorso = "B (Solo Natura)"
            liv1_solo_natura = LivelloJsonF1(livello_id=1)
            liv1_solo_natura.accoppiamenti.append(AccoppiamentoJsonF1(
                crea_pokemon_json_f1([], natura_obiettivo_spec, {}),
                PokemonJsonF1(nome_formattato="(qualsiasi)"), pkmn_solo_natura ))
            piano_solo_natura_json.percorso_B.livelli.append(liv1_solo_natura)
            piano_solo_natura_json.percorso_B.risultato_percorso = pkmn_solo_natura
            piano_solo_natura_json.pokemon_target_finale_piano = pkmn_solo_natura
            tutti_piani_json.append(piano_solo_natura_json)
            outfile_text_stream.write("==========================================================\n")
            outfile_text_stream.write(f"                     PIANO #{piano_count} (Solo {natura_obiettivo_spec})\n")
            outfile_text_stream.write("==========================================================\n\n")
            outfile_text_stream.write(f"Target: Ottenere un Pokémon con Natura {natura_obiettivo_spec}.\n")
            outfile_text_stream.write(f"1. Accoppiare un Pokémon con Natura {natura_obiettivo_spec} (tenendo Pietrastante) con qualsiasi altro Pokémon.\n")
            outfile_text_stream.write(f"   -> Pokémon Target: {pkmn_solo_natura.nome_formattato}\n\n")

        elif num_iv_target_per_colori >= 0:
            permutazioni_da_usare = list(itertools.permutations(stats_per_modalita_ordinate_per_permutazioni)) if stats_per_modalita_ordinate_per_permutazioni else [tuple()]
            for current_permutation_tuple in permutazioni_da_usare:
                current_permutation_list = list(current_permutation_tuple)
                piano_count += 1
                piano_corrente_json = PianoJsonF1(id_piano_fase1=piano_count)
                legenda_corrente_stat_to_colore_ruolo = {}
                for i, stat_permuted in enumerate(current_permutation_list):
                    if i < len(colori_fissi_per_ruolo_iv):
                         legenda_corrente_stat_to_colore_ruolo[stat_permuted] = colori_fissi_per_ruolo_iv[i]
                piano_corrente_json.legenda_usata = legenda_corrente_stat_to_colore_ruolo
                outfile_text_stream.write("==========================================================\n")
                outfile_text_stream.write(f"                     PIANO #{piano_count}\n")
                outfile_text_stream.write("==========================================================\n\n")
                if legenda_corrente_stat_to_colore_ruolo:
                    outfile_text_stream.write("### Legenda del Piano Corrente (Statistiche Permutate in Ruoli Colorati Fissi)\n")
                    for colore_fisso in colori_fissi_per_ruolo_iv:
                        stat_associata = None
                        for stat_perm, colore_assegnato in legenda_corrente_stat_to_colore_ruolo.items():
                            if colore_assegnato == colore_fisso:
                                stat_associata = stat_perm
                                break
                        if stat_associata:
                             outfile_text_stream.write(f"* **{colore_fisso}:** {stat_associata}\n")
                if con_natura_obiettivo:
                    outfile_text_stream.write(f"* **Verde:** {natura_obiettivo_spec} (rimane invariato)\n")
                outfile_text_stream.write("\n")

                ivs_per_percorso_a = current_permutation_list
                if num_iv_output_percorso_a > 0:
                    genera_percorso_a_fase1(outfile_text_stream, piano_corrente_json.percorso_A,
                                            legenda_corrente_stat_to_colore_ruolo,
                                            ivs_per_percorso_a,
                                            num_iv_output_percorso_a)

                ivs_per_percorso_b = current_permutation_list
                if con_natura_obiettivo or (not con_natura_obiettivo and num_iv_output_percorso_b > 0):
                    natura_per_b = natura_obiettivo_spec if con_natura_obiettivo else ""
                    genera_percorso_b_fase1(outfile_text_stream, piano_corrente_json.percorso_B,
                                            legenda_corrente_stat_to_colore_ruolo,
                                            natura_per_b,
                                            ivs_per_percorso_b,
                                            num_iv_output_percorso_b)

                target_ivs_finali_piano = list(current_permutation_list)
                natura_target_finale_json = natura_obiettivo_spec if con_natura_obiettivo else ""
                piano_corrente_json.pokemon_target_finale_piano = crea_pokemon_json_f1(
                    target_ivs_finali_piano, natura_target_finale_json, legenda_corrente_stat_to_colore_ruolo
                )

                if modalita_operativa == "5IV+N":
                    outfile_text_stream.write(f"--- Fine: L'Accoppiamento Finale del Piano 5IV+{natura_obiettivo_spec} ---\n")
                    outfile_text_stream.write(f"* Genitore A: {piano_corrente_json.percorso_A.risultato_percorso.nome_formattato if piano_corrente_json.percorso_A.valido else 'N/A'}\n")
                    outfile_text_stream.write("    +\n")
                    outfile_text_stream.write(f"* Genitore B: {piano_corrente_json.percorso_B.risultato_percorso.nome_formattato if piano_corrente_json.percorso_B.valido else 'N/A'}\n")
                    outfile_text_stream.write(f"    -> Pokémon Target: {piano_corrente_json.pokemon_target_finale_piano.nome_formattato}\n")
                elif modalita_operativa in ["4IV+N", "3IV+N", "2IV+N"]:
                    outfile_text_stream.write(f"--- Fine: L'Accoppiamento Finale del Piano {modalita_op_base}+{natura_obiettivo_spec} ---\n")
                    outfile_text_stream.write(f"* Genitore A (IVs): {piano_corrente_json.percorso_A.risultato_percorso.nome_formattato if piano_corrente_json.percorso_A.valido else 'N/A'}\n")
                    outfile_text_stream.write("    +\n")
                    outfile_text_stream.write(f"* Genitore B (Natura): {piano_corrente_json.percorso_B.risultato_percorso.nome_formattato if piano_corrente_json.percorso_B.valido else 'N/A'}\n")
                    outfile_text_stream.write(f"    -> Pokémon Target: {piano_corrente_json.pokemon_target_finale_piano.nome_formattato}\n")
                elif con_natura_obiettivo: # Handles 1IV+N and other specific cases if any
                    outfile_text_stream.write(f"--- Risultato Finale del Piano {modalita_op_base}+{natura_obiettivo_spec} ---\n")
                    outfile_text_stream.write(f"* Pokémon Target: {piano_corrente_json.pokemon_target_finale_piano.nome_formattato}\n")
                else: # Handles _noN modes
                    outfile_text_stream.write(f"--- Risultato Finale del Piano {modalita_op_base} ---\n")
                    outfile_text_stream.write(f"* Pokémon Target: {piano_corrente_json.pokemon_target_finale_piano.nome_formattato}\n")
                outfile_text_stream.write("\n\n")
                tutti_piani_json.append(piano_corrente_json)
        else:
             outfile_text_stream.write("Nessun IV target e nessuna Natura specificata. Nessun piano generato.\n")

    json_output_data = {
        "versione_formato": "1.0",
        "modalita_operativa_base": modalita_operativa + "_StatPerm",
        "stats_target_set": stats_originali_per_titolo,
        "piani": [p.to_dict() for p in tutti_piani_json]
    }
    if con_natura_obiettivo and natura_obiettivo_spec:
        json_output_data["natura_target_specifica"] = natura_obiettivo_spec

    with open(nome_file_out_json, "w", encoding="utf-8") as outfile_json_stream:
        json.dump(json_output_data, outfile_json_stream, indent=2)

    print(f"Output JSON scritto su '{nome_file_out_json}'.")
    print(f"Generazione Fase 1 completata. {piano_count} piani scritti su '{nome_file_out_text}'.\n")


# --- Strutture Dati Fase 2 (Aggiornate) ---
@dataclass
class PokemonDefF2:
    nome_formattato_dal_piano: str = ""
    ivs: List[str] = field(default_factory=list)
    natura: str = ""
    soddisfatto_da_posseduto: bool = False
    soddisfatto_da_id_utente: Optional[str] = None
    sesso_determinato: Optional[str] = None # Nuovo campo per il sesso

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

    def to_dict(self) -> Dict[str, Any]: # Per esportazione JSON
        return {
            "nome_formattato_dal_piano": self.nome_formattato_dal_piano,
            "ivs": self.ivs,
            "natura": self.natura,
            "soddisfatto_da_posseduto": self.soddisfatto_da_posseduto,
            "soddisfatto_da_id_utente": self.soddisfatto_da_id_utente,
            "sesso_determinato": self.sesso_determinato # Includi il nuovo campo
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'PokemonDefF2':
        return cls(
            nome_formattato_dal_piano=data.get("nome_formattato_dal_piano", ""),
            ivs=data.get("ivs", []),
            natura=data.get("natura", ""),
            soddisfatto_da_posseduto=data.get("soddisfatto_da_posseduto", False),
            soddisfatto_da_id_utente=data.get("soddisfatto_da_id_utente"),
            sesso_determinato=data.get("sesso_determinato") # Inizializza il nuovo campo
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
            "mappa_richiesto_a_posseduto": self.mappa_richiesto_a_posseduto # Esporta la mappa
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

# --- Funzioni Deserializzazione Fase 2 (Invariate) ---
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
        soddisfatto_da_posseduto=pkmn_data.get("soddisfatto_da_posseduto", False), # Mantenere lo stato se presente
        soddisfatto_da_id_utente=pkmn_data.get("soddisfatto_da_id_utente")       # Mantenere lo stato se presente
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


# --- Funzioni Logica Fase 2 (Invariate) ---
def ivs_match_fase2(possedute_param: List[str], richieste_param: List[str]) -> bool:
    if not richieste_param: return True
    return possedute_param == richieste_param

def natura_match_fase2(posseduta_nat: str, richiesta_nat_dal_pokemon_del_piano: str, natura_target_specifica_del_piano_globale: str) -> bool:
    req_trimmed = richiesta_nat_dal_pokemon_del_piano.strip() if richiesta_nat_dal_pokemon_del_piano else ""
    poss_trimmed = posseduta_nat.strip() if posseduta_nat else ""
    if not req_trimmed or req_trimmed.lower() == "null" or req_trimmed == '""': return True
    if req_trimmed == "NATURA":
        if not natura_target_specifica_del_piano_globale: return bool(poss_trimmed)
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
    elementi_da_resettare = []
    for percorso_key in ["percorso_A", "percorso_B"]:
        percorso = getattr(piano, percorso_key)
        if percorso.valido:
            elementi_da_resettare.append(percorso.risultato_percorso)
            for livello in percorso.livelli:
                for accoppiamento in livello.accoppiamenti:
                    elementi_da_resettare.extend([accoppiamento.genitore1_richiesto, accoppiamento.genitore2_richiesto, accoppiamento.figlio_generato])
    elementi_da_resettare.append(piano.pokemon_target_finale_piano)

    for pkmn_def in elementi_da_resettare:
        if pkmn_def:
            pkmn_def.soddisfatto_da_posseduto = False
            pkmn_def.soddisfatto_da_id_utente = None


# --- NUOVA FUNZIONE PER CONTEGGIO BASE FASE 2 (Invariata dalla v3) ---
def calcola_pokemon_base_necessari_f2(
    piano_valutato: PianoCompletoF2,
    log_debug_func
    ) -> Counter:
    necessari_base = Counter()
    ricette_pokedex_piano: Dict[str, Tuple[PokemonDefF2, PokemonDefF2]] = {}
    definizione_pkmn_nel_piano: Dict[str, PokemonDefF2] = {}

    def popola_definizioni_e_ricette(percorso: PercorsoDefF2):
        if not percorso.valido: return
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
    if piano_valutato.pokemon_target_finale_piano.nome_formattato_dal_piano:
        definizione_pkmn_nel_piano[piano_valutato.pokemon_target_finale_piano.nome_formattato_dal_piano] = piano_valutato.pokemon_target_finale_piano

    cache_decomposizione = {}

    def decomponi_in_base_ricorsivo(nome_pkmn_da_decomporre: str) -> Counter:
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
        if not pkmn_def.ivs and pkmn_def.natura:
            base_key = f"Solo Natura: {pkmn_def.natura}"
            is_base = True
        elif len(pkmn_def.ivs) == 1 and not pkmn_def.natura:
            iv_stat = pkmn_def.ivs[0]
            colore_ruolo = next((col for stat, col in piano_valutato.legenda_usata.items() if stat == iv_stat), "Sconosciuto")
            base_key = f"Solo IV: {iv_stat} ({colore_ruolo})"
            is_base = True

        if is_base:
            cache_decomposizione[nome_pkmn_da_decomporre] = Counter({base_key: 1})
            return cache_decomposizione[nome_pkmn_da_decomporre].copy()

        if nome_pkmn_da_decomporre in ricette_pokedex_piano:
            genitore1_def, genitore2_def = ricette_pokedex_piano[nome_pkmn_da_decomporre]
            req_g1 = decomponi_in_base_ricorsivo(genitore1_def.nome_formattato_dal_piano if genitore1_def else "")
            req_g2 = decomponi_in_base_ricorsivo(genitore2_def.nome_formattato_dal_piano if genitore2_def else "")
            risultato_decomposizione = req_g1 + req_g2
            cache_decomposizione[nome_pkmn_da_decomporre] = risultato_decomposizione
            return risultato_decomposizione.copy()

        log_debug_func(f"    Attenzione: {nome_pkmn_da_decomporre} non è base, non soddisfatto, e non ha ricetta chiara. Contato come 'Da Procurare'.")
        cache_decomposizione[nome_pkmn_da_decomporre] = Counter({f"Da Procurare (Definizione: {pkmn_def.log_str()})": 1})
        return cache_decomposizione[nome_pkmn_da_decomporre].copy()

    requisiti_totali_base = Counter()

    # Invece di partire solo dal target finale, si dovrebbe iterare su tutti i genitori richiesti
    # che non sono soddisfatti e che non sono figli di altri accoppiamenti (cioè, sono "radici" di sotto-alberi necessari)
    # Tuttavia, la logica di `decomponi_in_base_ricorsivo` già gestisce la decomposizione a partire da qualsiasi nodo.
    # Il punto di ingresso principale è il target finale del piano. Se questo non è soddisfatto,
    # la sua decomposizione coprirà tutti i suoi predecessori non soddisfatti.
    # Se il target finale È soddisfatto, ma altri rami del piano per arrivare a quel target non lo sono,
    # questo approccio potrebbe non contare quei rami.
    # La logica più robusta è iterare su TUTTI i genitori richiesti non soddisfatti.

    for percorso_key in ["percorso_A", "percorso_B"]:
        percorso = getattr(piano_valutato, percorso_key)
        if percorso.valido:
            for livello in percorso.livelli:
                for accoppiamento in livello.accoppiamenti:
                    for gen_slot_key in ["genitore1_richiesto", "genitore2_richiesto"]:
                        gen_richiesto = getattr(accoppiamento, gen_slot_key)
                        if gen_richiesto.nome_formattato_dal_piano and not gen_richiesto.soddisfatto_da_posseduto:
                            necessari_base.update(decomponi_in_base_ricorsivo(gen_richiesto.nome_formattato_dal_piano))

    return necessari_base

# --- Logica Principale Fase 2 (Modificata per esportare piani candidati) ---
def run_fase2(file_piani_json: str, owned_pokemon_list: List[PokemonPossedutoF2], file_debug_log: str, file_output_fase3: str):
    debug_log_lines = []
    def log_debug(message):
        debug_log_lines.append(str(message))

    log_debug("--- Inizio Log di Debug Fase 2 ---")
    print("--- Fase 2: Valutazione Piani di Breeding ---")
    log_debug("--- Fase 2: Valutazione Piani di Breeding ---")

    # pokemon_posseduti_originali ora viene direttamente da owned_pokemon_list
    pokemon_posseduti_originali: List[PokemonPossedutoF2] = list(owned_pokemon_list)
    print(f"{len(pokemon_posseduti_originali)} Pokémon posseduti ricevuti come parametro.")
    log_debug(f"{len(pokemon_posseduti_originali)} Pokémon posseduti ricevuti come parametro.")
    if pokemon_posseduti_originali:
        for p in pokemon_posseduti_originali:
            iv_str = "/".join(sorted(p.ivs)) if p.ivs else "Nessuna" # Assicura ordinamento per consistenza
            nat_str = p.natura if p.natura else "N/D"
            specie_str = f", Specie: {p.specie}" if p.specie else ""
            sesso_str = f", Sesso: {p.sesso}" if p.sesso else ""
            egg_groups_str = f", Gruppi Uova: {', '.join(p.egg_groups)}" if p.egg_groups else ""
            print(f"- {p.id_utente} (IVs: {iv_str}, Natura: {nat_str}{specie_str}{sesso_str}{egg_groups_str})")
            log_debug(f"- {p.id_utente} (IVs: {iv_str}, Natura: {nat_str}{specie_str}{sesso_str}{egg_groups_str})")
    else:
        print("Nessun Pokémon posseduto fornito.")
        log_debug("Nessun Pokémon posseduto fornito.")

    piani_da_analizzare: List[PianoCompletoF2] = []
    natura_target_globale_letta_dal_json = ""
    try:
        with open(file_piani_json, "r", encoding="utf-8") as f:
            piani_file_data = json.load(f)
            print(f"\nCaricamento piani da {file_piani_json}...")
            log_debug(f"\nCaricamento piani da {file_piani_json}...")
            natura_target_globale_letta_dal_json = piani_file_data.get("natura_target_specifica", "")
            if natura_target_globale_letta_dal_json:
                print(f"Natura Target Globale letta dal file piani: {natura_target_globale_letta_dal_json}")
                log_debug(f"Natura Target Globale letta dal file piani: {natura_target_globale_letta_dal_json}")
            else:
                print("Natura Target Globale non specificata nel file piani.")
                log_debug("Natura Target Globale non specificata nel file piani.")

            for piano_data in piani_file_data.get("piani", []):
                piano = PianoCompletoF2(
                    id_piano_fase1=piano_data.get("id_piano_fase1", 0),
                    legenda_usata=piano_data.get("legenda_usata", {}),
                    percorso_A=deserialize_percorso_def_f2(piano_data.get("percorso_A")),
                    percorso_B=deserialize_percorso_def_f2(piano_data.get("percorso_B")),
                    pokemon_target_finale_piano=deserialize_pokemon_def_f2(piano_data.get("pokemon_target_finale_piano")),
                    natura_target_specifica_del_piano_globale=natura_target_globale_letta_dal_json
                )
                piani_da_analizzare.append(piano)
        print(f"{len(piani_da_analizzare)} piani caricati.")
        log_debug(f"{len(piani_da_analizzare)} piani caricati.")
    except FileNotFoundError:
        print(f"Errore: Impossibile aprire il file dei piani: {file_piani_json}", file=sys.stderr)
        log_debug(f"Errore: Impossibile aprire il file dei piani: {file_piani_json}")
    except json.JSONDecodeError:
        print(f"Errore: Formato JSON non valido in {file_piani_json}", file=sys.stderr)
        log_debug(f"Errore: Formato JSON non valido in {file_piani_json}")

    piani_valutati: List[PianoCompletoF2] = []

    if not piani_da_analizzare:
        print("\nNessun piano da analizzare. Esecuzione terminata.")
        log_debug("\nNessun piano da analizzare. Esecuzione terminata.")

    for piano_idx, piano in enumerate(piani_da_analizzare):
        reset_soddisfazione_piano(piano)
        log_debug(f"\nValutazione Piano ID: {piano.id_piano_fase1}")
        if piano.natura_target_specifica_del_piano_globale:
            log_debug(f" (Natura Target per questo set di piani: {piano.natura_target_specifica_del_piano_globale})")
        legenda_str = ", ".join([f'{k}="{v}"' for k,v in piano.legenda_usata.items()])
        log_debug(f" Legenda Usata: {legenda_str}")

        id_pkmn_usati_in_questo_piano_set: Set[str] = set()
        piano.mappa_richiesto_a_posseduto.clear()
        piano.punteggio_ottenuto = 0.0
        piano.pokemon_matchati_count = 0

        percorsi_del_piano_corrente = []
        if piano.percorso_A.valido: percorsi_del_piano_corrente.append(piano.percorso_A)
        if piano.percorso_B.valido: percorsi_del_piano_corrente.append(piano.percorso_B)

        for percorso_attivo in percorsi_del_piano_corrente:
            log_debug(f" Analisi Percorso {percorso_attivo.tipo_percorso}")
            for livello in percorso_attivo.livelli:
                log_debug(f"  Livello {livello.livello_id}")
                for acc_idx, accoppiamento in enumerate(livello.accoppiamenti):
                    for gen_slot_idx, gen_attr_name in enumerate(["genitore1_richiesto", "genitore2_richiesto"]):
                        genitore_richiesto_ptr = getattr(accoppiamento, gen_attr_name)
                        if not genitore_richiesto_ptr.nome_formattato_dal_piano or genitore_richiesto_ptr.soddisfatto_da_posseduto:
                            continue
                        best_match_pokemon_info: Optional[PokemonPossedutoF2] = None
                        best_match_pokemon_carries_global_target_nat = False
                        for poss_candidate in pokemon_posseduti_originali:
                            if poss_candidate.id_utente in id_pkmn_usati_in_questo_piano_set:
                                continue
                            iv_match = ivs_match_fase2(poss_candidate.ivs, genitore_richiesto_ptr.ivs)
                            nat_match = natura_match_fase2(poss_candidate.natura, genitore_richiesto_ptr.natura, piano.natura_target_specifica_del_piano_globale)
                            if (genitore_richiesto_ptr.ivs or genitore_richiesto_ptr.natura):
                                log_debug(f"    DEBUG MATCHING ATTEMPT (Piano:{piano.id_piano_fase1}, Lvl:{livello.livello_id}, Acc:{acc_idx+1}, Gen:{gen_slot_idx+1}, Richiesto: {genitore_richiesto_ptr.nome_formattato_dal_piano}) vs Posseduto: {poss_candidate.id_utente} -> IVMatch:{'T' if iv_match else 'F'}, NatMatch:{'T' if nat_match else 'F'}")
                            if iv_match and nat_match:
                                candidate_carries_global_target_nat = bool(piano.natura_target_specifica_del_piano_globale and poss_candidate.natura == piano.natura_target_specifica_del_piano_globale)
                                if best_match_pokemon_info is None:
                                    best_match_pokemon_info = poss_candidate
                                    best_match_pokemon_carries_global_target_nat = candidate_carries_global_target_nat
                                else:
                                    slot_req_nat_trim = genitore_richiesto_ptr.natura.strip() if genitore_richiesto_ptr.natura else ""
                                    slot_is_nature_flexible = (not slot_req_nat_trim or slot_req_nat_trim.lower() == "null" or slot_req_nat_trim == '""')
                                    if slot_is_nature_flexible:
                                        if candidate_carries_global_target_nat and not best_match_pokemon_carries_global_target_nat:
                                            best_match_pokemon_info = poss_candidate
                                            best_match_pokemon_carries_global_target_nat = True
                        if best_match_pokemon_info:
                            id_pkmn_usati_in_questo_piano_set.add(best_match_pokemon_info.id_utente)
                            genitore_richiesto_ptr.soddisfatto_da_posseduto = True
                            genitore_richiesto_ptr.soddisfatto_da_id_utente = best_match_pokemon_info.id_utente
                            piano.mappa_richiesto_a_posseduto[genitore_richiesto_ptr.nome_formattato_dal_piano] = best_match_pokemon_info.id_utente
                            piano.punteggio_ottenuto += calcola_punteggio_pokemon_fase2(genitore_richiesto_ptr)
                            piano.pokemon_matchati_count += 1
                            log_debug(f"  MATCH FINALE SELEZIONATO: {genitore_richiesto_ptr.nome_formattato_dal_piano} con {best_match_pokemon_info.id_utente}")
                        elif genitore_richiesto_ptr.nome_formattato_dal_piano and (genitore_richiesto_ptr.ivs or genitore_richiesto_ptr.natura):
                            log_debug(f"  NON TROVATO match per Richiesto: {genitore_richiesto_ptr.nome_formattato_dal_piano}")

        piano.id_pokemon_posseduti_usati_unici = id_pkmn_usati_in_questo_piano_set
        piani_valutati.append(piano)
        log_debug(f"Piano ID: {piano.id_piano_fase1} - Punteggio Finale: {piano.punteggio_ottenuto} (#Match: {piano.pokemon_matchati_count}, #PossedutiUnici: {len(piano.id_pokemon_posseduti_usati_unici)})")
        if piano.id_pokemon_posseduti_usati_unici:
            log_debug(f"  Pokemon posseduti (unici) usati: {', '.join(sorted(list(piano.id_pokemon_posseduti_usati_unici)))}")


    # MODIFICA: Identifica TUTTI i piani che sono "migliori" a pari merito
    piani_candidati_per_fase3: List[PianoCompletoF2] = []
    if piani_valutati:
        max_punteggio = -1.0
        max_match_count = -1
        max_posseduti_usati = -1 # Ora cerchiamo il massimo numero di posseduti usati

        # Primo passaggio per trovare i valori massimi
        for p_val in piani_valutati: # Rinomino la variabile per evitare shadowing
            if p_val.punteggio_ottenuto > max_punteggio:
                max_punteggio = p_val.punteggio_ottenuto
                max_match_count = p_val.pokemon_matchati_count
                max_posseduti_usati = len(p_val.id_pokemon_posseduti_usati_unici)
            elif p_val.punteggio_ottenuto == max_punteggio:
                if p_val.pokemon_matchati_count > max_match_count:
                    max_match_count = p_val.pokemon_matchati_count
                    max_posseduti_usati = len(p_val.id_pokemon_posseduti_usati_unici)
                elif p_val.pokemon_matchati_count == max_match_count:
                    if len(p_val.id_pokemon_posseduti_usati_unici) > max_posseduti_usati:
                        max_posseduti_usati = len(p_val.id_pokemon_posseduti_usati_unici)

        # Secondo passaggio per raccogliere tutti i piani che raggiungono questi massimi
        for p_val in piani_valutati:
            if p_val.punteggio_ottenuto == max_punteggio and \
               p_val.pokemon_matchati_count == max_match_count and \
               len(p_val.id_pokemon_posseduti_usati_unici) == max_posseduti_usati:
                # Calcola i Pokémon base necessari per questo piano candidato
                p_val.pokemon_base_necessari_calcolati = dict(calcola_pokemon_base_necessari_f2(p_val, log_debug))
                piani_candidati_per_fase3.append(p_val)

        if piani_candidati_per_fase3:
            # Stampa solo il primo dei candidati come "miglior piano" per la console
            # La Fase 3 poi analizzerà tutti i candidati
            miglior_piano_console = piani_candidati_per_fase3[0]
            print(f"\n{GREEN_BOLD_TERMINAL}--- Miglior Piano Trovato (tra {len(piani_candidati_per_fase3)} candidati) ---{RESET_TERMINAL}")
            log_debug(f"\n--- Miglior Piano Trovato (tra {len(piani_candidati_per_fase3)} candidati) ---")
            print(f"ID Piano (da Fase 1): {miglior_piano_console.id_piano_fase1}")
            log_debug(f"ID Piano (da Fase 1): {miglior_piano_console.id_piano_fase1}")
            # ... (resto della stampa dettagliata per miglior_piano_console, come nella versione precedente) ...
            if miglior_piano_console.natura_target_specifica_del_piano_globale:
                print(f"Natura Target del Set di Piani: {miglior_piano_console.natura_target_specifica_del_piano_globale}")
                log_debug(f"Natura Target del Set di Piani: {miglior_piano_console.natura_target_specifica_del_piano_globale}")
            legenda_out_str = ", ".join([f'{k}="{v}"' for k,v in miglior_piano_console.legenda_usata.items()])
            print(f"Legenda Usata: {legenda_out_str}")
            log_debug(f"Legenda Usata: {legenda_out_str}")
            print(f"Punteggio Totale Ottenuto: {YELLOW_BOLD_TERMINAL}{miglior_piano_console.punteggio_ottenuto}{RESET_TERMINAL}")
            log_debug(f"Punteggio Totale Ottenuto: {miglior_piano_console.punteggio_ottenuto}")
            print(f"Numero di Pokémon Richiesti Soddisfatti da Posseduti: {miglior_piano_console.pokemon_matchati_count}")
            log_debug(f"Numero di Pokémon Richiesti Soddisfatti da Posseduti: {miglior_piano_console.pokemon_matchati_count}")
            num_posseduti_unici_miglior_piano = len(miglior_piano_console.id_pokemon_posseduti_usati_unici)
            print(f"Numero di Pokémon Posseduti Unici Utilizzati: {num_posseduti_unici_miglior_piano}")
            log_debug(f"Numero di Pokémon Posseduti Unici Utilizzati: {num_posseduti_unici_miglior_piano}")
            if miglior_piano_console.id_pokemon_posseduti_usati_unici:
                usati_out_str_list = [f"{YELLOW_BOLD_TERMINAL}{pid}{RESET_TERMINAL}" for pid in sorted(list(miglior_piano_console.id_pokemon_posseduti_usati_unici))]
                print(f"Pokemon Posseduti Utilizzati: {', '.join(usati_out_str_list)}")
                log_debug(f"Pokemon Posseduti Utilizzati: {', '.join(sorted(list(miglior_piano_console.id_pokemon_posseduti_usati_unici)))}")

            print("\nDettagli del Target Finale del Piano:")
            log_debug("\nDettagli del Target Finale del Piano:")
            miglior_piano_console.pokemon_target_finale_piano.print_pokemon(stream=sys.stdout, show_match_details=False)
            log_debug(f"  {miglior_piano_console.pokemon_target_finale_piano.log_str()}")

            print("\n--- Dettagli Accoppiamenti del Miglior Piano (Pokémon richiesti) ---")
            log_debug("\n--- Dettagli Accoppiamenti del Miglior Piano (Pokémon richiesti) ---")
            for percorso_key in ["percorso_A", "percorso_B"]:
                percorso = getattr(miglior_piano_console, percorso_key)
                if percorso.valido:
                    print(f" Percorso {percorso.tipo_percorso}:")
                    log_debug(f" Percorso {percorso.tipo_percorso}:")
                    for livello in percorso.livelli:
                        print(f"  Livello {livello.livello_id}:")
                        log_debug(f"  Livello {livello.livello_id}:")
                        for acc_idx, acc in enumerate(livello.accoppiamenti):
                            print(f"   Accoppiamento #{acc_idx + 1}:")
                            log_debug(f"   Accoppiamento #{acc_idx + 1}:")
                            if acc.genitore1_richiesto.nome_formattato_dal_piano:
                                acc.genitore1_richiesto.print_pokemon(indent="    G1 Richiesto: ", stream=sys.stdout)
                                log_debug(f"    G1 Richiesto: {acc.genitore1_richiesto.log_str()}")
                            if acc.genitore2_richiesto.nome_formattato_dal_piano:
                                acc.genitore2_richiesto.print_pokemon(indent="    G2 Richiesto: ", stream=sys.stdout)
                                log_debug(f"    G2 Richiesto: {acc.genitore2_richiesto.log_str()}")
                            if acc.figlio_generato.nome_formattato_dal_piano:
                                 print(f"    Figlio Generato: \"{acc.figlio_generato.nome_formattato_dal_piano}\"")
                                 log_debug(f"    Figlio Generato: \"{acc.figlio_generato.nome_formattato_dal_piano}\"")

            print("\n--- Riepilogo Pokémon Base Teorici Necessari per le Parti NON COPERTE di Questo Piano ---")
            log_debug("\n--- Riepilogo Pokémon Base Teorici Necessari per le Parti NON COPERTE di Questo Piano ---")
            if miglior_piano_console.pokemon_base_necessari_calcolati:
                for base_pkmn_desc, count in sorted(miglior_piano_console.pokemon_base_necessari_calcolati.items()):
                    print(f"  - {base_pkmn_desc}: {count}x")
                    log_debug(f"  - {base_pkmn_desc}: {count}x")
            else:
                 print("  Tutti i componenti del piano sembrano essere coperti da Pokémon posseduti o non richiedono ulteriori Pokémon base.")
                 log_debug("  Tutti i componenti del piano sembrano essere coperti da Pokémon posseduti o non richiedono ulteriori Pokémon base.")

            # Esporta TUTTI i piani candidati per la Fase 3
            output_data_fase3_list = [p.to_dict_per_fase3() for p in piani_candidati_per_fase3]
            try:
                with open(file_output_fase3, "w", encoding="utf-8") as f_out_f3:
                    json.dump(output_data_fase3_list, f_out_f3, indent=2)
                print(f"\nDati dei {len(piani_candidati_per_fase3)} piani candidati esportati in '{file_output_fase3}' per la Fase 3.")
                log_debug(f"Dati dei {len(piani_candidati_per_fase3)} piani candidati esportati in '{file_output_fase3}' per la Fase 3.")
            except IOError:
                print(f"Errore: Impossibile scrivere il file di output per la Fase 3: {file_output_fase3}", file=sys.stderr)
                log_debug(f"Errore: Impossibile scrivere il file di output per la Fase 3: {file_output_fase3}")
        else:
            print("\nNessun piano candidato trovato dopo la valutazione.")
            log_debug("\nNessun piano candidato trovato dopo la valutazione.")
    else:
        print("\nNessun piano valutato disponibile.")
        log_debug("\nNessun piano valutato disponibile.")

    log_debug("--- Fine Log di Debug Fase 2 ---")
    try:
        with open(file_debug_log, "w", encoding="utf-8") as f_log:
            for line in debug_log_lines:
                f_log.write(line + "\n")
        print(f"\nLog di debug scritto su {file_debug_log}")
    except IOError:
        print(f"Errore: Impossibile scrivere il file di log di debug: {file_debug_log}", file=sys.stderr)


# --- Logica Principale di Esecuzione (Aggiornata per passare il nome del file di output Fase 3) ---
if __name__ == "__main__":
    # --- Configurazione Fase 1 (Stress Test Scenario 1) ---
    config_fase1 = {
        "modalita_op_base": "5IV",
        "con_natura_obiettivo": True,
        "natura_obiettivo_spec": "Decisa", # This is Adamant
        "stats_target_config": ["PS", "ATT", "DEF", "SP.DEF", "Velocità"]
    }

    print("--- Esecuzione Fase 1: Generazione Piani ---")
    run_fase1(
        modalita_op_base=config_fase1["modalita_op_base"],
        con_natura_obiettivo=config_fase1["con_natura_obiettivo"],
        natura_obiettivo_spec=config_fase1["natura_obiettivo_spec"],
        stats_target_config=config_fase1["stats_target_config"]
    )
    print("--- Fine Fase 1 ---\n")

    # --- Configurazione Fase 2 ---
    file_piani_json_input = "piani_dati.json"
    # file_pokemon_posseduti_input = "pokemon_posseduti.json" # Questo file non è più usato come input diretto
    file_debug_log_output = "fase2_debug_log.txt"
    file_output_per_fase3 = "fase2_output_per_fase3.json"

    print("--- Esecuzione Fase 2: Valutazione Piani ---")

    # Creazione della lista di Pokémon posseduti campione come da istruzioni
    sample_owned_pokemon = [
        PokemonPossedutoF2(id_utente="Ditto1", ivs=["PS", "ATT"], natura="Decisa", specie="Ditto", sesso=None, egg_groups=["Ditto"]),
        PokemonPossedutoF2(id_utente="Pika1", ivs=["SP.ATT", "Velocità"], natura="Modesta", specie="Pikachu", sesso="M", egg_groups=["Campo", "Folletto"])
    ]

    # Non è più necessario creare/scrivere un file pokemon_posseduti.json fittizio
    # i dati dei Pokémon posseduti vengono passati direttamente come lista.

    if os.path.exists(file_piani_json_input):
         # Chiamata a run_fase2 aggiornata per passare la lista sample_owned_pokemon
         run_fase2(file_piani_json_input, sample_owned_pokemon, file_debug_log_output, file_output_per_fase3)
    else:
        print(f"File dei piani '{file_piani_json_input}' non trovato. Assicurarsi che la Fase 1 sia stata eseguita correttamente.")

    print("--- Fine Fase 2 ---")
