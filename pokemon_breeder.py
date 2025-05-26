# pokemon_breeder.py
import json
from typing import List, Dict, Optional, Set, Tuple, Any
import functools  # Non utilizzato direttamente, ma potrebbe servire per future ottimizzazioni con cache
import heapq  # Non utilizzato direttamente, ma utile per algoritmi di ricerca come A*
from itertools import combinations
import os
import time  # Per timestamp nel log di debug

DEBUG_RECURSIVE_PLANNER = True
DEBUG_FILE_NAME = "debug.txt"


def clear_debug_log_once_for_suite():
    """
    Pulisce il file di debug una volta all'inizio di una suite di test.
    Questa funzione dovrebbe essere chiamata solo una volta prima di eseguire run_complex_test.
    """
    try:
        with open(DEBUG_FILE_NAME, 'w', encoding='utf-8') as f:
            f.write(f"--- Inizio Nuovo Log di Debug Suite ({time.strftime('%Y-%m-%d %H:%M:%S')}) ---\n")
    except IOError:
        print(f"Attenzione: Impossibile pulire il file di debug {DEBUG_FILE_NAME}")


def d_print(*args, **kwargs):
    """Scrive i messaggi di debug in modalità append su un file chiamato debug.txt."""
    if not DEBUG_RECURSIVE_PLANNER:
        return
    try:
        with open(DEBUG_FILE_NAME, 'a', encoding='utf-8') as f:
            print(*args, **kwargs, file=f)
    except IOError:
        # Fallback alla console se la scrittura su file fallisce
        print("Errore: Impossibile scrivere sul file di debug. Messaggio originale:")
        print(*args, **kwargs)


def load_pokemon_data(filename="pokemon_data.json") -> Dict[str, List[str]]:
    """Carica i dati dei Pokémon (gruppi uova) da un file JSON."""
    try:
        with open(filename, 'r', encoding='utf-8') as f:
            data = json.load(f)
            # Converte i nomi delle specie in minuscolo per una ricerca case-insensitive
            return {k.lower(): v for k, v in data.items()}
    except (FileNotFoundError, json.JSONDecodeError):
        d_print(f"Errore: File {filename} non trovato o formato JSON non valido.")
        return {}


POKEMON_EGG_GROUPS_RAW = load_pokemon_data()
ALL_POKEMON_NAMES = sorted([name.capitalize() for name in POKEMON_EGG_GROUPS_RAW.keys()])

IV_STATS = ["PS", "ATK", "DEF", "SPA", "SPD", "SPE"]
VIGOR_ITEMS_MAP = {
    "PS": "VigorPeso", "ATK": "VigorCerchio", "DEF": "VigorFascia",
    "SPA": "VigorLente", "SPD": "VigorBanda", "SPE": "Vigorgliera",
}
REVERSE_VIGOR_ITEMS_MAP = {v: k for k, v in VIGOR_ITEMS_MAP.items()}
EVERSTONE = "Pietrastante"
ALL_NATURES = sorted([
    "Adamant", "Bashful", "Bold", "Brave", "Calm", "Careful", "Docile",
    "Gentle", "Hardy", "Hasty", "Impish", "Jolly", "Lax", "Lonely",
    "Mild", "Modest", "Naive", "Naughty", "Quiet", "Quirky", "Rash",
    "Relaxed", "Sassy", "Serious", "Timid"
])


class Pokemon:
    """Rappresenta un singolo Pokémon con le sue caratteristiche rilevanti per il breeding."""
    _id_counter = 0  # Contatore statico per assegnare ID univoci ai Pokémon generati

    def __init__(self, species: str, ivs: Set[str], nature: str, gender: str,
                 name: Optional[str] = None, is_owned: bool = False,
                 source_info: str = "N/A", internal_id: Optional[int] = None):
        self.species = species.capitalize()  # Standardizza la prima lettera maiuscola
        self.name = name if name else self.species
        self.ivs = set(ivs)  # Assicura che sia un set
        self.nature = nature
        self.gender = gender
        self.is_owned = is_owned  # True se il Pokémon è posseduto dall'utente inizialmente
        self.egg_groups = POKEMON_EGG_GROUPS_RAW.get(self.species.lower(), [])

        if internal_id is not None:  # Permette di specificare un ID (es. per Pokémon posseduti)
            self.id = internal_id
        else:  # Altrimenti, assegna un nuovo ID
            self.id = Pokemon._id_counter
            Pokemon._id_counter += 1

        self.source_info = source_info  # Stringa per tracciare l'origine del Pokémon nel piano
        self.cost_to_produce = 0.0  # Costo (in acquisti) per produrre questo Pokémon

    def __repr__(self):
        iv_str = ", ".join(sorted(list(self.ivs))) if self.ivs else "Nessuno"
        cost_str = f"CostoProd:{self.cost_to_produce:.1f}" if not self.is_owned else "Posseduto"
        return (f"{self.name} ({self.species}, {self.gender}) | N: {self.nature}, "
                f"IVs: [{iv_str}] | ID: {self.id} ({cost_str}) | Fonte: {self.source_info}")

    def get_display_string(self):  # Usato dalla GUI
        iv_str = f"IVs: {', '.join(sorted(list(self.ivs)))}" if self.ivs else "Nessun IV 31"
        nature_str = f"Natura: {self.nature}" if self.nature != "NEUTRAL" else "Natura non specificata"
        return f"{self.name} ({self.species}, {self.gender}) - {nature_str}, {iv_str}"


class BreedingStepDetailed:
    """Rappresenta un singolo passo di accoppiamento nel piano di breeding."""

    def __init__(self, child_pokemon: Pokemon,
                 parent1_pokemon: Pokemon, parent1_item: Optional[str],
                 parent2_pokemon: Pokemon, parent2_item: Optional[str],
                 step_number: int = 0):
        self.child = child_pokemon
        self.parent1 = parent1_pokemon
        self.parent1_item = parent1_item
        self.parent2 = parent2_pokemon
        self.parent2_item = parent2_item
        self.step_number = step_number  # Numero progressivo del passo nel piano

    def __str__(self):
        child_ivs_str = str(set(self.child.ivs)) if self.child.ivs else "{}"
        p1_ivs_str = str(set(self.parent1.ivs)) if self.parent1.ivs else "{}"
        p2_ivs_str = str(set(self.parent2.ivs)) if self.parent2.ivs else "{}"
        return (f"--- PASSO {self.step_number} ---\n"
                f"  Figlio Generato: {self.child.name} ({self.child.species}, {self.child.gender}) N:{self.child.nature}, IVs:{child_ivs_str} (Fonte: {self.child.source_info})\n"
                f"  Genitore 1: {self.parent1.name} ({self.parent1.species}, {self.parent1.gender}) [{self.parent1_item if self.parent1_item else 'Nessun Oggetto'}]\n"
                f"    (N:{self.parent1.nature}, IVs:{p1_ivs_str}, ID:{self.parent1.id}, Fonte:{self.parent1.source_info})\n"
                f"  Genitore 2: {self.parent2.name} ({self.parent2.species}, {self.parent2.gender}) [{self.parent2_item if self.parent2_item else 'Nessun Oggetto'}]\n"
                f"    (N:{self.parent2.nature}, IVs:{p2_ivs_str}, ID:{self.parent2.id}, Fonte:{self.parent2.source_info})\n")


class BreedingNode:
    """Rappresenta un Pokémon target da ottenere (uno stato nella ricerca)."""

    def __init__(self, species: str, ivs: Set[str], nature: str, **kwargs):
        self.species = species.capitalize()
        self.ivs = frozenset(ivs)  # Immutabile, per uso come chiave in dizionari/set
        self.nature = nature

    def get_state_tuple(self) -> Tuple[str, frozenset, str]:
        """Restituisce una tupla che rappresenta univocamente lo stato del Pokémon."""
        return (self.species, self.ivs, self.nature)


def generate_breeding_options_for_child(child_node_state: BreedingNode) -> List[Dict[str, Any]]:
    """
    Genera le possibili combinazioni di genitori (specifiche) e oggetti per produrre il child_node_state.
    Questa funzione è cruciale e deve riflettere accuratamente le regole di breeding
    per garantire la trasmissione degli IV e della natura.
    """
    options: List[Dict[str, Any]] = []
    child_s, child_i_set, child_n = child_node_state.species, set(child_node_state.ivs), child_node_state.nature

    is_child_buyable_base = (not child_i_set and child_n == "NEUTRAL") or \
                            (len(child_i_set) == 1 and child_n == "NEUTRAL") or \
                            (not child_i_set and child_n != "NEUTRAL")
    if is_child_buyable_base:
        return []

    if child_n != "NEUTRAL":
        if child_i_set:
            for iv_vigor_p2 in child_i_set:
                item_p2 = VIGOR_ITEMS_MAP.get(iv_vigor_p2)
                if not item_p2: continue

                p1_ivs_spec = child_i_set - {iv_vigor_p2}
                p1_spec = {'species': child_s, 'ivs': p1_ivs_spec, 'nature': child_n}

                p2_ivs_spec_for_option1 = set(child_i_set)

                p2_spec_non_ditto = {'species': child_s, 'ivs': p2_ivs_spec_for_option1, 'nature': "NEUTRAL"}
                options.append(
                    {'type': 'bred', 'p1_spec': p1_spec, 'p2_spec': p2_spec_non_ditto, 'item1': EVERSTONE,
                     'item2': item_p2})

                if child_s.lower() != 'ditto' and p1_spec['species'].lower() != 'ditto':
                    p2_spec_ditto = {'species': 'Ditto', 'ivs': p2_ivs_spec_for_option1, 'nature': "NEUTRAL"}
                    options.append(
                        {'type': 'bred', 'p1_spec': p1_spec, 'p2_spec': p2_spec_ditto, 'item1': EVERSTONE,
                         'item2': item_p2})

        if not child_i_set:
            p1_spec_no_iv = {'species': child_s, 'ivs': set(), 'nature': child_n}
            p2_spec_non_ditto_no_iv = {'species': child_s, 'ivs': set(), 'nature': "NEUTRAL"}
            options.append(
                {'type': 'bred', 'p1_spec': p1_spec_no_iv, 'p2_spec': p2_spec_non_ditto_no_iv, 'item1': EVERSTONE,
                 'item2': None})

            if child_s.lower() != 'ditto' and p1_spec_no_iv['species'].lower() != 'ditto':
                p2_spec_ditto_no_iv = {'species': 'Ditto', 'ivs': set(), 'nature': "NEUTRAL"}
                options.append(
                    {'type': 'bred', 'p1_spec': p1_spec_no_iv, 'p2_spec': p2_spec_ditto_no_iv, 'item1': EVERSTONE,
                     'item2': None})

    if child_i_set:
        for iv_vigor_p1 in child_i_set:
            item_p1 = VIGOR_ITEMS_MAP.get(iv_vigor_p1)
            if not item_p1: continue

            p1_ivs_spec_for_option2 = set(child_i_set)
            p1_spec_op2 = {'species': child_s, 'ivs': p1_ivs_spec_for_option2, 'nature': "NEUTRAL"}

            p2_nature_spec = child_n if child_n != "NEUTRAL" else "NEUTRAL"
            item_p2_op2 = EVERSTONE if child_n != "NEUTRAL" else None
            p2_spec_op2_corrected = {'species': child_s, 'ivs': set(child_i_set), 'nature': p2_nature_spec}

            options.append({'type': 'bred', 'p1_spec': p1_spec_op2,
                            'p2_spec': p2_spec_op2_corrected,
                            'item1': item_p1, 'item2': item_p2_op2})

            if child_s.lower() != 'ditto':
                if p2_spec_op2_corrected['species'].lower() != 'ditto':
                    ditto_p1_spec = {'species': 'Ditto', 'ivs': p1_ivs_spec_for_option2, 'nature': 'NEUTRAL'}
                    options.append({'type': 'bred', 'p1_spec': ditto_p1_spec, 'p2_spec': p2_spec_op2_corrected,
                                    'item1': item_p1, 'item2': item_p2_op2})

                if p1_spec_op2['species'].lower() != 'ditto':
                    ditto_p2_spec = {'species': 'Ditto', 'ivs': set(child_i_set), 'nature': p2_nature_spec}
                    options.append({'type': 'bred', 'p1_spec': p1_spec_op2, 'p2_spec': ditto_p2_spec,
                                    'item1': item_p1, 'item2': item_p2_op2})

    if child_n == "NEUTRAL" and len(child_i_set) >= 2:
        for iv_p1_vigor, iv_p2_vigor in combinations(child_i_set, 2):
            item_p1_for_3 = VIGOR_ITEMS_MAP.get(iv_p1_vigor)
            item_p2_for_3 = VIGOR_ITEMS_MAP.get(iv_p2_vigor)
            if not item_p1_for_3 or not item_p2_for_3: continue

            shared_ivs_op3 = child_i_set - {iv_p1_vigor, iv_p2_vigor}

            p1_ivs_op3 = {iv_p1_vigor}.union(shared_ivs_op3)
            p1_spec_op3 = {'species': child_s, 'ivs': p1_ivs_op3, 'nature': "NEUTRAL"}

            p2_ivs_op3 = {iv_p2_vigor}.union(shared_ivs_op3)
            p2_spec_op3 = {'species': child_s, 'ivs': p2_ivs_op3, 'nature': "NEUTRAL"}

            options.append({'type': 'bred', 'p1_spec': p1_spec_op3, 'p2_spec': p2_spec_op3, 'item1': item_p1_for_3,
                            'item2': item_p2_for_3})

            if child_s.lower() != 'ditto':
                if p2_spec_op3['species'].lower() != 'ditto':
                    p1_spec_op3_ditto = {'species': 'Ditto', 'ivs': p1_ivs_op3, 'nature': "NEUTRAL"}
                    options.append(
                        {'type': 'bred', 'p1_spec': p1_spec_op3_ditto, 'p2_spec': p2_spec_op3, 'item1': item_p1_for_3,
                         'item2': item_p2_for_3})
                if p1_spec_op3['species'].lower() != 'ditto':
                    p2_spec_op3_ditto = {'species': 'Ditto', 'ivs': p2_ivs_op3, 'nature': "NEUTRAL"}
                    options.append(
                        {'type': 'bred', 'p1_spec': p1_spec_op3, 'p2_spec': p2_spec_op3_ditto, 'item1': item_p1_for_3,
                         'item2': item_p2_for_3})

    final_options, seen_options_tuples = [], set()
    for opt_idx, opt in enumerate(options):
        p1_s, p1_i, p1_n = opt['p1_spec']['species'], frozenset(opt['p1_spec']['ivs']), opt['p1_spec']['nature']
        p2_s, p2_i, p2_n = opt['p2_spec']['species'], frozenset(opt['p2_spec']['ivs']), opt['p2_spec']['nature']
        it1, it2 = opt['item1'], opt['item2']

        if p1_s.lower() == 'ditto' and p2_s.lower() == 'ditto':
            continue

        if it1 == EVERSTONE and it2 == EVERSTONE:
            continue
        if it1 and it1 in REVERSE_VIGOR_ITEMS_MAP and \
                it2 and it2 in REVERSE_VIGOR_ITEMS_MAP and it1 == it2:
            continue

        # CORREZIONE TypeError: Sostituisci None con "" per l'ordinamento degli item
        item1_sort_val = it1 if it1 is not None else ""
        item2_sort_val = it2 if it2 is not None else ""

        parents_tuple_part1 = (p1_s, tuple(sorted(list(p1_i))), p1_n, item1_sort_val)
        parents_tuple_part2 = (p2_s, tuple(sorted(list(p2_i))), p2_n, item2_sort_val)

        try:
            sorted_parents_tuple = tuple(sorted((parents_tuple_part1, parents_tuple_part2)))
        except TypeError as e:
            d_print(f"Errore durante l'ordinamento delle tuple dei genitori: {e}")
            d_print(f"  Tuple Part 1: {parents_tuple_part1}")
            d_print(f"  Tuple Part 2: {parents_tuple_part2}")
            continue  # Salta questa opzione se l'ordinamento fallisce ancora per qualche motivo

        if sorted_parents_tuple not in seen_options_tuples:
            final_options.append(opt)
            seen_options_tuples.add(sorted_parents_tuple)

    return final_options


memo_get_pokemon = {}
MAX_RECURSION_DEPTH = 30


def get_pokemon_with_minimal_cost(
        target_species: str,
        target_ivs: Set[str],
        target_nature: str,
        owned_pokemon_map: Dict[int, Pokemon],
        consumed_owned_ids: frozenset[int],
        depth: int = 0
) -> Tuple[Optional[Pokemon], List[BreedingStepDetailed], float, frozenset[int]]:
    global memo_get_pokemon

    target_species_cap = target_species.capitalize()
    target_ivs_fs = frozenset(target_ivs)
    current_target_tuple_for_loop_check = (target_species_cap, target_ivs_fs, target_nature)

    memo_key = (target_species_cap, target_ivs_fs, target_nature, consumed_owned_ids)

    if memo_key in memo_get_pokemon:
        cached_pkm_template, cached_steps, cached_cost, cached_consumed = memo_get_pokemon[memo_key]
        cloned_pkm = None
        if cached_pkm_template:
            cloned_pkm = Pokemon(cached_pkm_template.species, cached_pkm_template.ivs, cached_pkm_template.nature,
                                 cached_pkm_template.gender,
                                 name=cached_pkm_template.name,
                                 is_owned=cached_pkm_template.is_owned,
                                 source_info=cached_pkm_template.source_info,
                                 internal_id=cached_pkm_template.id if cached_pkm_template.is_owned else None)
            if not cloned_pkm.is_owned:
                cloned_pkm.id = Pokemon._id_counter
                Pokemon._id_counter += 1
            cloned_pkm.cost_to_produce = cached_pkm_template.cost_to_produce

        d_print(
            f"{'  ' * depth}CACHE HIT for: {target_species_cap} {target_ivs_fs} {target_nature} (Consumed: {list(consumed_owned_ids)}) -> Cost: {cached_cost}, PkmID: {cloned_pkm.id if cloned_pkm else 'None'}")
        return cloned_pkm, list(cached_steps), cached_cost, cached_consumed

    if depth > MAX_RECURSION_DEPTH:
        d_print(
            f"{'  ' * depth}MAX DEPTH {MAX_RECURSION_DEPTH} reached for: {target_species_cap} {target_ivs_fs} {target_nature}")
        memo_get_pokemon[memo_key] = (None, [], float('inf'), consumed_owned_ids)
        return None, [], float('inf'), consumed_owned_ids

    d_print(
        f"{'  ' * depth}GETTING: {target_species_cap} IVs:{target_ivs_fs} N:{target_nature} (Consumed: {list(consumed_owned_ids)}) Depth: {depth}")

    best_owned_candidate: Optional[Pokemon] = None
    best_candidate_score = -float('inf')

    for p_id, owned_p in owned_pokemon_map.items():
        if p_id not in consumed_owned_ids:
            current_p_score = 0.0
            species_compatible_for_role = False

            if target_species_cap.lower() == "ditto":
                if owned_p.species.lower() == "ditto":
                    species_compatible_for_role = True;
                    current_p_score += 200
            elif owned_p.species.lower() == target_species_cap.lower():
                species_compatible_for_role = True;
                current_p_score += 100

            if species_compatible_for_role:
                if not target_ivs_fs.issubset(owned_p.ivs):
                    d_print(
                        f"{'  ' * (depth + 1)}[IV-CHECK] SKIPPING Owned Pkm ID {owned_p.id} ({owned_p.name}) for target '{target_species_cap} IVs:{target_ivs_fs} N:{target_nature}' | Needed IVs: {sorted(list(target_ivs_fs))} | Has IVs: {sorted(list(owned_p.ivs))}")
                    continue
                d_print(
                    f"{'  ' * (depth + 1)}[IV-CHECK] PASSED Owned Pkm ID {owned_p.id} ({owned_p.name}) for target '{target_species_cap} IVs:{target_ivs_fs} N:{target_nature}' | Needed IVs: {sorted(list(target_ivs_fs))} | Has IVs: {sorted(list(owned_p.ivs))}")

                matching_iv_count = len(target_ivs_fs.intersection(owned_p.ivs))
                current_p_score += matching_iv_count * 10

                if target_nature == "NEUTRAL":
                    current_p_score += 5
                elif owned_p.nature == target_nature:
                    current_p_score += 30
                else:
                    continue

                current_p_score -= len(owned_p.ivs) * 0.1

                if current_p_score > best_candidate_score:
                    best_candidate_score = current_p_score
                    best_owned_candidate = owned_p

    if best_owned_candidate:
        d_print(
            f"{'  ' * depth}  FOUND OWNED (Best): {best_owned_candidate} (ID: {best_owned_candidate.id}, Score: {best_candidate_score:.2f}) for {target_species_cap} {target_ivs_fs} {target_nature}")
        new_consumed_ids = consumed_owned_ids.union({best_owned_candidate.id})

        final_owned_pkm = Pokemon(best_owned_candidate.species, best_owned_candidate.ivs, best_owned_candidate.nature,
                                  best_owned_candidate.gender,
                                  name=best_owned_candidate.name,
                                  is_owned=True,
                                  source_info=f"Posseduto (Nome: {best_owned_candidate.name}, ID:{best_owned_candidate.id})",
                                  internal_id=best_owned_candidate.id)
        final_owned_pkm.cost_to_produce = 0.0

        memo_get_pokemon[memo_key] = (final_owned_pkm, [], 0.0, new_consumed_ids)
        return final_owned_pkm, [], 0.0, new_consumed_ids

    is_buyable_base = (not target_ivs_fs and target_nature == "NEUTRAL") or \
                      (len(target_ivs_fs) == 1 and target_nature == "NEUTRAL") or \
                      (not target_ivs_fs and target_nature != "NEUTRAL")

    if is_buyable_base:
        ivs_str_info = ",".join(sorted(list(target_ivs_fs))) if target_ivs_fs else "0IV"
        nature_str_info = target_nature if target_nature != "NEUTRAL" else "Ntrl"

        bought_pokemon = Pokemon(species=target_species_cap,
                                 ivs=set(target_ivs_fs),
                                 nature=target_nature,
                                 gender="Acquistato",
                                 name=f"Acq_{target_species_cap[:3]}",
                                 source_info=f"Acquistato Base ({ivs_str_info},{nature_str_info}, ID:temp)")
        bought_pokemon.cost_to_produce = 1.0
        bought_pokemon.source_info = f"Acquistato Base ({ivs_str_info},{nature_str_info}, ID:{bought_pokemon.id})"
        d_print(f"{'  ' * depth}  BUYING BASE: {bought_pokemon}")

        memo_get_pokemon[memo_key] = (bought_pokemon, [], 1.0, consumed_owned_ids)
        return bought_pokemon, [], 1.0, consumed_owned_ids

    current_request_node = BreedingNode(species=target_species_cap, ivs=set(target_ivs_fs), nature=target_nature)
    possible_parent_options = generate_breeding_options_for_child(current_request_node)

    if not possible_parent_options:
        d_print(
            f"{'  ' * depth}  NO BREEDING OPTIONS generated for {target_species_cap} {target_ivs_fs} {target_nature}")
        memo_get_pokemon[memo_key] = (None, [], float('inf'), consumed_owned_ids)
        return None, [], float('inf'), consumed_owned_ids

    best_overall_child_obj: Optional[Pokemon] = None
    min_overall_cost = float('inf')
    best_overall_steps: List[BreedingStepDetailed] = []
    best_overall_consumed_ids = consumed_owned_ids

    def option_complexity_sort_key(opt):
        c = len(opt['p1_spec']['ivs']) + len(opt['p2_spec']['ivs'])
        if opt['p1_spec']['nature'] != "NEUTRAL": c += 1
        if opt['p2_spec']['nature'] != "NEUTRAL": c += 1
        if opt['p1_spec']['species'].lower() == 'ditto' or opt['p2_spec']['species'].lower() == 'ditto':
            c -= 0.5

        p1_tuple_check = (opt['p1_spec']['species'].capitalize(), frozenset(opt['p1_spec']['ivs']),
                          opt['p1_spec']['nature'])
        p2_tuple_check = (opt['p2_spec']['species'].capitalize(), frozenset(opt['p2_spec']['ivs']),
                          opt['p2_spec']['nature'])

        if p1_tuple_check == current_target_tuple_for_loop_check: c += 1000
        if p2_tuple_check == current_target_tuple_for_loop_check: c += 1000
        return c

    sorted_parent_options = sorted(possible_parent_options, key=option_complexity_sort_key)

    for option_idx, parent_option in enumerate(sorted_parent_options):
        p1_spec = parent_option['p1_spec']
        p2_spec = parent_option['p2_spec']

        p1_obj_result, p1_plan_result, p1_cost_result, p1_consumed_after = get_pokemon_with_minimal_cost(
            p1_spec['species'], set(p1_spec['ivs']), p1_spec['nature'],
            owned_pokemon_map, consumed_owned_ids, depth + 1
        )

        if p1_obj_result is None or p1_cost_result == float('inf'):
            continue

        p2_obj_result, p2_plan_result, p2_cost_result, p2_consumed_after = get_pokemon_with_minimal_cost(
            p2_spec['species'], set(p2_spec['ivs']), p2_spec['nature'],
            owned_pokemon_map, p1_consumed_after, depth + 1
        )

        if p2_obj_result is None or p2_cost_result == float('inf'):
            continue

        current_option_total_cost = p1_cost_result + p2_cost_result

        if current_option_total_cost < min_overall_cost:
            min_overall_cost = current_option_total_cost

            p1_gender_for_step, p2_gender_for_step = "Maschio", "Femmina"
            effective_p1_species = p1_obj_result.species.lower()
            effective_p2_species = p2_obj_result.species.lower()

            if effective_p1_species == "ditto":
                p1_gender_for_step = "Genderless"
                p2_gender_for_step = "Femmina" if effective_p2_species != "ditto" else "Genderless"
                if POKEMON_EGG_GROUPS_RAW.get(p2_obj_result.species.lower(), [""])[
                    0] == "Genderless" and effective_p2_species != "ditto":
                    p2_gender_for_step = "Genderless"
            elif effective_p2_species == "ditto":
                p2_gender_for_step = "Genderless"
                p1_gender_for_step = "Femmina" if effective_p1_species != "ditto" else "Genderless"
                if POKEMON_EGG_GROUPS_RAW.get(p1_obj_result.species.lower(), [""])[
                    0] == "Genderless" and effective_p1_species != "ditto":
                    p1_gender_for_step = "Genderless"
            else:
                if effective_p1_species == target_species_cap.lower():
                    p1_gender_for_step = "Femmina";
                    p2_gender_for_step = "Maschio"
                elif effective_p2_species == target_species_cap.lower():
                    p2_gender_for_step = "Femmina";
                    p1_gender_for_step = "Maschio"
                else:
                    if p1_spec['species'].lower() == target_species_cap.lower():
                        p1_gender_for_step = "Femmina";
                        p2_gender_for_step = "Maschio"
                    elif p2_spec['species'].lower() == target_species_cap.lower():
                        p2_gender_for_step = "Femmina";
                        p1_gender_for_step = "Maschio"
                    else:
                        d_print(
                            f"ATTENZIONE: Logica genere P1/P2 incerta per {p1_obj_result.species} + {p2_obj_result.species} -> {target_species_cap}")
                        p1_gender_for_step = "Femmina";
                        p2_gender_for_step = "Maschio"

            child_for_this_step = Pokemon(species=target_species_cap,
                                          ivs=set(target_ivs_fs),
                                          nature=target_nature,
                                          gender="Nascituro",
                                          name=f"Bred_{target_species_cap[:3]}",
                                          source_info=f"Intermedio (ID:temp, Costo Prod.: {min_overall_cost:.1f})")
            child_for_this_step.cost_to_produce = min_overall_cost
            child_for_this_step.source_info = f"Figlio Intermedio (ID:{child_for_this_step.id}, Costo Prod.: {min_overall_cost:.1f})"
            best_overall_child_obj = child_for_this_step

            p1_step_parent = p1_obj_result
            p1_step_parent.gender = p1_gender_for_step

            p2_step_parent = p2_obj_result
            p2_step_parent.gender = p2_gender_for_step

            current_step = BreedingStepDetailed(
                child_pokemon=best_overall_child_obj,
                parent1_pokemon=p1_step_parent, parent1_item=parent_option['item1'],
                parent2_pokemon=p2_step_parent, parent2_item=parent_option['item2']
            )
            best_overall_steps = p1_plan_result + p2_plan_result + [current_step]
            best_overall_consumed_ids = p2_consumed_after

            d_print(
                f"{'  ' * (depth + 1)}  SUCCESSFUL OPTION: Total cost {min_overall_cost}. Consumed: {list(best_overall_consumed_ids)}")

    if best_overall_child_obj:
        d_print(
            f"{'  ' * depth}RETURNING BEST for {target_species_cap} {target_ivs_fs} {target_nature}: Cost={min_overall_cost}, Child ID: {best_overall_child_obj.id}")
        memo_get_pokemon[memo_key] = (best_overall_child_obj, best_overall_steps, min_overall_cost,
                                      best_overall_consumed_ids)
        return best_overall_child_obj, best_overall_steps, min_overall_cost, best_overall_consumed_ids
    else:
        d_print(f"{'  ' * depth}NO VIABLE BREEDING PATH found for {target_species_cap} {target_ivs_fs} {target_nature}")
        memo_get_pokemon[memo_key] = (None, [], float('inf'), consumed_owned_ids)
        return None, [], float('inf'), consumed_owned_ids


def plan_breeding_recursively_phased(
        target_species: str,
        target_ivs: Set[str],
        target_nature: str,
        target_gender: str,
        owned_pokemon_list: List[Pokemon]
) -> Optional[List[BreedingStepDetailed]]:
    global memo_get_pokemon
    memo_get_pokemon = {}

    max_owned_id = -1
    if owned_pokemon_list:
        valid_ids = [p.id for p in owned_pokemon_list if hasattr(p, 'id') and isinstance(p.id, int)]
        if valid_ids:
            max_owned_id = max(valid_ids)
    Pokemon._id_counter = max_owned_id + 1001

    owned_pokemon_map = {p.id: p for p in owned_pokemon_list}

    d_print(
        f"\n\n--- Inizio Pianificazione: {target_species} IVs:{target_ivs} N:{target_nature} G:{target_gender} ({time.strftime('%H:%M:%S')}) ---")
    d_print(f"Pokémon Posseduti Iniziali: {[(p.name, p.id, p.ivs, p.nature) for p in owned_pokemon_list]}")
    d_print(f"ID Counter start: {Pokemon._id_counter}")

    final_pokemon_obj_template, plan_steps, total_cost, final_consumed_ids = get_pokemon_with_minimal_cost(
        target_species=target_species,
        target_ivs=target_ivs,
        target_nature=target_nature,
        owned_pokemon_map=owned_pokemon_map,
        consumed_owned_ids=frozenset(),
        depth=0
    )

    if final_pokemon_obj_template and total_cost != float('inf'):
        d_print(f"\n--- PIANO RICORSIVO TROVATO ({target_species}) ---")
        d_print(f"Costo Totale Acquisti Stimato: {total_cost}")
        d_print(f"ID Pokémon Posseduti Consumati (dal set finale): {list(final_consumed_ids)}")
        d_print(f"Template del Pokémon finale ottenuto dalla ricorsione: {final_pokemon_obj_template}")

        final_pokemon_for_plan: Pokemon

        if not plan_steps:
            d_print("Il piano non ha passi, il target era posseduto o acquistato base.")
            final_pokemon_for_plan = Pokemon(
                final_pokemon_obj_template.species,
                final_pokemon_obj_template.ivs,
                final_pokemon_obj_template.nature,
                target_gender,
                name=f"TARGET_{final_pokemon_obj_template.species[:3]}",
                is_owned=final_pokemon_obj_template.is_owned,
                source_info=f"FINALE ({final_pokemon_obj_template.source_info}, Costo Piano: {total_cost:.1f})",
                internal_id=final_pokemon_obj_template.id
            )
            final_pokemon_for_plan.cost_to_produce = total_cost

            dummy_p_na_id_1 = Pokemon._id_counter;
            Pokemon._id_counter += 1
            dummy_p_na_id_2 = Pokemon._id_counter;
            Pokemon._id_counter += 1
            dummy_p_na1 = Pokemon("N/A", set(), "NEUTRAL", "N/A", name="N/A_P1", internal_id=dummy_p_na_id_1,
                                  source_info="Dummy")
            dummy_p_na2 = Pokemon("N/A", set(), "NEUTRAL", "N/A", name="N/A_P2", internal_id=dummy_p_na_id_2,
                                  source_info="Dummy")
            step0 = BreedingStepDetailed(final_pokemon_for_plan, dummy_p_na1, None, dummy_p_na2, None, step_number=0)
            plan_steps = [step0]
            d_print(f"Creato passo fittizio 0 per il target: {final_pokemon_for_plan}")
        else:
            final_child_in_plan = plan_steps[-1].child
            final_child_in_plan.gender = target_gender
            final_child_in_plan.name = f"TARGET_{final_child_in_plan.species[:3]}"
            final_child_in_plan.source_info = f"FINALE (Costo Piano: {total_cost:.1f}, ID:{final_child_in_plan.id})"
            final_child_in_plan.cost_to_produce = total_cost
            final_pokemon_for_plan = final_child_in_plan
            d_print(f"Aggiornato l'ultimo figlio del piano: {final_pokemon_for_plan}")

        child_to_step_map: Dict[int, int] = {}
        for i, step in enumerate(plan_steps):
            step.step_number = i + 1 if plan_steps[0].step_number != 0 else i
            if step.child:
                child_to_step_map[step.child.id] = step.step_number
                if not step.child.source_info.startswith("FINALE") and \
                        not step.child.source_info.startswith("Figlio del Passo") and \
                        not step.child.source_info.startswith("Acquistato Base") and \
                        not step.child.source_info.startswith("Posseduto"):
                    step.child.source_info = f"Figlio del Passo {step.step_number} (ID:{step.child.id}, Costo prod.:{step.child.cost_to_produce:.1f})"

        for step in plan_steps:
            for parent_obj in [step.parent1, step.parent2]:
                if parent_obj.name.startswith("N/A_P"): continue
                if not parent_obj.is_owned and \
                        not parent_obj.source_info.startswith("Acquistato Base") and \
                        not parent_obj.source_info.startswith("Posseduto") and \
                        not parent_obj.source_info.startswith("Da Passo") and \
                        not parent_obj.source_info.startswith("Figlio del Passo"):
                    if parent_obj.id in child_to_step_map:
                        parent_obj.source_info = f"Da Passo {child_to_step_map[parent_obj.id]} (ID:{parent_obj.id}, Costo prod.:{parent_obj.cost_to_produce:.1f})"

        d_print(f"\n--- Dettagli del Piano Finale ({target_species}) ---")
        for step in plan_steps:
            d_print(str(step))

        return plan_steps
    else:
        d_print(f"\n--- NESSUN PIANO RICORSIVO TROVATO per {target_species} {target_ivs} {target_nature} ---")
        d_print(f"Costo riscontrato: {total_cost}")
        return None


find_optimal_breeding_plan = plan_breeding_recursively_phased


def run_complex_test():
    """Esegue test complessi per verificare la logica di breeding."""
    print("\n" + "=" * 30 + " ESECUZIONE TEST COMPLESSO (Output su debug.txt) " + "=" * 30)

    clear_debug_log_once_for_suite()
    d_print("\n" + "=" * 30 + " ESECUZIONE TEST COMPLESSO (Inizio Suite) " + "=" * 30)

    Pokemon._id_counter = 0
    owned_test1 = [
        Pokemon(species="Charizard", ivs={"PS"}, nature="Adamant", gender="Maschio", name="AdaChar1_PS", is_owned=True,
                internal_id=0),
        Pokemon(species="Ditto", ivs={"ATK", "DEF"}, nature="NEUTRAL", gender="Genderless", name="Ditto_AD",
                is_owned=True, internal_id=1),
        Pokemon(species="Charizard", ivs={"SPE"}, nature="Jolly", gender="Femmina", name="JolChar_SPE", is_owned=True,
                internal_id=2),
        Pokemon(species="Arcanine", ivs={"PS", "DEF"}, nature="Serious", gender="Maschio", name="Arca_PSDEF",
                is_owned=True, internal_id=3),
        Pokemon(species="Nidoqueen", ivs={"ATK"}, nature="Adamant", gender="Femmina", name="Nido_ATKAda", is_owned=True,
                internal_id=4),
        Pokemon(species="Blastoise", ivs={"SPD"}, nature="Modest", gender="Femmina", name="Blast_SPD", is_owned=True,
                internal_id=5)
    ]

    target_species_t1 = "Charizard"
    target_ivs_t1 = {"PS", "ATK", "DEF", "SPE"}
    target_nature_t1 = "Adamant"
    target_gender_t1 = "Maschio"

    print(f"\n--- Test 1: {target_species_t1} {target_ivs_t1} N:{target_nature_t1} G:{target_gender_t1} ---")

    plan1 = plan_breeding_recursively_phased(
        target_species_t1, target_ivs_t1, target_nature_t1, target_gender_t1, owned_test1
    )

    if plan1:
        print(f"Piano Test 1 trovato. Numero di passi: {len(plan1)}. Vedere debug.txt per dettagli.")
        final_cost_t1 = 0
        if plan1 and plan1[-1].child: final_cost_t1 = plan1[-1].child.cost_to_produce
        summary_t1 = f"Piano Test 1 completato. Numero di passi: {len(plan1)}. Costo Totale Acquisti: {final_cost_t1:.1f}"
        d_print(f"\nRIEPILOGO TEST 1: {summary_t1}\n")
    else:
        print("\n--- Nessun Piano Trovato per Test 1 ---")
        d_print("\n--- Nessun Piano Trovato per Test 1 ---\n")

    owned_test2 = [
        Pokemon(species="Dragonair", ivs={"PS", "ATK"}, nature="Hardy", gender="Maschio", name="Dra_PA_Hardy",
                is_owned=True, internal_id=10),
        Pokemon(species="Ditto", ivs={"SPA", "SPD"}, nature="NEUTRAL", gender="Genderless", name="Ditto_SpASpD",
                is_owned=True, internal_id=11),
        Pokemon(species="Gyarados", ivs={"DEF"}, nature="Timid", gender="Femmina", name="Gya_DEF_Timid", is_owned=True,
                internal_id=12),
        Pokemon(species="Kingdra", ivs={"SPE"}, nature="Modest", gender="Maschio", name="King_SPE_Mod", is_owned=True,
                internal_id=13),
        Pokemon(species="Altaria", ivs={"ATK"}, nature="NEUTRAL", gender="Femmina", name="Alta_ATK_N", is_owned=True,
                internal_id=14),
        Pokemon(species="Salamence", ivs={"PS", "SPA"}, nature="Jolly", gender="Maschio", name="Sala_PSSpA_Jol",
                is_owned=True, internal_id=15),
        Pokemon(species="Dragonite", ivs={"DEF"}, nature="NEUTRAL", gender="Femmina", name="Dnite_DEF", is_owned=True,
                internal_id=16)
    ]

    target_species_t2 = "Dragonite"
    target_ivs_t2 = {"PS", "ATK", "DEF", "SPA", "SPE"}
    target_nature_t2 = "Timid"
    target_gender_t2 = "Femmina"

    print(f"\n--- Test 2: {target_species_t2} {target_ivs_t2} N:{target_nature_t2} G:{target_gender_t2} ---")

    plan2 = plan_breeding_recursively_phased(
        target_species_t2, target_ivs_t2, target_nature_t2, target_gender_t2, owned_test2
    )
    if plan2:
        print(f"Piano Test 2 trovato. Numero di passi: {len(plan2)}. Vedere debug.txt per dettagli.")
        final_cost_t2 = 0
        if plan2 and plan2[-1].child: final_cost_t2 = plan2[-1].child.cost_to_produce
        summary_t2 = f"Piano Test 2 completato. Numero di passi: {len(plan2)}. Costo Totale Acquisti: {final_cost_t2:.1f}"
        d_print(f"\nRIEPILOGO TEST 2: {summary_t2}\n")
    else:
        print("\n--- Nessun Piano Trovato per Test 2 ---")
        d_print("\n--- Nessun Piano Trovato per Test 2 ---\n")

    d_print("\n" + "=" * 30 + " ESECUZIONE TEST COMPLESSO (Fine Suite) " + "=" * 30)


if __name__ == "__main__":
    run_complex_test()
