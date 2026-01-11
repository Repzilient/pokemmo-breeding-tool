import copy
import itertools
from typing import List, Dict, Optional, Any, Tuple, Set
from collections import defaultdict

from structures import PianoCompleto, PokemonRichiesto, PokemonPosseduto, PianoValutato
from price_manager import PriceManager
from gender_helper import GenderHelper

class PlanEvaluator:
    """
    A comprehensive and robust class to evaluate breeding plans.
    """

    def __init__(self, piano: PianoCompleto, pokemon_posseduti: List[PokemonPosseduto], price_manager: Optional[PriceManager] = None, target_species: str = "Ditto", pokemon_data: Dict = {}, target_nature: Optional[str] = None, gender_helper: Optional[GenderHelper] = None):
        self.piano = piano
        self.pokemon_posseduti = pokemon_posseduti
        self.legenda = piano.legenda_ruoli
        self.price_manager = price_manager
        self.target_species = target_species
        self.pokemon_data = pokemon_data
        self.target_nature = target_nature
        self.gender_helper = gender_helper
        self._child_to_parents_map: Dict[int, List[int]] = {}
        self._node_map: Dict[int, PokemonRichiesto] = {}

    def _ensure_unique_nodes(self):
        """
        Traverses the plan and ensures that every leaf (base parent) is a unique object instance.
        This prevents conflicting decision logic when a single requirement object is reused
        across multiple branches of the breeding tree.

        CRITICAL: Only clones external leaves if they are SHARED (ref_count > 1).
        This ensures idempotency: if the plan is already a Tree (unique leaves), IDs are preserved.
        """
        generated_ids = set()
        ref_counts = defaultdict(int)

        # 1. Identify generated nodes and count references
        for livello in self.piano.livelli:
            for acc in livello.accoppiamenti:
                generated_ids.add(id(acc.figlio))
                ref_counts[id(acc.genitore1)] += 1
                ref_counts[id(acc.genitore2)] += 1

        # 2. Uniquify shared external leaves
        for livello in self.piano.livelli:
            for acc in livello.accoppiamenti:
                # Handle Genitore 1
                if id(acc.genitore1) not in generated_ids:
                    # External Leaf. Only clone if shared.
                    if ref_counts[id(acc.genitore1)] > 1:
                        acc.genitore1 = copy.copy(acc.genitore1)

                # Handle Genitore 2
                if id(acc.genitore2) not in generated_ids:
                    if ref_counts[id(acc.genitore2)] > 1:
                        acc.genitore2 = copy.copy(acc.genitore2)

    def _build_tree_maps(self):
        """Creates a map to find the parents of any child node in the tree."""
        # Fix: Ensure nodes are unique before mapping
        self._ensure_unique_nodes()

        for livello in self.piano.livelli:
            for acc in livello.accoppiamenti:
                self._child_to_parents_map[id(acc.figlio)] = [id(acc.genitore1), id(acc.genitore2)]
                self._node_map[id(acc.genitore1)] = acc.genitore1
                self._node_map[id(acc.genitore2)] = acc.genitore2
                self._node_map[id(acc.figlio)] = acc.figlio

    def _is_valid_candidate(self, richiesto: PokemonRichiesto, posseduto: PokemonPosseduto, required_gender: Optional[str] = None) -> bool:
        ivs_reali_richieste = {self.legenda.get(r) for r in richiesto.ruoli_iv if r in self.legenda}
        if not ivs_reali_richieste.issubset(set(posseduto.ivs)):
            return False

        natura_reale_richiesta = self.legenda.get(richiesto.ruolo_natura) if richiesto.ruolo_natura in self.legenda else None
        if natura_reale_richiesta is not None and posseduto.natura != natura_reale_richiesta:
            return False

        # Gender Check
        if required_gender and posseduto.sesso:
             # Standard roles: Genitore 1 (Mother) -> Needs F; Genitore 2 (Father) -> Needs M.
             if required_gender == "F":
                 if posseduto.sesso not in ["F", "Genderless"]: return False
             elif required_gender == "M":
                 if posseduto.sesso not in ["M", "Genderless"]: return False

        return True

    def _rank_candidate(self, richiesto: PokemonRichiesto, posseduto: PokemonPosseduto) -> Tuple[int, int]:
        ivs_reali_richieste = {self.legenda.get(r) for r in richiesto.ruoli_iv if r in self.legenda}
        iv_waste = len(posseduto.ivs) - len(ivs_reali_richieste)

        natura_reale_richiesta = self.legenda.get(richiesto.ruolo_natura) if richiesto.ruolo_natura in self.legenda else None
        nature_waste = 1 if natura_reale_richiesta is None and posseduto.natura is not None else 0

        return (iv_waste, nature_waste)

    def _calcola_punteggio_match(self, richiesto: PokemonRichiesto, posseduto: PokemonPosseduto) -> float:
        punteggio = 10.0
        punteggio += len(richiesto.ruoli_iv) * 5.0

        natura_reale_richiesta = self.legenda.get(richiesto.ruolo_natura) if richiesto.ruolo_natura in self.legenda else None
        if natura_reale_richiesta is not None and posseduto.natura == natura_reale_richiesta:
            punteggio += 15.0

        iv_waste, _ = self._rank_candidate(richiesto, posseduto)
        if iv_waste == 0:
            punteggio += 5.0
        else:
            punteggio -= iv_waste * 2.0

        return punteggio

    def calculate_cost_recursive(self, node_id: int, piano_valutato: PianoValutato, is_species_mandatory: bool) -> Tuple[int, Dict[int, str]]:
        """
        Calculates the cost to obtain the Pokemon at node_id.
        Returns (Cost, Decisions_Map).
        is_species_mandatory: If True, this Pokemon MUST be the target species (Female).
        """
        # 1. Check if Owned
        if node_id in piano_valutato.mappa_assegnazioni:
            return 0, {}

        node = self._node_map.get(node_id)
        if not node:
             return 999999999, {}

        # 2. Determine Requirements
        iv_roles = node.ruoli_iv
        nature_role = node.ruolo_natura

        required_stats = [self.legenda.get(r) for r in iv_roles if r in self.legenda]
        required_nature = self.legenda.get(nature_role) if nature_role in self.legenda else None

        # 3. Base Case: Leaf Node or Hole
        if node_id not in self._child_to_parents_map:
            if self.price_manager is None:
                return 999999999, {}

            primary_stat_key = None
            if required_stats:
                primary_stat_key = required_stats[0]
            elif required_nature:
                primary_stat_key = "Natura"
            else:
                primary_stat_key = "Base"

            cost = 999999999
            decision_desc = "Sconosciuto"

            egg_groups = self.pokemon_data.get(self.target_species, [])
            # Usa il primo gruppo uova se disponibile, altrimenti "Mostro"
            group_name = egg_groups[0] if egg_groups else "Mostro"

            if is_species_mandatory:
                # Must be Female Species (or target species Genderless/MaleOnly)
                target_type = "Unknown"
                if self.gender_helper:
                    target_type = self.gender_helper.get_gender_ratio_type(self.target_species)

                req_gender_buy = "F"
                if "solo maschio" in target_type: req_gender_buy = "M"
                if "genderless" in target_type or "N/A" in target_type: req_gender_buy = "X"

                # If we need Female, buy Female.
                if req_gender_buy == "F":
                    c = self.price_manager.get_price(primary_stat_key, "Specie", "F")
                    if c < cost:
                        cost = c
                        decision_desc = f"Comprare {self.target_species} ♀\n({primary_stat_key}) - ${c}"
                elif req_gender_buy == "M":
                    c = self.price_manager.get_price(primary_stat_key, "Specie", "M")
                    if c < cost:
                        cost = c
                        decision_desc = f"Comprare {self.target_species} ♂\n({primary_stat_key}) - ${c}"
                else: # Genderless
                    c = self.price_manager.get_price(primary_stat_key, "Specie", "M")
                    if c < cost:
                        cost = c
                        decision_desc = f"Comprare {self.target_species}\n({primary_stat_key}) - ${c}"

            else:
                # Can be Male Helper.
                options = []

                # Option 1: Target Species Male
                c_specie_m = self.price_manager.get_price(primary_stat_key, "Specie", "M")
                options.append((c_specie_m, f"Comprare {self.target_species} ♂\n({primary_stat_key}) - ${c_specie_m}"))

                # Option 2: Egg Group Male (Optimized)
                c_group_m = self.price_manager.get_price(primary_stat_key, "EggGroup", "M")

                # Find optimized species
                optimal_species_name = group_name
                if self.gender_helper:
                    optimal_species_name = self.gender_helper.get_optimal_species_for_egg_group(group_name, "M")

                options.append((c_group_m, f"Comprare {optimal_species_name} ♂\n(EggGroup {group_name}) - ${c_group_m}"))

                # Option 3: Ditto
                c_ditto = self.price_manager.get_price(primary_stat_key, "Ditto", "X")
                options.append((c_ditto, f"Comprare Ditto\n({primary_stat_key}) - ${c_ditto}"))

                # Find min
                options.sort(key=lambda x: x[0])
                cost, decision_desc = options[0]

            return cost, {node_id: decision_desc}

        # 4. Recursive Step: Breeding
        parents = self._child_to_parents_map[node_id]
        p1_id, p2_id = parents[0], parents[1]

        base_fee = 20000
        if required_nature is not None:
             base_fee = 15000

        egg_groups = self.pokemon_data.get(self.target_species, [])
        group_name = egg_groups[0] if egg_groups else "Mostro"

        # Resolve Species for this Node to calculate Gender Fee correctly
        node_species = self.target_species
        if not is_species_mandatory and self.gender_helper:
            # If helper line, use Optimal Species
            node_species = self.gender_helper.get_optimal_species_for_egg_group(group_name, "M")

        # Calculate Gender Selection Fee for THIS node
        required_gender_child = "F" if is_species_mandatory else "M"

        # Check if Target is Genderless/MaleOnly (Edge Case)
        target_type = "Unknown"
        if self.gender_helper:
            target_type = self.gender_helper.get_gender_ratio_type(node_species)

        if "genderless" in target_type: required_gender_child = "X"
        elif "solo maschio" in target_type: required_gender_child = "M"
        elif "solo femmina" in target_type: required_gender_child = "F"

        gender_fee = 0
        if self.gender_helper:
            gender_fee = self.gender_helper.get_gender_selection_cost(node_species, required_gender_child)

        # Recursive Calls
        # Case A: P1=Female(Line), P2=Male(Filler)
        cost_A1, decisions_A1 = self.calculate_cost_recursive(p1_id, piano_valutato, True) # Mother (Species)
        cost_A2, decisions_A2 = self.calculate_cost_recursive(p2_id, piano_valutato, False) # Father (Helper)

        total_A = cost_A1 + cost_A2 + gender_fee

        # Same for B
        cost_B1, decisions_B1 = self.calculate_cost_recursive(p2_id, piano_valutato, True)
        cost_B2, decisions_B2 = self.calculate_cost_recursive(p1_id, piano_valutato, False)
        total_B = cost_B1 + cost_B2 + gender_fee

        if total_A <= total_B:
            decisions = {**decisions_A1, **decisions_A2}
            return base_fee + total_A, decisions
        else:
            decisions = {**decisions_B1, **decisions_B2}
            return base_fee + total_B, decisions

    def evaluate(self) -> PianoValutato:
        """
        Executes the full evaluation (assignments only).
        """
        self._build_tree_maps()
        piano_valutato = PianoValutato(piano_originale=self.piano)
        posseduti_disponibili = list(self.pokemon_posseduti)

        potential_reqs = []
        for livello in self.piano.livelli:
            for acc in livello.accoppiamenti:
                # Genitore 1 is typically Mother (F). Genitore 2 is Father (M).
                potential_reqs.append({'req': acc.genitore1, 'id': id(acc.genitore1), 'level': livello.livello_id, 'gender': 'F'})
                potential_reqs.append({'req': acc.genitore2, 'id': id(acc.genitore2), 'level': livello.livello_id, 'gender': 'M'})

        potential_reqs.sort(key=lambda item: (item['level'], len(item['req'].ruoli_iv), item['req'].ruolo_natura is not None), reverse=True)

        fulfilled_req_ids: Set[int] = set()

        for item in potential_reqs:
            req_id = item['id']
            if req_id in fulfilled_req_ids:
                continue

            richiesto = item['req']
            req_gender = item['gender']

            candidati_validi = []
            for candidato in posseduti_disponibili:
                if self._is_valid_candidate(richiesto, candidato, req_gender):
                    rank = self._rank_candidate(richiesto, candidato)
                    candidati_validi.append({'pokemon': candidato, 'rank': rank})

            if not candidati_validi:
                continue

            candidati_validi.sort(key=lambda x: x['rank'])
            best_candidate = candidati_validi[0]
            best_pokemon_assegnato = best_candidate['pokemon']

            score = self._calcola_punteggio_match(richiesto, best_pokemon_assegnato)
            piano_valutato.punteggio += score
            piano_valutato.pokemon_usati.add(best_pokemon_assegnato.id_utente)
            piano_valutato.mappa_assegnazioni[req_id] = best_pokemon_assegnato.id_utente
            posseduti_disponibili.remove(best_pokemon_assegnato)

            q = [req_id]
            while q:
                req_id_to_prune = q.pop(0)
                if req_id_to_prune not in fulfilled_req_ids:
                    fulfilled_req_ids.add(req_id_to_prune)
                    if req_id_to_prune in self._child_to_parents_map:
                        q.extend(self._child_to_parents_map[req_id_to_prune])

        return piano_valutato

    def update_cost(self, piano_valutato: PianoValutato):
        """
        Runs the cost calculation on an already evaluated plan.
        """
        if self.price_manager and self.piano.livelli:
             final_node = self.piano.livelli[-1].accoppiamenti[0].figlio
             cost, decisions = self.calculate_cost_recursive(id(final_node), piano_valutato, True)
             piano_valutato.costo_totale = cost
             piano_valutato.mappa_acquisti = decisions


def valuta_piani(piani_generati: List[PianoCompleto], pokemon_posseduti: List[PokemonPosseduto]) -> List[PianoValutato]:
    """
    Initial evaluation based only on Owned Pokemon score.
    """
    piani_valutati = []
    for piano in piani_generati:
        evaluator = PlanEvaluator(piano, list(pokemon_posseduti))
        piano_valutato = evaluator.evaluate()
        piani_valutati.append(piano_valutato)

    piani_valutati.sort(key=lambda p: p.punteggio, reverse=True)
    return piani_valutati
