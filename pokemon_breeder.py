# pokemon_breeder.py
import json
from typing import List, Dict, Optional, Set, Tuple, Any
import functools
import heapq
from itertools import combinations

DEBUG_ASTAR = True


def d_print(*args, **kwargs):
    if DEBUG_ASTAR:
        print(*args, **kwargs)


def load_pokemon_data(filename="pokemon_data.json") -> Dict[str, List[str]]:
    try:
        with open(filename, 'r', encoding='utf-8') as f:
            data = json.load(f)
            return {k.lower(): v for k, v in data.items()}
    except (FileNotFoundError, json.JSONDecodeError):
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
    _id_counter = 0

    def __init__(self, species: str, ivs: Set[str], nature: str, gender: str,
                 name: Optional[str] = None, is_owned: bool = False,
                 source_info: str = "N/A"):
        self.species = species.capitalize()
        self.name = name if name else self.species
        self.ivs = set(ivs)
        self.nature = nature
        self.gender = gender
        self.is_owned = is_owned
        self.egg_groups = POKEMON_EGG_GROUPS_RAW.get(self.species.lower(), [])
        self.id = Pokemon._id_counter
        Pokemon._id_counter += 1
        self.source_info = source_info

    def __repr__(self):
        iv_str = ", ".join(sorted(list(self.ivs))) if self.ivs else "Nessuno"
        return (f"{self.name} ({self.species}, {self.gender}) | N: {self.nature}, "
                f"IVs: [{iv_str}] | ID: {self.id} | Fonte: {self.source_info}")

    def get_display_string(self):
        iv_str = f"IVs: {', '.join(sorted(list(self.ivs)))}" if self.ivs else "Nessun IV 31"
        nature_str = f"Natura: {self.nature}" if self.nature != "NEUTRAL" else "Natura non specificata"
        return f"{self.name} ({self.species}, {self.gender}) - {nature_str}, {iv_str}"


class BreedingStepDetailed:
    def __init__(self, child_pokemon: Pokemon,
                 parent1_pokemon: Pokemon, parent1_item: Optional[str],
                 parent2_pokemon: Pokemon, parent2_item: Optional[str],
                 step_number: int = 0):
        self.child = child_pokemon
        self.parent1 = parent1_pokemon
        self.parent1_item = parent1_item
        self.parent2 = parent2_pokemon
        self.parent2_item = parent2_item
        self.step_number = step_number

    def __str__(self):
        child_ivs_str = str(set(self.child.ivs)) if self.child.ivs else "{}"
        p1_ivs_str = str(set(self.parent1.ivs)) if self.parent1.ivs else "{}"
        p2_ivs_str = str(set(self.parent2.ivs)) if self.parent2.ivs else "{}"
        return (f"--- PASSO {self.step_number} ---\n"
                f"  Figlio Generato: {self.child.name} ({self.child.species}, {self.child.gender}) N:{self.child.nature}, IVs:{child_ivs_str} (Fonte: {self.child.source_info})\n"
                f"  Genitore 1: {self.parent1.name} ({self.parent1.species}, {self.parent1.gender}) [{self.parent1_item if self.parent1_item else 'Nessun Oggetto'}]\n"
                f"    (N:{self.parent1.nature}, IVs:{p1_ivs_str}, Fonte:{self.parent1.source_info})\n"
                f"  Genitore 2: {self.parent2.name} ({self.parent2.species}, {self.parent2.gender}) [{self.parent2_item if self.parent2_item else 'Nessun Oggetto'}]\n"
                f"    (N:{self.parent2.nature}, IVs:{p2_ivs_str}, Fonte:{self.parent2.source_info})\n")


@functools.total_ordering
class BreedingNode:
    def __init__(self, species: str, ivs: Set[str], nature: str,
                 g_cost: float = float('inf'), depth: int = 0,
                 used_owned_ids: Optional[Set[int]] = None):
        self.species = species.capitalize()
        self.ivs = frozenset(ivs)
        self.nature = nature
        self.g_cost = g_cost
        self.h_cost = 0
        self.depth = depth
        self.used_owned_pokemon_ids = used_owned_ids if used_owned_ids is not None else set()
        self.action_taken_to_create_this_node: Optional[Dict[str, Any]] = None
        self.parent_options_for_this_node: List[Dict[str, Any]] = []
        self.children_in_plan_this_node_is_parent_for: List[Tuple[BreedingNode, Dict[str, Any]]] = []

    @property
    def f_cost(self) -> float:
        return self.g_cost + self.h_cost

    def get_state_tuple(self) -> Tuple[str, frozenset, str]:
        return (self.species, self.ivs, self.nature)

    def get_full_state_tuple_for_closed_list(self) -> Tuple[str, frozenset, str, frozenset]:
        return (self.species, self.ivs, self.nature, frozenset(self.used_owned_pokemon_ids))

    def __eq__(self, other):
        if not isinstance(other, BreedingNode): return NotImplemented
        return self.get_full_state_tuple_for_closed_list() == other.get_full_state_tuple_for_closed_list()

    def __lt__(self, other):
        if not isinstance(other, BreedingNode): return NotImplemented
        if self.f_cost != other.f_cost:
            return self.f_cost < other.f_cost
        if self.h_cost != other.h_cost:
            return self.h_cost < other.h_cost
        return self.g_cost < other.g_cost

    def __hash__(self):
        return hash(self.get_full_state_tuple_for_closed_list())

    def __repr__(self):
        iv_s = set(self.ivs)
        action_type = self.action_taken_to_create_this_node.get('type',
                                                                'N/D') if self.action_taken_to_create_this_node else 'N/D'
        return (f"Nodo(S:{self.species}, IVs:{iv_s if iv_s else '{}'}, N:{self.nature}, "
                f"g:{self.g_cost:.1f}, h:{self.h_cost:.1f}, f:{self.f_cost:.1f}, d:{self.depth}, "
                f"UsedIDs:{sorted(list(self.used_owned_pokemon_ids)) if self.used_owned_pokemon_ids else '{}'}, Action:{action_type})")


def calculate_heuristic(node_to_evaluate: BreedingNode, owned_pokemon: List[Pokemon]) -> int:
    _species, node_ivs_set, node_nature = node_to_evaluate.species, set(node_to_evaluate.ivs), node_to_evaluate.nature
    is_base = (not node_ivs_set and node_nature == "NEUTRAL") or \
              (len(node_ivs_set) == 1 and node_nature == "NEUTRAL") or \
              (not node_ivs_set and node_nature != "NEUTRAL") or \
              (len(node_ivs_set) == 1 and node_nature != "NEUTRAL") # Added: 1 IV + Specific Nature
    if is_base:
        for pkm in owned_pokemon:
            if pkm.id not in node_to_evaluate.used_owned_pokemon_ids and \
                    pkm.species == _species and node_ivs_set.issubset(pkm.ivs) and \
                    (node_nature == "NEUTRAL" or node_nature == pkm.nature):
                return 0
        return 1
    h = 0
    if node_nature != "NEUTRAL":
        if not any(p.id not in node_to_evaluate.used_owned_pokemon_ids and
                   p.nature == node_nature and
                   (p.species == _species or p.species.lower() == 'ditto')
                   for p in owned_pokemon):
            h += 1
    for iv in node_ivs_set:
        if not any(p.id not in node_to_evaluate.used_owned_pokemon_ids and
                   iv in p.ivs and
                   (p.species == _species or p.species.lower() == 'ditto')
                   for p in owned_pokemon):
            h += 1
    if not node_ivs_set and node_nature == "NEUTRAL" and h == 0:
        if not any(p.id not in node_to_evaluate.used_owned_pokemon_ids and p.species == _species and
                   not p.ivs and p.nature == "NEUTRAL" for p in owned_pokemon):
            return 1
    return h


def generate_breeding_options_for_child(child_node_state: BreedingNode) -> List[Dict[str, Any]]:
    options: List[Dict[str, Any]] = []
    child_s, child_i_set, child_n = child_node_state.species, set(child_node_state.ivs), child_node_state.nature
    is_child_buyable_base = (not child_i_set and child_n == "NEUTRAL") or \
                            (len(child_i_set) == 1 and child_n == "NEUTRAL") or \
                            (not child_i_set and child_n != "NEUTRAL") or \
                            (len(child_i_set) == 1 and child_n != "NEUTRAL") # Added: 1 IV + Specific Nature
    if is_child_buyable_base:
        d_print(
            f"  [GenOpts] Nodo figlio {child_node_state.get_state_tuple()} è acquistabile base, nessuna opzione di breeding.")
        return []
    d_print(f"  [GenOpts] Generazione opzioni per figlio: {child_node_state.get_state_tuple()}")
    if child_n != "NEUTRAL":
        p1_spec_1a = {'species': child_s, 'ivs': set(child_i_set), 'nature': child_n}
        p2_spec_1a = {'species': child_s, 'ivs': set(child_i_set), 'nature': "NEUTRAL"}
        options.append(
            {'type': 'bred', 'p1_spec': p1_spec_1a, 'p2_spec': p2_spec_1a, 'item1': EVERSTONE, 'item2': None})
        for iv_x_from_p2_vigor in child_i_set:
            item2_for_p2 = VIGOR_ITEMS_MAP.get(iv_x_from_p2_vigor)
            if not item2_for_p2: continue
            shared_ivs_for_1b = child_i_set - {iv_x_from_p2_vigor}
            p1_spec_1b = {'species': child_s, 'ivs': set(shared_ivs_for_1b), 'nature': child_n}
            p2_ivs_for_1b = set(shared_ivs_for_1b);
            p2_ivs_for_1b.add(iv_x_from_p2_vigor)
            p2_spec_1b = {'species': child_s, 'ivs': p2_ivs_for_1b, 'nature': "NEUTRAL"}
            options.append({'type': 'bred', 'p1_spec': p1_spec_1b, 'p2_spec': p2_spec_1b, 'item1': EVERSTONE,
                            'item2': item2_for_p2})
    if child_i_set:
        for iv_x_from_p1_vigor in child_i_set:
            item1_for_p1 = VIGOR_ITEMS_MAP.get(iv_x_from_p1_vigor)
            if not item1_for_p1: continue
            shared_ivs_for_2a = child_i_set - {iv_x_from_p1_vigor}
            p1_ivs_for_2a = set(shared_ivs_for_2a);
            p1_ivs_for_2a.add(iv_x_from_p1_vigor)
            p1_spec_2a = {'species': child_s, 'ivs': p1_ivs_for_2a, 'nature': "NEUTRAL"}
            p2_nature_req = child_n if child_n != "NEUTRAL" else "NEUTRAL"
            item2_for_p2 = EVERSTONE if child_n != "NEUTRAL" else None
            p2_spec_2a = {'species': child_s, 'ivs': set(shared_ivs_for_2a), 'nature': p2_nature_req}
            options.append({'type': 'bred', 'p1_spec': p1_spec_2a, 'p2_spec': p2_spec_2a, 'item1': item1_for_p1,
                            'item2': item2_for_p2})
    if child_n == "NEUTRAL" and len(child_i_set) >= 2:
        for iv_x, iv_y in combinations(child_i_set, 2):
            item1_for_p1 = VIGOR_ITEMS_MAP.get(iv_x);
            item2_for_p2 = VIGOR_ITEMS_MAP.get(iv_y)
            if not item1_for_p1 or not item2_for_p2 or item1_for_p1 == item2_for_p2: continue
            shared_ivs_for_2b = child_i_set - {iv_x, iv_y}
            p1_ivs_for_2b = set(shared_ivs_for_2b);
            p1_ivs_for_2b.add(iv_x)
            p2_ivs_for_2b = set(shared_ivs_for_2b);
            p2_ivs_for_2b.add(iv_y)
            p1_spec_2b = {'species': child_s, 'ivs': p1_ivs_for_2b, 'nature': "NEUTRAL"}
            p2_spec_2b = {'species': child_s, 'ivs': p2_ivs_for_2b, 'nature': "NEUTRAL"}
            options.append({'type': 'bred', 'p1_spec': p1_spec_2b, 'p2_spec': p2_spec_2b, 'item1': item1_for_p1,
                            'item2': item2_for_p2})
    if child_n == "NEUTRAL" and child_i_set:
        p1_spec_2c = {'species': child_s, 'ivs': set(child_i_set), 'nature': "NEUTRAL"}
        p2_spec_2c = {'species': child_s, 'ivs': set(child_i_set), 'nature': "NEUTRAL"}
        options.append({'type': 'bred', 'p1_spec': p1_spec_2c, 'p2_spec': p2_spec_2c, 'item1': None, 'item2': None})
    final_options, seen_options_tuples = [], set()
    for opt_idx, opt in enumerate(options):
        p1_s, p1_i, p1_n = opt['p1_spec']['species'], frozenset(opt['p1_spec']['ivs']), opt['p1_spec']['nature']
        p2_s, p2_i, p2_n = opt['p2_spec']['species'], frozenset(opt['p2_spec']['ivs']), opt['p2_spec']['nature']
        it1, it2 = opt['item1'], opt['item2']
        if (it1 == EVERSTONE and it2 == EVERSTONE): continue
        if it1 and it1 in REVERSE_VIGOR_ITEMS_MAP.values() and \
                it2 and it2 in REVERSE_VIGOR_ITEMS_MAP.values() and it1 == it2:
            continue
        parents_tuple_part1 = (p1_s, tuple(sorted(list(p1_i))), p1_n, it1)
        parents_tuple_part2 = (p2_s, tuple(sorted(list(p2_i))), p2_n, it2)
        sorted_parents_tuple = tuple(sorted((parents_tuple_part1, parents_tuple_part2)))
        if sorted_parents_tuple not in seen_options_tuples:
            final_options.append(opt)
            seen_options_tuples.add(sorted_parents_tuple)
            d_print(
                f"    [GenOpts] Opzione valida {len(final_options)}: P1({p1_s}, {set(p1_i)}, {p1_n}, It:{it1}) + P2({p2_s}, {set(p2_i)}, {p2_n}, It:{it2})")
    d_print(f"  [GenOpts] Trovate {len(final_options)} opzioni uniche per {child_node_state.get_state_tuple()}")
    return final_options


_RECONSTRUCTION_INSTANCE_COUNTER = 0
_final_target_node_for_reconstruction: Optional[BreedingNode] = None


def propagate_cost_update_to_children_in_plan(
        resolved_parent_P: BreedingNode,
        open_list: list,
        open_list_map: Dict[Tuple[str, frozenset, str, frozenset], BreedingNode],
        closed_list: Dict[Tuple[str, frozenset, str, frozenset], BreedingNode],
        owned_pokemon_list: List[Pokemon],
        final_goal_node_for_heuristic: BreedingNode
):
    d_print(
        f"    [Propagate] Genitore Risolto P: {resolved_parent_P.get_state_tuple()} (key: {resolved_parent_P.get_full_state_tuple_for_closed_list()}) con g={resolved_parent_P.g_cost}. Used: {resolved_parent_P.used_owned_pokemon_ids}")

    if resolved_parent_P.g_cost == float('inf'): return

    for child_C_node_original_ref, breeding_option_for_C in resolved_parent_P.children_in_plan_this_node_is_parent_for:
        d_print(
            f"      [Propagate] Considerando figlio C (ref originale): {child_C_node_original_ref.get_state_tuple()} (key: {child_C_node_original_ref.get_full_state_tuple_for_closed_list()}) attuale g={child_C_node_original_ref.g_cost}")

        p1_spec_in_option = breeding_option_for_C['p1_spec']
        p2_spec_in_option = breeding_option_for_C['p2_spec']

        current_P_node_state_tuple = resolved_parent_P.get_state_tuple()
        other_parent_spec_in_option: Optional[Dict[str, Any]] = None

        if current_P_node_state_tuple == (p1_spec_in_option['species'], frozenset(p1_spec_in_option['ivs']),
                                          p1_spec_in_option['nature']):
            other_parent_spec_in_option = p2_spec_in_option
        elif current_P_node_state_tuple == (p2_spec_in_option['species'], frozenset(p2_spec_in_option['ivs']),
                                            p2_spec_in_option['nature']):
            other_parent_spec_in_option = p1_spec_in_option
        else:
            d_print(
                f"        [Propagate] ERRORE MATCH: resolved_parent_P {resolved_parent_P.get_state_tuple()} non matcha spec opzione per C {child_C_node_original_ref.get_state_tuple()}.");
            continue

        if not other_parent_spec_in_option: continue

        other_parent_resolved_node: Optional[BreedingNode] = None
        other_parent_target_state_tuple = (other_parent_spec_in_option['species'],
                                           frozenset(other_parent_spec_in_option['ivs']),
                                           other_parent_spec_in_option['nature'])

        possible_other_parents = [node for key, node in closed_list.items() if
                                  node.get_state_tuple() == other_parent_target_state_tuple]
        for p_other_candidate in possible_other_parents:
            if p_other_candidate.g_cost != float('inf') and \
                    not resolved_parent_P.used_owned_pokemon_ids.intersection(p_other_candidate.used_owned_pokemon_ids):
                if other_parent_resolved_node is None or p_other_candidate.g_cost < other_parent_resolved_node.g_cost:
                    other_parent_resolved_node = p_other_candidate

        if not other_parent_resolved_node:
            d_print(
                f"        [Propagate] Altro genitore P_other ({other_parent_target_state_tuple}) non ancora risolto/compatibile in closed_list. Salto aggiornamento per C.")
            continue

        d_print(
            f"        [Propagate] Trovato altro genitore P_other risolto: {other_parent_resolved_node.get_state_tuple()} (key: {other_parent_resolved_node.get_full_state_tuple_for_closed_list()}) con g={other_parent_resolved_node.g_cost}. Used: {other_parent_resolved_node.used_owned_pokemon_ids}")

        new_g_cost_for_child_C = resolved_parent_P.g_cost + other_parent_resolved_node.g_cost
        combined_used_ids = resolved_parent_P.used_owned_pokemon_ids.union(
            other_parent_resolved_node.used_owned_pokemon_ids)
        child_C_target_full_key = (child_C_node_original_ref.species, child_C_node_original_ref.ivs,
                                   child_C_node_original_ref.nature, frozenset(combined_used_ids))

        node_to_update_C: BreedingNode
        if child_C_target_full_key in open_list_map:
            node_to_update_C = open_list_map[child_C_target_full_key]
        elif child_C_target_full_key in closed_list:
            node_to_update_C = closed_list[child_C_target_full_key]
        elif child_C_node_original_ref.get_full_state_tuple_for_closed_list() == child_C_target_full_key:
            node_to_update_C = child_C_node_original_ref
        else:
            node_to_update_C = BreedingNode(
                species=child_C_node_original_ref.species, ivs=child_C_node_original_ref.ivs,
                nature=child_C_node_original_ref.nature,
                g_cost=float('inf'), depth=child_C_node_original_ref.depth,
                used_owned_ids=combined_used_ids
            )
            node_to_update_C.parent_options_for_this_node = list(child_C_node_original_ref.parent_options_for_this_node)
            node_to_update_C.children_in_plan_this_node_is_parent_for = list(
                child_C_node_original_ref.children_in_plan_this_node_is_parent_for)

        if new_g_cost_for_child_C < node_to_update_C.g_cost:
            d_print(
                f"        [Propagate] Trovato percorso MIGLIORE per figlio C {node_to_update_C.get_state_tuple()} (key: {child_C_target_full_key}): nuovo g={new_g_cost_for_child_C} (vecchio g={node_to_update_C.g_cost}). Used IDs: {combined_used_ids}")

            node_to_update_C.g_cost = new_g_cost_for_child_C
            node_to_update_C.used_owned_pokemon_ids = combined_used_ids
            node_to_update_C.action_taken_to_create_this_node = {
                'type': 'bred',
                'p1_node_full_key': resolved_parent_P.get_full_state_tuple_for_closed_list() if resolved_parent_P.get_state_tuple() == (
                    p1_spec_in_option['species'], frozenset(p1_spec_in_option['ivs']),
                    p1_spec_in_option['nature']) else other_parent_resolved_node.get_full_state_tuple_for_closed_list(),
                'p2_node_full_key': other_parent_resolved_node.get_full_state_tuple_for_closed_list() if resolved_parent_P.get_state_tuple() == (
                    p1_spec_in_option['species'], frozenset(p1_spec_in_option['ivs']),
                    p1_spec_in_option['nature']) else resolved_parent_P.get_full_state_tuple_for_closed_list(),
                'item1': breeding_option_for_C['item1'],
                'item2': breeding_option_for_C['item2']
            }
            node_to_update_C.h_cost = calculate_heuristic(node_to_update_C, owned_pokemon_list)
            d_print(f"          [Propagate] Aggiornato figlio C: {node_to_update_C}")

            if child_C_target_full_key in closed_list and closed_list[child_C_target_full_key] == node_to_update_C:
                del closed_list[child_C_target_full_key]
                d_print(f"          [Propagate] Rimosso {child_C_target_full_key} da closed_list per riapertura.")

            if child_C_target_full_key in open_list_map:
                if open_list_map[child_C_target_full_key] != node_to_update_C or \
                        open_list_map[child_C_target_full_key].g_cost > new_g_cost_for_child_C:
                    try:
                        if open_list_map[child_C_target_full_key] != node_to_update_C:
                            open_list.remove(open_list_map[child_C_target_full_key])
                            heapq.heapify(open_list)
                    except ValueError:
                        pass
                    if open_list_map.get(child_C_target_full_key) != node_to_update_C:
                        heapq.heappush(open_list, node_to_update_C)
                    open_list_map[child_C_target_full_key] = node_to_update_C
                    d_print(f"          [Propagate] Nodo {child_C_target_full_key} aggiornato/riaggiunto a open_list.")
            else:
                heapq.heappush(open_list, node_to_update_C)
                open_list_map[child_C_target_full_key] = node_to_update_C
                d_print(f"          [Propagate] Nodo {child_C_target_full_key} aggiunto a open_list.")
        else:
            d_print(
                f"        [Propagate] Percorso NON migliore per figlio C {node_to_update_C.get_state_tuple()} (key: {child_C_target_full_key}): nuovo g={new_g_cost_for_child_C}, vecchio g={node_to_update_C.g_cost}.")


def _materialize_node_recursively(
        node_to_materialize_key: Tuple[str, frozenset, str, frozenset],
        target_gender_for_this_instance: str,
        closed_list_lookup: Dict[Tuple[str, frozenset, str, frozenset], BreedingNode],
        owned_pokemon_map_by_id: Dict[int, Pokemon],
        parent_context_name: str,
        is_final_target_node: bool
) -> Tuple[Optional[Pokemon], List[BreedingStepDetailed]]:
    global _RECONSTRUCTION_INSTANCE_COUNTER
    _RECONSTRUCTION_INSTANCE_COUNTER += 1
    current_instance_suffix = f"inst{_RECONSTRUCTION_INSTANCE_COUNTER}"

    node_definition = closed_list_lookup.get(node_to_materialize_key)
    if not node_definition:
        d_print(
            f"  [RecursiveMat:{current_instance_suffix}] ERRORE: Definizione nodo {node_to_materialize_key} non trovata.")
        error_pkm = Pokemon("ErroreRic", set(), "NEUTRAL", "N/A",
                            name=f"Err_{parent_context_name}_{current_instance_suffix}",
                            source_info="Def Nodo Mancante")
        return error_pkm, []

    action = node_definition.action_taken_to_create_this_node
    steps_for_this_node: List[BreedingStepDetailed] = []
    created_pokemon_instance: Optional[Pokemon] = None

    effective_gender = target_gender_for_this_instance
    if node_definition.species.lower() == "ditto":
        effective_gender = "Genderless"

    unique_name_base = f"{node_definition.species[:3]}_{parent_context_name}_{current_instance_suffix}"

    if not action:
        d_print(
            f"  [RecursiveMat:{current_instance_suffix}] ERRORE: Azione mancante per nodo {node_to_materialize_key}")
        created_pokemon_instance = Pokemon(node_definition.species, set(node_definition.ivs), node_definition.nature,
                                           effective_gender,
                                           name=f"Err_NoAct_{unique_name_base}",
                                           source_info=f"Azione Mancante ({unique_name_base})")
        return created_pokemon_instance, []

    elif action['type'] == 'owned':
        pkm_id = action['pokemon_id']
        original_pkm_obj = action.get('pokemon_object') or owned_pokemon_map_by_id.get(pkm_id)
        if original_pkm_obj:
            actual_display_gender = original_pkm_obj.gender
            if original_pkm_obj.species.lower() != "ditto":
                actual_display_gender = target_gender_for_this_instance if is_final_target_node else original_pkm_obj.gender
            else:
                actual_display_gender = "Genderless"

            created_pokemon_instance = Pokemon(original_pkm_obj.species, original_pkm_obj.ivs, original_pkm_obj.nature,
                                               actual_display_gender,
                                               name=f"{original_pkm_obj.name}_{current_instance_suffix}", is_owned=True,
                                               source_info=f"Posseduto (ID:{original_pkm_obj.id}) per {parent_context_name} (Costo Nodo:{node_definition.g_cost})")
            created_pokemon_instance.id = original_pkm_obj.id
        else:
            created_pokemon_instance = Pokemon(node_definition.species, set(node_definition.ivs),
                                               node_definition.nature, effective_gender,
                                               name=f"Err_OwnMiss_{unique_name_base}",
                                               source_info=f"Posseduto Mancante ID:{pkm_id}")
        return created_pokemon_instance, []

    elif action['type'] == 'bought_base':
        created_pokemon_instance = Pokemon(node_definition.species, set(node_definition.ivs), node_definition.nature,
                                           effective_gender,
                                           name=f"Acq_{unique_name_base}", is_owned=False,
                                           source_info=f"Acquistato Base per {parent_context_name} (Costo Nodo:{node_definition.g_cost})")
        return created_pokemon_instance, []

    elif action['type'] == 'bred':
        p1_key, p2_key = action.get('p1_node_full_key'), action.get('p2_node_full_key')
        item1, item2 = action.get('item1'), action.get('item2')

        p1_node_def = closed_list_lookup.get(p1_key)
        p2_node_def = closed_list_lookup.get(p2_key)

        if not p1_node_def or not p2_node_def:
            d_print(
                f"  [RecursiveMat:{current_instance_suffix}] ERRORE: Def genitore mancante per {node_to_materialize_key}")
            error_pkm = Pokemon(node_definition.species, set(node_definition.ivs), node_definition.nature,
                                effective_gender, name=f"Err_ParentDef_{unique_name_base}",
                                source_info="Def Genitore Mancante")
            return error_pkm, []

        p1_req_gender, p2_req_gender = "Maschio", "Femmina"

        if p1_node_def.species.lower() == "ditto":
            p1_req_gender = "Genderless"
            # If P1 is Ditto, P2 must be the one providing the species for the child.
            # P2's gender for breeding with Ditto can be either Male or Female.
            # We assign a gender opposite to the desired child's gender for P2,
            # unless child is genderless (then P2 can be anything not Ditto).
            if effective_gender == "Genderless":
                p2_req_gender = "Femmina"  # Default if child is genderless and P2 is not Ditto
            else:
                p2_req_gender = "Femmina" if effective_gender == "Maschio" else "Maschio"

            if node_definition.species.lower() != p2_node_def.species.lower():
                d_print(
                    f"  [RecursiveMat:{current_instance_suffix}] ERRORE SPECIE (P1 Ditto): P2 {p2_node_def.species} dovrebbe essere {node_definition.species}")
        elif p2_node_def.species.lower() == "ditto":
            p2_req_gender = "Genderless"
            # If P2 is Ditto, P1 must be the one providing the species.
            if effective_gender == "Genderless":
                p1_req_gender = "Femmina"  # Default if child is genderless and P1 is not Ditto
            else:
                p1_req_gender = "Femmina" if effective_gender == "Maschio" else "Maschio"
            if node_definition.species.lower() != p1_node_def.species.lower():
                d_print(
                    f"  [RecursiveMat:{current_instance_suffix}] ERRORE SPECIE (P2 Ditto): P1 {p1_node_def.species} dovrebbe essere {node_definition.species}")
        else:  # Neither parent is Ditto
            # Child species must come from the female parent.
            # If child species matches P1, P1 must be female.
            if node_definition.species.lower() == p1_node_def.species.lower():
                p1_req_gender = "Femmina"
                p2_req_gender = "Maschio"
            # If child species matches P2, P2 must be female.
            elif node_definition.species.lower() == p2_node_def.species.lower():
                p2_req_gender = "Femmina"
                p1_req_gender = "Maschio"
            else:
                # This case implies an egg group match but different species, which is complex.
                # For now, default to P1 female, P2 male if species don't match child.
                # This might need refinement based on specific game mechanics for cross-species breeding if it's common.
                d_print(
                    f"  [RecursiveMat:{current_instance_suffix}] AVVISO SPECIE/GENERE (Non-Ditto): Figlio={node_definition.species}, P1={p1_node_def.species}, P2={p2_node_def.species}. Assegnazione generi di default P1=F, P2=M.")
                p1_req_gender = "Femmina"
                p2_req_gender = "Maschio"

        (p1_instance, p1_steps) = _materialize_node_recursively(p1_key, p1_req_gender, closed_list_lookup,
                                                                owned_pokemon_map_by_id, parent_context_name + "_p1",
                                                                False)
        (p2_instance, p2_steps) = _materialize_node_recursively(p2_key, p2_req_gender, closed_list_lookup,
                                                                owned_pokemon_map_by_id, parent_context_name + "_p2",
                                                                False)

        if not p1_instance or not p2_instance:
            d_print(
                f"  [RecursiveMat:{current_instance_suffix}] ERRORE: Fallita materializzazione di un genitore per {node_to_materialize_key}")
            created_pokemon_instance = Pokemon(node_definition.species, set(node_definition.ivs),
                                               node_definition.nature, effective_gender,
                                               name=f"Err_ParentMat_{unique_name_base}",
                                               source_info="Fallita Mat. Genitore")
            all_partial_steps = []
            if p1_steps: all_partial_steps.extend(p1_steps)
            if p2_steps: all_partial_steps.extend(p2_steps)
            return created_pokemon_instance, all_partial_steps

        # Ensure correct gender assignment for display and logic, especially if one is Ditto
        p1_final_gender = p1_instance.gender
        p2_final_gender = p2_instance.gender

        if p1_instance.species.lower() == "ditto":
            p1_final_gender = "Genderless"
            # If P1 is Ditto, P2 determines the species. P2's gender should be set according to breeding rules.
            # If child is genderless, P2 can be M/F. If child has gender, P2 is that gender.
            if node_definition.species.lower() == p2_instance.species.lower():  # P2 is the species parent
                if effective_gender != "Genderless":
                    p2_final_gender = effective_gender  # P2 takes child's gender if child is gendered
                # If child is genderless, p2_final_gender remains as it was (M or F, not Ditto)
        elif p2_instance.species.lower() == "ditto":
            p2_final_gender = "Genderless"
            if node_definition.species.lower() == p1_instance.species.lower():  # P1 is the species parent
                if effective_gender != "Genderless":
                    p1_final_gender = effective_gender
        else:  # Neither is Ditto
            # The female parent determines the species.
            # Ensure the parent providing the species is female.
            if node_definition.species.lower() == p1_instance.species.lower():
                p1_final_gender = "Femmina"
                p2_final_gender = "Maschio"
            elif node_definition.species.lower() == p2_instance.species.lower():
                p2_final_gender = "Femmina"
                p1_final_gender = "Maschio"
            # If genders were conflicting (e.g. both male), adjust one.
            if p1_final_gender != "Genderless" and p2_final_gender != "Genderless" and p1_final_gender == p2_final_gender:
                d_print(
                    f"  [RecursiveMat:{current_instance_suffix}] Adattamento genere (non-Ditto): P1({p1_final_gender}) & P2({p2_final_gender}) -> P2 diventa l'opposto di P1.")
                p2_final_gender = "Femmina" if p1_final_gender == "Maschio" else "Maschio"

        p1_instance.gender = p1_final_gender
        p2_instance.gender = p2_final_gender

        created_pokemon_instance = Pokemon(node_definition.species, set(node_definition.ivs), node_definition.nature,
                                           effective_gender,
                                           name=f"Bred_{unique_name_base}",
                                           source_info=f"Generato per {parent_context_name} (Costo Nodo Orig:{node_definition.g_cost})")

        current_step = BreedingStepDetailed(created_pokemon_instance, p1_instance, item1, p2_instance, item2)
        steps_for_this_node.extend(p1_steps)
        steps_for_this_node.extend(p2_steps)
        steps_for_this_node.append(current_step)

        return created_pokemon_instance, steps_for_this_node

    else:
        d_print(
            f"  [RecursiveMat:{current_instance_suffix}] ERRORE: Tipo azione '{action.get('type')}' sconosciuto per {node_to_materialize_key}")
        created_pokemon_instance = Pokemon(node_definition.species, set(node_definition.ivs), node_definition.nature,
                                           effective_gender, name=f"Err_BadAct_{unique_name_base}",
                                           source_info="Azione Sconosciuta")
        return created_pokemon_instance, []


def reconstruct_plan(final_node: BreedingNode, target_final_gender: str,
                     owned_pokemon_map_by_id: Dict[int, Pokemon],
                     closed_list_for_lookup: Dict[Tuple[str, frozenset, str, frozenset], BreedingNode]
                     ) -> List[BreedingStepDetailed]:
    d_print("\n--- Inizio Ricostruzione Piano (Logica Ricorsiva) ---")
    global _RECONSTRUCTION_INSTANCE_COUNTER, _final_target_node_for_reconstruction
    _RECONSTRUCTION_INSTANCE_COUNTER = 0
    _final_target_node_for_reconstruction = final_node

    max_owned_id = -1
    if owned_pokemon_map_by_id:
        max_owned_id = max(owned_pokemon_map_by_id.keys(), default=-1)
    Pokemon._id_counter = max_owned_id + 1001  # Start new IDs well above owned ones

    if final_node is None or (not final_node.action_taken_to_create_this_node and final_node.g_cost == float('inf')):
        d_print(f"  [Reconstruct] Nodo finale invalido o non risolto. Impossibile ricostruire.")
        return [BreedingStepDetailed(
            Pokemon("Errore", set(), "NEUTRAL", "N/A", source_info=f"Piano Invalido (Nodo Target non risolto)"),
            Pokemon("N/A", set(), "NEUTRAL", "N/A"), None, Pokemon("N/A", set(), "NEUTRAL", "N/A"), None)]

    final_node_key = final_node.get_full_state_tuple_for_closed_list()

    final_pokemon_instance, all_steps = _materialize_node_recursively(
        final_node_key,
        target_final_gender,
        closed_list_for_lookup,
        owned_pokemon_map_by_id,
        "target",
        True  # This is the final target node
    )

    # Assign step numbers and refine source info for generated/bought Pokemon in steps
    generated_pokemon_in_plan_ids = set()
    step_counter = 0
    final_plan_ordered: List[BreedingStepDetailed] = []

    # First, identify all Pokemon that are products of a breeding step (children)
    # These are the ones that will get a step number in their source_info if they are bred
    # Owned or directly bought base Pokemon for the final target don't get this "Passo X" in source.

    # We need a way to uniquely identify Pokemon instances within the plan as they are created
    # The Pokemon.id is global, so newly created Pokemon will have unique IDs.
    # We can use these IDs to track if a Pokemon in a step was already part of a previous step's output.

    # Re-think step numbering:
    # The goal is to present a chronological plan.
    # The `all_steps` list is already roughly in order of dependency due to recursion.
    # We just need to assign sequential step numbers.

    temp_id_map_for_reconstruction: Dict[
        int, Pokemon] = {}  # Maps original Pokemon ID to reconstructed instance for this plan

    # Populate owned Pokemon into the temp map
    for p_id, p_obj in owned_pokemon_map_by_id.items():
        temp_id_map_for_reconstruction[p_id] = p_obj

    processed_child_ids_for_numbering = set()

    for i, step in enumerate(all_steps):
        step.step_number = i + 1

        # Update source_info for the child of this step
        child_source_info_prefix = "Generato"
        if step.child.source_info.startswith("Acq_"):  # Indicates it was a 'bought_base' type node
            child_source_info_prefix = "Acquistato Base"

        # Ensure child's name reflects its role if it's not an owned Pokemon being directly used
        # The name like "Bred_Cha_target_p1_inst123" is already good.
        # Source info should clearly indicate it's from this step.
        step.child.source_info = f"{child_source_info_prefix} (Passo {step.step_number})"

        # For parents, if they were from a previous step, their source_info should already be set.
        # If a parent is an owned Pokemon, its source_info will be like "Posseduto (ID:X)"
        # If a parent was bought base for a previous step, its source_info will reflect that.

        # Add the child to the temp_id_map if it's newly created in this step
        if not step.child.is_owned:  # Check if it's not an original owned Pokemon
            temp_id_map_for_reconstruction[step.child.id] = step.child

        # Update parent instances from the temp_id_map if they were products of earlier steps or owned
        if step.parent1.id in temp_id_map_for_reconstruction and temp_id_map_for_reconstruction[
            step.parent1.id] != step.parent1:
            step.parent1 = temp_id_map_for_reconstruction[step.parent1.id]
        elif not step.parent1.is_owned and step.parent1.id not in temp_id_map_for_reconstruction and step.parent1.name != "N/A":
            # This case implies a parent was materialized but not from owned or a previous step's child,
            # which means it was likely a 'bought_base' that didn't become a child of another step.
            # Its source_info should reflect it was bought.
            if "Acquistato Base per" in step.parent1.source_info:  # Check the original source_info from node materialization
                step.parent1.source_info = "Acquistato Base (Necessario per Passo Successivo)"  # Generic, as it's not a step child
            temp_id_map_for_reconstruction[step.parent1.id] = step.parent1

        if step.parent2.id in temp_id_map_for_reconstruction and temp_id_map_for_reconstruction[
            step.parent2.id] != step.parent2:
            step.parent2 = temp_id_map_for_reconstruction[step.parent2.id]
        elif not step.parent2.is_owned and step.parent2.id not in temp_id_map_for_reconstruction and step.parent2.name != "N/A":
            if "Acquistato Base per" in step.parent2.source_info:
                step.parent2.source_info = "Acquistato Base (Necessario per Passo Successivo)"
            temp_id_map_for_reconstruction[step.parent2.id] = step.parent2

    if not all_steps and final_pokemon_instance:
        action = final_node.action_taken_to_create_this_node
        if action and action.get('type') in ('owned', 'bought_base'):
            d_print(f"  [Reconstruct] Piano finale è un Pokémon base/owned: {final_pokemon_instance}")
            dummy_p = Pokemon("N/A", set(), "NEUTRAL", "N/A", source_info="Non Applicabile")
            # Update source_info of the final Pokemon to be more descriptive for this special case
            final_pokemon_instance.source_info = f"TARGET ({action.get('type').upper()}, Costo Totale: {final_node.g_cost})"
            if action.get('type') == 'owned':
                final_pokemon_instance.source_info += f", ID Originale: {action.get('pokemon_id')}"
            return [BreedingStepDetailed(final_pokemon_instance, dummy_p, None, dummy_p, None,
                                         step_number=0)]  # Step 0 for base case

    d_print(f"--- Fine Ricostruzione Piano (Logica Ricorsiva). Step totali: {len(all_steps)} ---")
    if not all_steps:
        d_print(
            f"  [Reconstruct] Nessuno step generato. Nodo finale: {final_node}, Azione: {final_node.action_taken_to_create_this_node}")
        return [BreedingStepDetailed(
            Pokemon("Errore", set(), "NEUTRAL", "N/A",
                    source_info=f"Piano Vuoto o Errore Ricostr. (Target: {final_node.get_state_tuple()})"),
            Pokemon("N/A", set(), "NEUTRAL", "N/A"), None, Pokemon("N/A", set(), "NEUTRAL", "N/A"), None)]

    return all_steps


def find_optimal_breeding_plan(
        target_species: str, target_ivs: Set[str], target_nature: str, target_gender: str,
        owned_pokemon_list: List[Pokemon], max_depth: int = 10, max_nodes_to_explore: int = 100000
):
    initial_max_id = -1
    if owned_pokemon_list:
        initial_max_id = max((p.id for p in owned_pokemon_list), default=-1)
    Pokemon._id_counter = initial_max_id + 1

    d_print(f"\n--- Inizio A* per {target_species} {target_ivs} {target_nature} ({target_gender}) ---")
    d_print(f"Pokémon Posseduti: {[str(p) for p in owned_pokemon_list]}")

    start_node = BreedingNode(species=target_species, ivs=target_ivs, nature=target_nature,
                              g_cost=float('inf'), depth=0, used_owned_ids=set())
    start_node.h_cost = calculate_heuristic(start_node, owned_pokemon_list)

    open_list: List[BreedingNode] = []
    open_list_map: Dict[Tuple[str, frozenset, str, frozenset], BreedingNode] = {}

    heapq.heappush(open_list, start_node)
    open_list_map[start_node.get_full_state_tuple_for_closed_list()] = start_node
    d_print(f"[A*] Start Node aggiunto a Open List: {start_node}")

    closed_list: Dict[Tuple[str, frozenset, str, frozenset], BreedingNode] = {}
    nodes_processed_count = 0

    while open_list and nodes_processed_count < max_nodes_to_explore:
        nodes_processed_count += 1
        current_C_node = heapq.heappop(open_list)
        current_C_full_key = current_C_node.get_full_state_tuple_for_closed_list()

        if current_C_full_key in open_list_map:
            del open_list_map[current_C_full_key]

        d_print(
            f"\n[A* ({nodes_processed_count})] Nodo C estratto da Open List ({len(open_list)} rimasti): {current_C_node}")

        if current_C_full_key in closed_list:
            closed_g = closed_list[current_C_full_key].g_cost
            current_g = current_C_node.g_cost
            if closed_g <= current_g:
                d_print(
                    f"  [A*] Nodo C {current_C_node.get_state_tuple()} (key: {current_C_full_key}) già in Closed List con costo ({closed_g}) <= costo corrente ({current_g}). Salto.")
                continue

        # Risoluzione del nodo C se è una foglia e la sua azione non è ancora stata definita
        if current_C_node.action_taken_to_create_this_node is None:
            owned_match = None
            for pkm in owned_pokemon_list:
                if pkm.id not in current_C_node.used_owned_pokemon_ids and \
                        pkm.species == current_C_node.species and \
                        current_C_node.ivs.issubset(pkm.ivs) and \
                        (current_C_node.nature == "NEUTRAL" or current_C_node.nature == pkm.nature):
                    owned_match = pkm;
                    break

            if owned_match:
                # This node can be fulfilled by an owned Pokemon
                current_C_node.g_cost = 0  # Cost is 0 for using an owned Pokemon
                current_C_node.used_owned_pokemon_ids = current_C_node.used_owned_pokemon_ids.union(
                    {owned_match.id})
                current_C_node.action_taken_to_create_this_node = {'type': 'owned', 'pokemon_id': owned_match.id,
                                                                   'pokemon_object': owned_match}
                d_print(
                    f"  [A*] Nodo C {current_C_node.get_state_tuple()} (key: {current_C_node.get_full_state_tuple_for_closed_list()}) RISOLTO come 'owned', g_cost=0")

            # MODIFIED BLOCK: If not an owned_match, check if it's a buyable base Pokemon
            else:  # No owned match found, try to buy if it's a base Pokemon
                is_buyable_base = (not current_C_node.ivs and current_C_node.nature == "NEUTRAL") or \
                                  (len(current_C_node.ivs) == 1 and current_C_node.nature == "NEUTRAL") or \
                                  (not current_C_node.ivs and current_C_node.nature != "NEUTRAL") or \
                                  (len(current_C_node.ivs) == 1 and current_C_node.nature != "NEUTRAL") # Added: 1 IV + Specific Nature
                if is_buyable_base:
                    current_C_node.g_cost = 1  # Cost is 1 for buying a base Pokemon
                    current_C_node.action_taken_to_create_this_node = {'type': 'bought_base',
                                                                       'species': current_C_node.species,
                                                                       'ivs': set(current_C_node.ivs),
                                                                       'nature': current_C_node.nature}
                    d_print(
                        f"  [A*] Nodo C {current_C_node.get_state_tuple()} (key: {current_C_full_key}) RISOLTO come 'bought_base', g_cost=1")
            # END OF MODIFIED BLOCK

        final_key_for_closed_list = current_C_node.get_full_state_tuple_for_closed_list()
        closed_list[final_key_for_closed_list] = current_C_node
        d_print(
            f"  [A*] Nodo C {current_C_node.get_state_tuple()} (key: {final_key_for_closed_list}) aggiunto/aggiornato in Closed List. g={current_C_node.g_cost}")

        if current_C_node.g_cost != float('inf'):
            # Check if the current node being processed is the START_NODE (our ultimate goal)
            # And if its g_cost is now finite, meaning a complete path to it has been found.
            # The start_node's full key needs to match the current_C_node's full key
            # This check needs to compare the *current state of current_C_node* with the *initial state of start_node*
            # However, the start_node itself might have its used_owned_ids set updated if it was resolved directly.
            # The most reliable check is if current_C_node represents the target species, IVs, and nature,
            # AND its g_cost is finite. The used_owned_ids for the start_node when it's *resolved* is what matters.

            # If the current_C_node *is* the start_node (by its state tuple and potentially used_ids if it was resolved directly)
            # and its cost is finite, we found a plan.
            # The start_node's *initial* full key (with empty used_ids) might differ from its *final* full key if it's resolved.
            # We are looking for *any* version of the start_node (potentially with different used_ids combinations)
            # that has a finite cost.

            # The critical check: is current_C_node (which is now in closed_list) our target Pokemon?
            if (current_C_node.species == start_node.species and
                    current_C_node.ivs == start_node.ivs and
                    current_C_node.nature == start_node.nature):
                # This means we have found a way to produce the target Pokemon.
                # The current_C_node IS the (or a version of the) start_node, but resolved.
                d_print(
                    f"[A*] Target finale {start_node.get_state_tuple()} (come {current_C_node.get_state_tuple()} con used_ids {current_C_node.used_owned_pokemon_ids}) FINALIZZATO con g_cost finito ({current_C_node.g_cost}). Piano trovato!")
                return reconstruct_plan(current_C_node, target_gender, {p.id: p for p in owned_pokemon_list},
                                        closed_list)

            d_print(
                f"  [A*] Propagazione aggiornamento costo da NODO ORA IN CLOSED {current_C_node.get_state_tuple()} (g={current_C_node.g_cost})")
            propagate_cost_update_to_children_in_plan(current_C_node, open_list, open_list_map, closed_list,
                                                      owned_pokemon_list, start_node)

        is_leaf_node_for_expansion_check = False
        if current_C_node.action_taken_to_create_this_node:
            if current_C_node.action_taken_to_create_this_node.get('type') in ('owned', 'bought_base'):
                is_leaf_node_for_expansion_check = True

        if is_leaf_node_for_expansion_check:
            d_print(
                f"  [A*] Nodo {current_C_node.get_state_tuple()} (key: {final_key_for_closed_list}) è una foglia, non espandere ulteriormente.")
            continue

        if current_C_node.depth >= max_depth:
            d_print(
                f"  [A*] Raggiunta profondità massima ({max_depth}) per {current_C_node.get_state_tuple()}. Salto espansione.");
            continue

        d_print(
            f"  [A*] Nodo C {current_C_node.get_state_tuple()} (g={current_C_node.g_cost}) deve essere generato (non è foglia). Espansione...")
        if not current_C_node.parent_options_for_this_node:
            current_C_node.parent_options_for_this_node = generate_breeding_options_for_child(current_C_node)

        if not current_C_node.parent_options_for_this_node:
            # If this node is the start_node itself and has no breeding options, it's impossible if not base
            is_start_node_state = (current_C_node.species == start_node.species and
                                   current_C_node.ivs == start_node.ivs and
                                   current_C_node.nature == start_node.nature)
            if is_start_node_state:
                d_print(
                    f"[A*] Target finale ({start_node.get_state_tuple()}) non è base/owned e non ha opzioni di breeding. Impossibile.")
                return None  # Cannot make the target

        for option in current_C_node.parent_options_for_this_node:
            p1_spec, p2_spec = option['p1_spec'], option['p2_spec']
            d_print(
                f"    [A*] Opzione per C: P1_spec={p1_spec}, P2_spec={p2_spec}, Items=({option['item1']},{option['item2']})")

            for parent_spec, parent_role_for_child in [(p1_spec, 'p1'), (p2_spec, 'p2')]:
                parent_species = parent_spec['species']
                parent_ivs = frozenset(parent_spec['ivs'])
                parent_nature = parent_spec['nature']
                # Parents inherit the used_owned_ids from the child they are trying to create (current_C_node)
                # because if current_C_node used certain owned Pokemon, its parents cannot re-use them for *their own* resolution.
                parent_used_ids = frozenset(current_C_node.used_owned_pokemon_ids)
                parent_P_full_key = (parent_species, parent_ivs, parent_nature, parent_used_ids)

                actual_parent_P_node: Optional[BreedingNode] = None

                if parent_P_full_key in open_list_map:
                    actual_parent_P_node = open_list_map[parent_P_full_key]
                    d_print(
                        f"      [A*] Genitore P {actual_parent_P_node.get_state_tuple()} (key: {parent_P_full_key}) trovato in open_list_map.")
                elif parent_P_full_key in closed_list:
                    actual_parent_P_node = closed_list[parent_P_full_key]
                    d_print(
                        f"      [A*] Genitore P {actual_parent_P_node.get_state_tuple()} (key: {parent_P_full_key}) trovato in closed_list.")

                if actual_parent_P_node is None:
                    actual_parent_P_node = BreedingNode(
                        species=parent_species, ivs=parent_ivs, nature=parent_nature,
                        g_cost=float('inf'), depth=current_C_node.depth + 1,
                        used_owned_ids=parent_used_ids  # Initialize with child's used IDs
                    )
                    actual_parent_P_node.h_cost = calculate_heuristic(actual_parent_P_node, owned_pokemon_list)
                    d_print(
                        f"      [A*] Creato NUOVO genitore P istanza {actual_parent_P_node.get_state_tuple()} (key: {parent_P_full_key}).")

                is_already_child = any(
                    child_node_in_list.get_full_state_tuple_for_closed_list() == current_C_full_key and opt_in_list == option
                    for child_node_in_list, opt_in_list in actual_parent_P_node.children_in_plan_this_node_is_parent_for
                )
                if not is_already_child:
                    actual_parent_P_node.children_in_plan_this_node_is_parent_for.append((current_C_node, option))
                    d_print(
                        f"        -> Registrato {current_C_node.get_state_tuple()} (key {current_C_full_key}) come figlio di {actual_parent_P_node.get_state_tuple()} (key {parent_P_full_key})")

                add_to_open = True
                if parent_P_full_key in closed_list:  # Check if this *exact* parent node (with these used_ids) is closed
                    if closed_list[
                        parent_P_full_key].g_cost <= actual_parent_P_node.g_cost:  # And has a better or equal cost
                        add_to_open = False

                if add_to_open and parent_P_full_key not in open_list_map:
                    # Only add to open list if not already there with this exact key
                    d_print(
                        f"      [A*] Aggiungo genitore P {actual_parent_P_node.get_state_tuple()} (key: {parent_P_full_key}) a Open List.")
                    heapq.heappush(open_list, actual_parent_P_node)
                    open_list_map[parent_P_full_key] = actual_parent_P_node
                elif parent_P_full_key in open_list_map:
                    # If it's already in open_list_map, ensure we have the best g_cost reference
                    # This scenario should ideally be handled by propagate_cost_update if a better path to this parent is found later.
                    # For now, if it's already there, we assume it's being handled or will be.
                    d_print(
                        f"      [A*] Genitore P {actual_parent_P_node.get_state_tuple()} (key: {parent_P_full_key}) già in open_list_map. Non ri-aggiunto.")

                elif not add_to_open:
                    d_print(
                        f"      [A*] Genitore P {actual_parent_P_node.get_state_tuple()} (key: {parent_P_full_key}) è in closed_list con costo migliore/uguale. Non aggiunto a Open.")

    d_print(f"[A*] Fine ricerca. Nodi processati: {nodes_processed_count}. Open list vuota o max nodi raggiunti.")

    # After the loop, check if the start_node (target) was ever resolved with a finite cost.
    # Iterate through all versions of the start_node state in the closed_list
    # (differing by used_owned_pokemon_ids)
    best_resolved_start_node = None
    for key, node_in_closed in closed_list.items():
        if (node_in_closed.species == start_node.species and
                node_in_closed.ivs == start_node.ivs and
                node_in_closed.nature == start_node.nature and
                node_in_closed.g_cost != float('inf')):
            if best_resolved_start_node is None or node_in_closed.g_cost < best_resolved_start_node.g_cost:
                best_resolved_start_node = node_in_closed
            # If costs are equal, prefer one with fewer used owned IDs as a tie-breaker (implicitly handled by A* if h_cost is good)
            # Or prefer one with shallower depth if costs are equal.
            elif node_in_closed.g_cost == best_resolved_start_node.g_cost:
                if len(node_in_closed.used_owned_pokemon_ids) < len(best_resolved_start_node.used_owned_pokemon_ids):
                    best_resolved_start_node = node_in_closed
                elif len(node_in_closed.used_owned_pokemon_ids) == len(
                        best_resolved_start_node.used_owned_pokemon_ids) and node_in_closed.depth < best_resolved_start_node.depth:
                    best_resolved_start_node = node_in_closed

    if best_resolved_start_node:
        d_print(
            f"[A*] Target finale ({best_resolved_start_node.get_state_tuple()} con used_ids {best_resolved_start_node.used_owned_pokemon_ids}) trovato nella closed list con g_cost={best_resolved_start_node.g_cost}. Ricostruzione piano...")
        return reconstruct_plan(best_resolved_start_node, target_gender, {p.id: p for p in owned_pokemon_list},
                                closed_list)

    d_print("[A*] Target finale non trovato con costo finito.")
    return None


def test_4iv_plus_nature_plan():
    """
    Tests the breeding plan generation for a 4IV Charizard with a specific nature,
    leveraging the 'buy 1 IV + Nature' logic.
    """
    print("\n--- Esecuzione test_4iv_plus_nature_plan ---")
    # global DEBUG_ASTAR
    # original_debug_astar = DEBUG_ASTAR
    # DEBUG_ASTAR = False  # Disable verbose A* logging for this test

    # Reset Pokemon ID counter for consistent IDs if tests are run multiple times in same session (if needed)
    Pokemon._id_counter = 0

    target_species = "Charizard"
    target_ivs = {"PS", "ATK", "DEF", "SPE"}
    target_nature = "Adamant"
    target_gender = "Maschio" # Gender for the final Pokemon

    owned_pokemon = [
        Pokemon("Charizard", {"PS"}, "Adamant", "Maschio", name="OwnedAdaPS", is_owned=True, source_info="OwnedInitial1"),
        Pokemon("Charizard", {"ATK", "PS"}, "NEUTRAL", "Maschio", name="OwnedNeutAtkPS", is_owned=True, source_info="OwnedInitial2")
    ]
    # Manually assign IDs for very precise test control if required, though automatic assignment is usually fine.
    # owned_pokemon[0].id = 0
    # owned_pokemon[1].id = 1
    # Pokemon._id_counter = 2 # Ensure next auto-IDs don't collide if more Pokemon are created manually

    print(f"Target: {target_species} ({target_gender}), Nature: {target_nature}, IVs: {target_ivs}")
    print("Owned Pokémon:")
    for p in owned_pokemon:
        print(f"  - {p}")

    plan = find_optimal_breeding_plan(
        target_species=target_species,
        target_ivs=target_ivs,
        target_nature=target_nature,
        target_gender=target_gender,
        owned_pokemon_list=owned_pokemon,
        max_depth=10, # Default max_depth
        max_nodes_to_explore=100000 # Default max_nodes
    )

    if plan:
        print("\n[SUCCESS] Piano di breeding trovato!")
        print(f"Numero totale di passi: {len(plan)}")
        final_pokemon_in_plan = plan[-1].child
        print(f"Costo totale stimato (g_cost del nodo finale): {final_pokemon_in_plan.source_info}") # g_cost is in source_info for target

        # Basic check: The final Pokemon in the plan should match the target specs
        assert final_pokemon_in_plan.species == target_species
        assert final_pokemon_in_plan.nature == target_nature
        assert final_pokemon_in_plan.ivs == target_ivs
        # Gender check might be more complex if the plan involves Dittos and gender assignment rules
        # For this specific test, we expect the target gender.
        if target_species.lower() != "ditto": # Dittos are genderless
             assert final_pokemon_in_plan.gender == target_gender


        print("\Dettagli del Piano:")
        for step in plan:
            print(step)
    else:
        print("\n[FAILURE] Nessun piano di breeding trovato.")

    assert plan is not None, "Il piano di breeding non dovrebbe essere None"

    # DEBUG_ASTAR = original_debug_astar # Restore original A* debug state
    print("--- Fine test_4iv_plus_nature_plan ---\n")


if __name__ == "__main__":
    # Example of how to run the test
    # You might want to load POKEMON_EGG_GROUPS_RAW here if it's not loaded globally
    # or ensure it's loaded before find_optimal_breeding_plan is called.
    # Global loading at the top of the script is typical.
    if not POKEMON_EGG_GROUPS_RAW:
        print("Dati Pokémon non caricati. Caricamento in corso...")
        POKEMON_EGG_GROUPS_RAW = load_pokemon_data()
        if not POKEMON_EGG_GROUPS_RAW:
            print("ERRORE: Impossibile caricare i dati dei Pokémon. Test annullato.")
            exit(1)
        # Re-initialize ALL_POKEMON_NAMES if necessary, though it's not directly used by the algorithm itself
        ALL_POKEMON_NAMES = sorted([name.capitalize() for name in POKEMON_EGG_GROUPS_RAW.keys()])


    test_4iv_plus_nature_plan()
