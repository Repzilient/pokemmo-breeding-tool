# pokemon_breeder.py
import json
from typing import List, Dict, Optional, Set, Tuple, Any
from itertools import combinations
import heapq
import time
from dataclasses import dataclass, field
import collections
import shutil # Added for copying debug files

# --- Costanti e Configurazione ---
DEBUG = True
DEBUG_FILE_NAME = "debug.txt"
EXPLORATION_LIMIT = 125000 
META_ANALYSIS_ATTEMPTS = 3 
NODES_FOR_META_ANALYSIS = 150 

IV_STATS = ["PS", "ATK", "DEF", "SPA", "SPD", "SPE"]
# Mappa NOME OGGETTO VIGOR -> STAT IV (usata se avessimo i nomi completi degli oggetti)
# VIGOR_ITEMS_FULL_NAME_TO_STAT = {
#     "VigorPeso": "PS", "VigorCerchio": "ATK", "VigorFascia": "DEF",
#     "VigorLente": "SPA", "VigorBanda": "SPD", "Vigorgliera": "SPE"
# }
# Mappa STAT IV -> NOME OGGETTO VIGOR (utile per descrizioni)
STAT_TO_VIGOR_ITEM_NAME = {
    "PS": "VigorPeso", "ATK": "VigorCerchio", "DEF": "VigorFascia",
    "SPA": "VigorLente", "SPD": "VigorBanda", "SPE": "Vigorgliera"
}


# --- Funzioni di Logging (invariate) ---
def clear_debug_log():
    try:
        with open(DEBUG_FILE_NAME, 'w', encoding='utf-8') as f:
            f.write(f"--- Inizio Nuovo Log A* Full Upgrade ({time.strftime('%Y-%m-%d %H:%M:%S')}) ---\n")
    except IOError: pass

def d_print(*args, **kwargs):
    if not DEBUG: return
    try:
        with open(DEBUG_FILE_NAME, 'a', encoding='utf-8') as f:
            print(*args, **kwargs, file=f)
    except IOError: pass

# --- Caricamento Dati Pokémon (invariato) ---
POKEMON_EGG_GROUPS_RAW = {}
ALL_POKEMON_NAMES = []
try:
    with open("pokemon_data.json", "r", encoding='utf-8') as f:
        data = json.load(f)
        POKEMON_EGG_GROUPS_RAW = {k.lower(): v for k, v in data.items()}
        ALL_POKEMON_NAMES = sorted([name.capitalize() for name in POKEMON_EGG_GROUPS_RAW.keys()])
except (FileNotFoundError, json.JSONDecodeError):
    print("Attenzione: file pokemon_data.json non trovato o corrotto.")

ALL_NATURES = sorted(["Adamant", "Bashful", "Bold", "Brave", "Calm", "Careful", "Docile", "Gentle", "Hardy", "Hasty", "Impish", "Jolly", "Lax", "Lonely", "Mild", "Modest", "Naive", "Naughty", "Quiet", "Quirky", "Rash", "Relaxed", "Sassy", "Serious", "Timid"])
ID_COUNTER = 1000

# --- Classi Fondamentali (Pokemon, BreedingNode - invariate) ---
class Pokemon:
    def __init__(self, species: str, ivs: Set[str], nature: str, gender: str, name: Optional[str] = None, is_owned: bool = False, source_info: str = ""):
        global ID_COUNTER
        self.id = ID_COUNTER
        ID_COUNTER += 1
        self.species = species.capitalize()
        self.name = name if name else self.species
        self.ivs = frozenset(ivs)
        self.nature = nature
        self.gender = gender
        self.is_owned = is_owned
        self.source_info = source_info

    def get_egg_groups(self) -> List[str]:
        return POKEMON_EGG_GROUPS_RAW.get(self.species.lower(), [])

    def __repr__(self):
        iv_str = sorted(list(self.ivs)) if self.ivs else "N/A"
        source_brief = self.source_info.split("_")[0] if self.source_info else ""
        return f"{self.name} ({self.species}, G:{self.gender}, N:{self.nature}, IVs:{iv_str}, ID:{self.id}, Src:{source_brief})"

@dataclass(order=True)
class BreedingNode:
    f_cost: float
    g_cost: int = field(compare=False) 
    available_pool: frozenset[Pokemon] = field(compare=False)
    plan: Tuple[str, ...] = field(compare=False)
    
    def __hash__(self):
        return hash((self.g_cost, frozenset(p.id for p in self.available_pool))) 

    def __eq__(self, other):
        if not isinstance(other, BreedingNode): return False
        return self.g_cost == other.g_cost and self.available_pool == other.available_pool


# --- Funzioni di Supporto per il Breeding (can_breed_with, determine_child_species - invariate) ---
def can_breed_with(pkm1: Pokemon, pkm2: Pokemon) -> bool:
    pkm1_is_ditto = pkm1.species == "Ditto"
    pkm2_is_ditto = pkm2.species == "Ditto"
    pkm1_groups = pkm1.get_egg_groups()
    pkm2_groups = pkm2.get_egg_groups()
    if not pkm1_groups or not pkm2_groups: return False
    if "Non Scoperto" in pkm1_groups or "Non Scoperto" in pkm2_groups: return False
    if pkm1_is_ditto and pkm2_is_ditto: return False
    if pkm1_is_ditto or pkm2_is_ditto: return True
    if pkm1.gender == pkm2.gender: return False
    if pkm1.gender == "Genderless" or pkm2.gender == "Genderless": return False
    return bool(set(pkm1_groups) & set(pkm2_groups))

def determine_child_species(p1: Pokemon, p2: Pokemon, target_species: str) -> Optional[str]:
    if p1.species == "Ditto" and p2.species != "Ditto":
        return p2.species
    elif p2.species == "Ditto" and p1.species != "Ditto":
        return p1.species
    elif p1.gender == "Femmina" and (p1.species == target_species or p2.species != target_species): 
        return p1.species
    elif p2.gender == "Femmina" and (p2.species == target_species or p1.species != target_species):
        return p2.species
    elif p1.gender == "Femmina": 
        return p1.species
    elif p2.gender == "Femmina":
        return p2.species
    d_print(f"ATTENZIONE: Impossibile determinare specie figlio per il target {target_species} da {repr(p1)} e {repr(p2)}")
    return None

# --- Euristica Raffinata (v3) (invariata) ---
def calculate_heuristic_v3(pool: frozenset[Pokemon], target: Pokemon) -> float:
    base_h_cost = 0
    pool_ivs_total = frozenset().union(*(p.ivs for p in pool))
    pool_natures_total = {p.nature for p in pool}

    if target.nature != "NEUTRAL" and target.nature not in pool_natures_total:
        base_h_cost += 20  
    missing_ivs_from_total_pool = target.ivs - pool_ivs_total
    base_h_cost += len(missing_ivs_from_total_pool) * 10 
    best_assembly_candidate_score = -100 
    found_perfect_candidate_for_assembly = False
    for pkm in pool:
        if not (pkm.species == target.species or pkm.species == "Ditto"):
            continue
        current_candidate_score = 0
        if pkm.nature == target.nature: current_candidate_score += 10 
        elif target.nature == "NEUTRAL": current_candidate_score += 2 
        else: 
            current_candidate_score -= 10 
            if target.nature in pool_natures_total: current_candidate_score += 5
        ivs_match_count = len(target.ivs.intersection(pkm.ivs))
        current_candidate_score += ivs_match_count * 3 
        if pkm.gender == target.gender or target.gender == "Any": current_candidate_score += 1
        if current_candidate_score > best_assembly_candidate_score:
            best_assembly_candidate_score = current_candidate_score
        if pkm.species == target.species and \
           (pkm.nature == target.nature or target.nature == "NEUTRAL") and \
           target.ivs.issubset(pkm.ivs) and \
           (pkm.gender == target.gender or target.gender == "Any"):
            found_perfect_candidate_for_assembly = True
            break 
    if found_perfect_candidate_for_assembly: assembly_penalty = 0
    else:
        max_possible_score = 10 + (len(target.ivs) * 3) + 1
        assembly_penalty = max(0, max_possible_score - best_assembly_candidate_score)
    return base_h_cost + assembly_penalty

def is_goal(pool: frozenset[Pokemon], target: Pokemon) -> Optional[Pokemon]:
    for pkm in pool:
        gender_match = (pkm.gender == target.gender) or (target.gender == "Any")
        if pkm.species == "Ditto" and pkm.gender == "Genderless" and target.gender not in ["Genderless", "Any"]:
            pass 
        elif pkm.species == target.species and \
           gender_match and \
           (pkm.nature == target.nature or target.nature == "NEUTRAL") and \
           target.ivs.issubset(pkm.ivs):
            return pkm
    return None

# --- A* Planner v4 (con correzione KeyError) ---
def a_star_planner_v4(initial_inventory: List[Pokemon], target: Pokemon, initial_g_cost: int = 0):
    # clear_debug_log() # Rimosso da qui, gestito per test case
    global ID_COUNTER
    max_initial_id = 0
    if initial_inventory: max_initial_id = max(p.id for p in initial_inventory if hasattr(p, 'id')) 
    ID_COUNTER = max(ID_COUNTER, max_initial_id + 100) 

    start_pool = frozenset(initial_inventory)
    g_cost = initial_g_cost
    h_cost = calculate_heuristic_v3(start_pool, target)
    start_node = BreedingNode(g_cost + h_cost, g_cost, start_pool, tuple())
    
    frontier = [start_node]
    visited_states = {} 
    
    nodes_explored = 0
    
    d_print(f"\n--- Inizio A* v4 (g_cost iniziale: {initial_g_cost}) per {repr(target)} ---")
    if initial_g_cost > 0 : d_print(f"Inventario potenziato dalla meta-analisi: {[repr(p) for p in initial_inventory if p.source_info.startswith('MetaAcquisto')]}")

    while frontier and nodes_explored < EXPLORATION_LIMIT:
        nodes_explored += 1
        current_node = heapq.heappop(frontier)

        if nodes_explored % 2000 == 0 or (len(frontier) < 50 and nodes_explored % 100 == 0):
            d_print(f"Iter: {nodes_explored}, Frontiera: {len(frontier)}, g: {current_node.g_cost}, h: {current_node.f_cost - current_node.g_cost:.2f}, f: {current_node.f_cost:.2f}, Pool: {len(current_node.available_pool)}")

        current_pool_ids_tuple = tuple(sorted(p.id for p in current_node.available_pool))
        if current_pool_ids_tuple in visited_states and visited_states[current_pool_ids_tuple] <= current_node.g_cost:
            continue
        visited_states[current_pool_ids_tuple] = current_node.g_cost

        goal_pokemon = is_goal(current_node.available_pool, target)
        if goal_pokemon:
            d_print(f"\nSOLUZIONE TROVATA! Costo g: {current_node.g_cost} acquisti. Nodi esplorati: {nodes_explored}")
            final_plan_list = list(current_node.plan)
            final_plan_list.append(f"OBIETTIVO RAGGIUNTO: {repr(goal_pokemon)}")
            return tuple(final_plan_list), goal_pokemon, [] 

        # --- Generazione Successori ---
        # 1. ACQUISTI 
        if not any(p.species == target.species and (p.nature == target.nature or target.nature=="NEUTRAL") for p in current_node.available_pool):
            purchase_sp = Pokemon(target.species, set(), "NEUTRAL" if target.nature != "NEUTRAL" else "NEUTRAL", 
                                  "Femmina" if target.gender != "Maschio" else "Maschio", 
                                  f"Acq_Base_{target.species}", source_info="Acq_BaseSpecie")
            new_pool_sp = current_node.available_pool.union({purchase_sp})
            new_g_sp, new_h_sp = current_node.g_cost + 1, calculate_heuristic_v3(new_pool_sp, target)
            new_plan_sp = current_node.plan + (f"Acquisto Base Specie ({target.species}): {repr(purchase_sp)}",)
            heapq.heappush(frontier, BreedingNode(new_g_sp + new_h_sp, new_g_sp, new_pool_sp, new_plan_sp))

        pool_ivs = frozenset().union(*(p.ivs for p in current_node.available_pool))
        missing_ivs = target.ivs - pool_ivs
        for iv in missing_ivs:
            purchase_iv = Pokemon("Ditto", {iv}, "NEUTRAL", "Genderless", f"Acq_Ditto_{iv}", source_info="Acq_IVMancante")
            new_pool_iv = current_node.available_pool.union({purchase_iv})
            new_g_iv, new_h_iv = current_node.g_cost + 1, calculate_heuristic_v3(new_pool_iv, target)
            new_plan_iv = current_node.plan + (f"Acquisto IV Mancante ({iv}): {repr(purchase_iv)}",)
            heapq.heappush(frontier, BreedingNode(new_g_iv + new_h_iv, new_g_iv, new_pool_iv, new_plan_iv))

        pool_natures = {p.nature for p in current_node.available_pool}
        if target.nature != "NEUTRAL" and target.nature not in pool_natures:
            purchase_n = Pokemon("Ditto", set(), target.nature, "Genderless", f"Acq_Ditto_{target.nature}", source_info="Acq_NaturaMancante")
            new_pool_n = current_node.available_pool.union({purchase_n})
            new_g_n, new_h_n = current_node.g_cost + 1, calculate_heuristic_v3(new_pool_n, target)
            new_plan_n = current_node.plan + (f"Acquisto Natura Mancante ({target.nature}): {repr(purchase_n)}",)
            heapq.heappush(frontier, BreedingNode(new_g_n + new_h_n, new_g_n, new_pool_n, new_plan_n))

        # 2. ACCOPPIAMENTI
        for p1, p2 in combinations(current_node.available_pool, 2):
            if not can_breed_with(p1, p2): continue
            
            child_species_for_pair = determine_child_species(p1, p2, target.species)
            if not child_species_for_pair: continue

            item_combos_to_try = []
            if p1.nature == target.nature or target.nature == "NEUTRAL":
                p1_stone = "Pietrastante" if p1.nature == target.nature else "Nessuno"
                for iv_p2_stat in IV_STATS: 
                    if iv_p2_stat in p2.ivs and iv_p2_stat in target.ivs: 
                        if not (p1_stone == "Pietrastante" and iv_p2_stat in p1.ivs):
                             item_combos_to_try.append({"p1_item": p1_stone, "p2_item": f"Vigor {iv_p2_stat}"})
                item_combos_to_try.append({"p1_item": p1_stone, "p2_item": "Nessuno"})

            if p2.nature == target.nature or target.nature == "NEUTRAL":
                p2_stone = "Pietrastante" if p2.nature == target.nature else "Nessuno"
                for iv_p1_stat in IV_STATS:
                    if iv_p1_stat in p1.ivs and iv_p1_stat in target.ivs:
                        if not (p2_stone == "Pietrastante" and iv_p1_stat in p2.ivs):
                            item_combos_to_try.append({"p1_item": f"Vigor {iv_p1_stat}", "p2_item": p2_stone})
                item_combos_to_try.append({"p1_item": "Nessuno", "p2_item": p2_stone})
            
            if target.nature == "NEUTRAL" or target.nature in {p1.nature, p2.nature}: 
                for iv_p1_stat in IV_STATS:
                    if iv_p1_stat not in p1.ivs or iv_p1_stat not in target.ivs: continue
                    for iv_p2_stat in IV_STATS:
                        if iv_p2_stat not in p2.ivs or iv_p2_stat not in target.ivs: continue
                        if iv_p1_stat == iv_p2_stat: continue 
                        item_combos_to_try.append({"p1_item": f"Vigor {iv_p1_stat}", "p2_item": f"Vigor {iv_p2_stat}"})
            
            for iv_s_single in IV_STATS:
                if iv_s_single in p1.ivs and iv_s_single in target.ivs: item_combos_to_try.append({"p1_item": f"Vigor {iv_s_single}", "p2_item": "Nessuno"})
                if iv_s_single in p2.ivs and iv_s_single in target.ivs: item_combos_to_try.append({"p1_item": "Nessuno", "p2_item": f"Vigor {iv_s_single}"})

            item_combos_to_try.append({"p1_item": "Nessuno", "p2_item": "Nessuno"})
            generated_children_in_combo = set()

            for combo in item_combos_to_try:
                p1_item_str, p2_item_str = combo["p1_item"], combo["p2_item"]
                child_ivs = set()
                child_nature = "NEUTRAL" 

                if p1_item_str == "Pietrastante": child_nature = p1.nature
                elif p2_item_str == "Pietrastante": child_nature = p2.nature
                elif target.nature == "NEUTRAL": child_nature = "NEUTRAL"
                else: child_nature = p1.nature 

                if p1_item_str and p1_item_str.startswith("Vigor "):
                    iv_stat_to_add = p1_item_str.split(" ")[1] 
                    if iv_stat_to_add in IV_STATS: child_ivs.add(iv_stat_to_add)
                if p2_item_str and p2_item_str.startswith("Vigor "):
                    iv_stat_to_add = p2_item_str.split(" ")[1]
                    if iv_stat_to_add in IV_STATS: child_ivs.add(iv_stat_to_add)
                
                child_ivs.update(p1.ivs.intersection(p2.ivs))
                child_gender_final = target.gender if target.gender != "Any" else ("Femmina" if child_species_for_pair != "Ditto" else "Genderless")
                child = Pokemon(child_species_for_pair, child_ivs, child_nature, child_gender_final, f"Bred_{p1.id}_{p2.id}", source_info="Bred")
                child_sig = (child.species, child.ivs, child.nature, child.gender)
                if child_sig in generated_children_in_combo: continue
                generated_children_in_combo.add(child_sig)

                new_pool_c = current_node.available_pool - {p1, p2} | {child}
                new_g_c = current_node.g_cost
                new_h_c = calculate_heuristic_v3(new_pool_c, target)
                new_pool_c_tuple = tuple(sorted(p.id for p in new_pool_c))
                if new_pool_c_tuple not in visited_states or visited_states[new_pool_c_tuple] > new_g_c:
                    new_plan_c = current_node.plan + (f"Accoppiamento: {repr(p1)} [{p1_item_str}] + {repr(p2)} [{p2_item_str}] -> {repr(child)}",)
                    heapq.heappush(frontier, BreedingNode(new_g_c + new_h_c, new_g_c, new_pool_c, new_plan_c))

    d_print(f"Ricerca A* v4 terminata. Limite ({EXPLORATION_LIMIT} nodi) raggiunto o frontiera vuota.")
    promising_nodes_for_meta = sorted(frontier, key=lambda node: node.f_cost)[:NODES_FOR_META_ANALYSIS]
    return None, None, promising_nodes_for_meta

# --- Meta-Analisi v2 (invariata) ---
def meta_analyzer_v2(promising_nodes: List[BreedingNode], target: Pokemon, past_meta_suggestions: List[Pokemon]) -> Optional[Pokemon]:
    d_print(f"\n--- Inizio Meta-Analisi v2 (Analizzando {len(promising_nodes)} nodi) ---")
    if not promising_nodes:
        d_print("Nessun nodo promettente da analizzare.")
        return None
    nature_on_target_species_missing = 0 
    specific_iv_on_natured_target_species_missing = collections.defaultdict(int) 
    general_nature_missing = 0 
    general_iv_missing = collections.defaultdict(int) 
    for node in promising_nodes:
        pool_natures = {p.nature for p in node.available_pool}
        pool_ivs_total = frozenset().union(*(p.ivs for p in node.available_pool))
        if target.nature != "NEUTRAL" and target.nature not in pool_natures: general_nature_missing += 1
        for iv in target.ivs:
            if iv not in pool_ivs_total: general_iv_missing[iv] += 1
        found_candidate_with_nature_and_species = False
        for pkm in node.available_pool:
            if (pkm.species == target.species or pkm.species == "Ditto"):
                if pkm.nature == target.nature:
                    found_candidate_with_nature_and_species = True
                    for iv_target in target.ivs:
                        if iv_target not in pkm.ivs: specific_iv_on_natured_target_species_missing[iv_target] +=1
                    break 
        if target.nature != "NEUTRAL" and not found_candidate_with_nature_and_species: nature_on_target_species_missing +=1
    num_nodes = len(promising_nodes)
    if num_nodes == 0: num_nodes = 1 
    already_suggested_specific_nature_transfer = any(p.nature == target.nature and (p.species == "Ditto" or p.species == target.species) and p.source_info.startswith("MetaAcquisto") for p in past_meta_suggestions)
    if target.nature != "NEUTRAL" and (nature_on_target_species_missing / num_nodes > 0.6) and not already_suggested_specific_nature_transfer:
        suggestion = Pokemon("Ditto", set(), target.nature, "Genderless", f"MetaAcq_Ditto_{target.nature}", source_info=f"MetaAcquisto_NaturaPerSpecie_{target.nature}")
        d_print(f"Meta-Suggerimento (Natura su Specie): {repr(suggestion)}")
        return suggestion
    if specific_iv_on_natured_target_species_missing:
        most_needed_iv_on_good_candidate = max(specific_iv_on_natured_target_species_missing, key=specific_iv_on_natured_target_species_missing.get)
        already_suggested_this_iv_compound = any(most_needed_iv_on_good_candidate in p.ivs and p.nature == target.nature and p.source_info.startswith("MetaAcquisto") for p in past_meta_suggestions)
        if (specific_iv_on_natured_target_species_missing[most_needed_iv_on_good_candidate] / num_nodes > 0.5) and not already_suggested_this_iv_compound:
            suggestion = Pokemon("Ditto", {most_needed_iv_on_good_candidate}, target.nature, "Genderless", f"MetaAcq_Ditto_{most_needed_iv_on_good_candidate}_{target.nature}", source_info=f"MetaAcquisto_IVNatura_{most_needed_iv_on_good_candidate}_{target.nature}")
            d_print(f"Meta-Suggerimento (IV su Specie Naturata): {repr(suggestion)}")
            return suggestion
    already_suggested_general_nature = any(p.nature == target.nature and p.source_info.startswith("MetaAcquisto_NaturaMancante") for p in past_meta_suggestions)
    if target.nature != "NEUTRAL" and (general_nature_missing / num_nodes > 0.7) and not already_suggested_specific_nature_transfer and not already_suggested_general_nature:
        suggestion = Pokemon("Ditto", set(), target.nature, "Genderless", f"MetaAcq_Ditto_N_Gen_{target.nature}", source_info=f"MetaAcquisto_NaturaMancante_{target.nature}")
        d_print(f"Meta-Suggerimento (Natura Generale): {repr(suggestion)}")
        return suggestion
    if general_iv_missing:
        most_missing_general_iv = max(general_iv_missing, key=general_iv_missing.get)
        already_suggested_this_general_iv = any(most_missing_general_iv in p.ivs and p.source_info.startswith("MetaAcquisto_IVMancante") for p in past_meta_suggestions)
        if (general_iv_missing[most_missing_general_iv] / num_nodes > 0.6) and not already_suggested_this_iv_compound and not already_suggested_this_general_iv:
            suggestion = Pokemon("Ditto", {most_missing_general_iv}, "NEUTRAL", "Genderless", f"MetaAcq_Ditto_IV_Gen_{most_missing_general_iv}", source_info=f"MetaAcquisto_IVMancante_{most_missing_general_iv}")
            d_print(f"Meta-Suggerimento (IV Generale): {repr(suggestion)}")
            return suggestion
    d_print("Meta-Analisi v2 non ha prodotto nuovi suggerimenti chiari.")
    return None

# --- Test Case 1: Gengar ---
def run_test_case_1_gengar():
    clear_debug_log()
    header_msg = "====================== EXECUTING TEST CASE 1: GENGAR ======================"
    print(f"\n{header_msg}")
    d_print(f"\n{header_msg}\n")
    
    initial_inventory_base_case1 = []
    target_pokemon_case1 = Pokemon(species="Gengar", ivs={"SPA", "SPD", "SPE"}, nature="Timid", gender="Femmina")
    
    d_print(f"--- Obiettivo Gengar Test Case: {repr(target_pokemon_case1)} ---")
    print(f"\n--- Obiettivo Gengar Test Case: {repr(target_pokemon_case1)} ---")
    
    accumulated_meta_suggestions_case1: List[Pokemon] = [] 
    accumulated_meta_purchases_cost_case1 = 0
    final_plan_overall_case1: Optional[Tuple[str, ...]] = None
    final_pokemon_obj_overall_case1: Optional[Pokemon] = None

    for attempt in range(META_ANALYSIS_ATTEMPTS):
        d_print(f"\n<<<<< GENGAR TEST META-TENTATIVO N. {attempt + 1} (Costo acquisti meta già effettuati: {accumulated_meta_purchases_cost_case1}) >>>>>")
        print(f"\nGengar Test Meta-Tentativo N. {attempt + 1}...")
        
        effective_inventory_for_a_star_case1 = list(initial_inventory_base_case1) + accumulated_meta_suggestions_case1
        
        if accumulated_meta_suggestions_case1:
             print(f"  Inventario potenziato con: {[repr(p) for p in accumulated_meta_suggestions_case1]}")
             d_print(f"  Inventario potenziato con: {[repr(p) for p in accumulated_meta_suggestions_case1]}")

        start_time = time.time()
        plan_from_a_star, goal_pokemon_from_a_star, promising_nodes = a_star_planner_v4(
            effective_inventory_for_a_star_case1, 
            target_pokemon_case1,
            initial_g_cost=accumulated_meta_purchases_cost_case1
        )
        end_time = time.time()
        print(f"  Tempo A* per tentativo {attempt+1}: {end_time - start_time:.2f} secondi.")
        d_print(f"  Tempo A* per tentativo {attempt+1}: {end_time - start_time:.2f} secondi.")

        if plan_from_a_star:
            print(f"  SUCCESSO nel tentativo {attempt+1}!")
            d_print(f"  SUCCESSO nel tentativo {attempt+1}!")
            final_plan_overall_case1 = plan_from_a_star
            final_pokemon_obj_overall_case1 = goal_pokemon_from_a_star
            break 
        
        print(f"  A* non ha trovato un piano nel tentativo {attempt+1}. Eseguo meta-analisi...")
        d_print(f"  A* non ha trovato un piano nel tentativo {attempt+1}. Eseguo meta-analisi...")
        if not promising_nodes:
            print("  Nessun nodo promettente fornito da A* per la meta-analisi. Interrompo.")
            d_print("  Nessun nodo promettente fornito da A* per la meta-analisi. Interrompo.")
            break

        meta_suggestion = meta_analyzer_v2(promising_nodes, target_pokemon_case1, accumulated_meta_suggestions_case1)
        
        if meta_suggestion:
            is_redundant_suggestion = False
            for prev_sugg in accumulated_meta_suggestions_case1:
                if prev_sugg.nature == meta_suggestion.nature and prev_sugg.ivs == meta_suggestion.ivs and prev_sugg.species == meta_suggestion.species:
                    is_redundant_suggestion = True
                    break
            if is_redundant_suggestion:
                print(f"  Meta-Analisi ha suggerito un Pokémon ({repr(meta_suggestion)}) già considerato. Interrompo.")
                d_print(f"  Meta-Analisi ha suggerito un Pokémon ({repr(meta_suggestion)}) già considerato. Interrompo.")
                break
            print(f"  Meta-Analisi suggerisce l'acquisto di: {repr(meta_suggestion)}")
            d_print(f"  Meta-Analisi suggerisce l'acquisto di: {repr(meta_suggestion)}")
            accumulated_meta_suggestions_case1.append(meta_suggestion)
            accumulated_meta_purchases_cost_case1 += 1 
        else:
            print("  Meta-Analisi non ha nuovi suggerimenti. Interrompo.")
            d_print("  Meta-Analisi non ha nuovi suggerimenti. Interrompo.")
            break 
    
    if final_plan_overall_case1:
        actual_purchases_in_plan = len([s for s in final_plan_overall_case1 if 'Acquisto' in s or 'MetaAcquisto' in s])
        summary_msg_gengar = f"\nPIANO FINALE TROVATO PER GENGAR!\nCosto Totale Effettivo (contando 'Acquisto' nel piano): {actual_purchases_in_plan} acquisti."
        print(summary_msg_gengar)
        d_print(summary_msg_gengar)
        
        print("--------------------------------------------------")
        d_print("--------------------------------------------------")
        for i, step in enumerate(final_plan_overall_case1):
            if "OBIETTIVO RAGGIUNTO" not in step : 
                 print(f"  Passo {i+1}: {step}")
                 d_print(f"  Passo {i+1}: {step}")
        print("--------------------------------------------------")
        d_print("--------------------------------------------------")
        
        final_pokemon_msg_gengar = f"Pokémon Finale Ottenuto: {repr(final_pokemon_obj_overall_case1)}"
        print(final_pokemon_msg_gengar)
        d_print(final_pokemon_msg_gengar)
    else:
        no_plan_msg_gengar = "\nNESSUN PIANO TROVATO PER GENGAR ANCHE DOPO I TENTATIVI DI META-ANALISI."
        print(no_plan_msg_gengar)
        d_print(no_plan_msg_gengar)

# --- Test Case 2: Dragonite ---
def run_test_case_2_dragonite():
    clear_debug_log() 
    header_msg = "====================== EXECUTING TEST CASE 2: DRAGONITE ======================"
    print(f"\n{header_msg}")
    d_print(f"\n{header_msg}\n")

    initial_inventory_base_case2 = [
        Pokemon(species="Dragonair", ivs={"ATK", "SPE"}, nature="Adamant", gender="Femmina", name="Owned_Dragonair_ATKSPE_Ada", is_owned=True, source_info="Owned"),
        Pokemon(species="Gyarados", ivs={"DEF", "PS"}, nature="Jolly", gender="Maschio", name="Owned_Gyarados_DEFPS_Jol", is_owned=True, source_info="Owned"),
        Pokemon(species="Ditto", ivs={"SPE", "SPA"}, nature="Modest", gender="Genderless", name="Owned_Ditto_SPESPA_Mod", is_owned=True, source_info="Owned"),
        Pokemon(species="Magikarp", ivs={"PS"}, nature="Bashful", gender="Maschio", name="Owned_Magikarp_PS", is_owned=True, source_info="Owned")
    ]
    target_pokemon_case2 = Pokemon(species="Dragonite", ivs={"ATK", "SPE", "DEF"}, nature="Adamant", gender="Maschio")

    d_print(f"--- Obiettivo Dragonite Test Case: {repr(target_pokemon_case2)} ---")
    print(f"\n--- Obiettivo Dragonite Test Case: {repr(target_pokemon_case2)} ---")
    
    accumulated_meta_suggestions_case2: List[Pokemon] = [] 
    accumulated_meta_purchases_cost_case2 = 0
    final_plan_overall_case2: Optional[Tuple[str, ...]] = None
    final_pokemon_obj_overall_case2: Optional[Pokemon] = None

    for attempt in range(META_ANALYSIS_ATTEMPTS):
        d_print(f"\n<<<<< DRAGONITE TEST META-TENTATIVO N. {attempt + 1} (Costo acquisti meta già effettuati: {accumulated_meta_purchases_cost_case2}) >>>>>")
        print(f"\nDragonite Test Meta-Tentativo N. {attempt + 1}...")
        
        effective_inventory_for_a_star_case2 = list(initial_inventory_base_case2) + accumulated_meta_suggestions_case2
        
        if accumulated_meta_suggestions_case2:
             print(f"  Inventario potenziato con: {[repr(p) for p in accumulated_meta_suggestions_case2]}")
             d_print(f"  Inventario potenziato con: {[repr(p) for p in accumulated_meta_suggestions_case2]}")

        start_time = time.time()
        plan_from_a_star, goal_pokemon_from_a_star, promising_nodes = a_star_planner_v4(
            effective_inventory_for_a_star_case2, 
            target_pokemon_case2,
            initial_g_cost=accumulated_meta_purchases_cost_case2 
        )
        end_time = time.time()
        print(f"  Tempo A* per tentativo {attempt+1}: {end_time - start_time:.2f} secondi.")
        d_print(f"  Tempo A* per tentativo {attempt+1}: {end_time - start_time:.2f} secondi.")

        if plan_from_a_star:
            print(f"  SUCCESSO nel tentativo {attempt+1}!")
            d_print(f"  SUCCESSO nel tentativo {attempt+1}!")
            final_plan_overall_case2 = plan_from_a_star
            final_pokemon_obj_overall_case2 = goal_pokemon_from_a_star
            break 
        
        print(f"  A* non ha trovato un piano nel tentativo {attempt+1}. Eseguo meta-analisi...")
        d_print(f"  A* non ha trovato un piano nel tentativo {attempt+1}. Eseguo meta-analisi...")
        if not promising_nodes:
            print("  Nessun nodo promettente fornito da A* per la meta-analisi. Interrompo.")
            d_print("  Nessun nodo promettente fornito da A* per la meta-analisi. Interrompo.")
            break

        meta_suggestion = meta_analyzer_v2(promising_nodes, target_pokemon_case2, accumulated_meta_suggestions_case2)
        
        if meta_suggestion:
            is_redundant_suggestion = False
            for prev_sugg in accumulated_meta_suggestions_case2:
                if prev_sugg.nature == meta_suggestion.nature and prev_sugg.ivs == meta_suggestion.ivs and prev_sugg.species == meta_suggestion.species:
                    is_redundant_suggestion = True
                    break
            if is_redundant_suggestion:
                print(f"  Meta-Analisi ha suggerito un Pokémon ({repr(meta_suggestion)}) già considerato. Interrompo.")
                d_print(f"  Meta-Analisi ha suggerito un Pokémon ({repr(meta_suggestion)}) già considerato. Interrompo.")
                break
            print(f"  Meta-Analisi suggerisce l'acquisto di: {repr(meta_suggestion)}")
            d_print(f"  Meta-Analisi suggerisce l'acquisto di: {repr(meta_suggestion)}")
            accumulated_meta_suggestions_case2.append(meta_suggestion)
            accumulated_meta_purchases_cost_case2 += 1 
        else:
            print("  Meta-Analisi non ha nuovi suggerimenti. Interrompo.")
            d_print("  Meta-Analisi non ha nuovi suggerimenti. Interrompo.")
            break 
    
    if final_plan_overall_case2:
        actual_purchases_in_plan = len([s for s in final_plan_overall_case2 if 'Acquisto' in s or 'MetaAcquisto' in s])
        summary_msg_dragonite = f"\nPIANO FINALE TROVATO PER DRAGONITE!\nCosto Totale Effettivo (contando 'Acquisto' nel piano): {actual_purchases_in_plan} acquisti."
        print(summary_msg_dragonite)
        d_print(summary_msg_dragonite)
        
        print("--------------------------------------------------")
        d_print("--------------------------------------------------")
        for i, step in enumerate(final_plan_overall_case2):
            if "OBIETTIVO RAGGIUNTO" not in step : 
                 print(f"  Passo {i+1}: {step}")
                 d_print(f"  Passo {i+1}: {step}")
        print("--------------------------------------------------")
        d_print("--------------------------------------------------")
        
        final_pokemon_msg_dragonite = f"Pokémon Finale Ottenuto: {repr(final_pokemon_obj_overall_case2)}"
        print(final_pokemon_msg_dragonite)
        d_print(final_pokemon_msg_dragonite)
    else:
        no_plan_msg_dragonite = "\nNESSUN PIANO TROVATO PER DRAGONITE ANCHE DOPO I TENTATIVI DI META-ANALISI."
        print(no_plan_msg_dragonite)
        d_print(no_plan_msg_dragonite)

if __name__ == "__main__":
    # run_gyarados_test_with_meta_analysis() # Original test commented out
    
    run_test_case_1_gengar()
    try:
        # Ensure debug.txt exists before trying to copy, though clear_debug_log should create it
        if DEBUG: # Only copy if debugging is on, otherwise debug.txt might not exist or be relevant
             shutil.copy(DEBUG_FILE_NAME, "debug_case1.txt")
             d_print(f"\n[System] Successfully copied {DEBUG_FILE_NAME} to debug_case1.txt after Gengar test.")
    except FileNotFoundError:
        print(f"[System] Error: {DEBUG_FILE_NAME} not found for Gengar, cannot copy to debug_case1.txt.")
        d_print(f"[System] Error: {DEBUG_FILE_NAME} not found for Gengar, cannot copy to debug_case1.txt.")
    except Exception as e:
        print(f"[System] Error copying debug_case1.txt: {e}")
        d_print(f"[System] Error copying debug_case1.txt: {e}")

    run_test_case_2_dragonite()
    try:
        if DEBUG: # Only copy if debugging is on
            shutil.copy(DEBUG_FILE_NAME, "debug_case2.txt")
            # This d_print will go into the debug_case2.txt (the new debug.txt for Dragonite)
            d_print(f"\n[System] Successfully copied {DEBUG_FILE_NAME} to debug_case2.txt after Dragonite test.")
    except FileNotFoundError:
        print(f"[System] Error: {DEBUG_FILE_NAME} not found for Dragonite, cannot copy to debug_case2.txt.")
        d_print(f"[System] Error: {DEBUG_FILE_NAME} not found for Dragonite, cannot copy to debug_case2.txt.") # This will also go to Dragonite's debug
    except Exception as e:
        print(f"[System] Error copying debug_case2.txt: {e}")
        d_print(f"[System] Error copying debug_case2.txt: {e}")
