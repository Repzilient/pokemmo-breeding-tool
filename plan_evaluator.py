import copy
import itertools
from typing import List, Dict, Optional, Any, Tuple, Set

from structures import PianoCompleto, PokemonRichiesto, PokemonPosseduto, PianoValutato
from price_manager import PriceManager

class PlanEvaluator:
    """
    A comprehensive and robust class to evaluate breeding plans.
    """

    def __init__(self, piano: PianoCompleto, pokemon_posseduti: List[PokemonPosseduto], price_manager: Optional[PriceManager] = None, target_species: str = "Ditto", pokemon_data: Dict = {}, target_nature: Optional[str] = None):
        self.piano = piano
        self.pokemon_posseduti = pokemon_posseduti
        self.legenda = piano.legenda_ruoli
        self.price_manager = price_manager
        self.target_species = target_species
        self.pokemon_data = pokemon_data
        self.target_nature = target_nature
        self._child_to_parents_map: Dict[int, List[int]] = {}
        self._node_map: Dict[int, PokemonRichiesto] = {}

    def _build_tree_maps(self):
        """Creates a map to find the parents of any child node in the tree."""
        for livello in self.piano.livelli:
            for acc in livello.accoppiamenti:
                self._child_to_parents_map[id(acc.figlio)] = [id(acc.genitore1), id(acc.genitore2)]
                self._node_map[id(acc.genitore1)] = acc.genitore1
                self._node_map[id(acc.genitore2)] = acc.genitore2
                self._node_map[id(acc.figlio)] = acc.figlio

    def _is_valid_candidate(self, richiesto: PokemonRichiesto, posseduto: PokemonPosseduto) -> bool:
        ivs_reali_richieste = {self.legenda.get(r) for r in richiesto.ruoli_iv if r in self.legenda}
        if not ivs_reali_richieste.issubset(set(posseduto.ivs)):
            return False

        natura_reale_richiesta = self.legenda.get(richiesto.ruolo_natura) if richiesto.ruolo_natura in self.legenda else None
        if natura_reale_richiesta is not None and posseduto.natura != natura_reale_richiesta:
            return False

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

    def calculate_cost_recursive(self, node_id: int, piano_valutato: PianoValutato, is_species_mandatory: bool) -> int:
        """
        Calculates the cost to obtain the Pokemon at node_id.
        is_species_mandatory: If True, this Pokemon MUST be the target species (Female).
        """
        # 1. Check if Owned
        if node_id in piano_valutato.mappa_assegnazioni:
            return 0

        node = self._node_map.get(node_id)
        if not node:
             return 999999

        # 2. Determine Requirements (Specific Stat Name or Nature)
        iv_roles = node.ruoli_iv
        nature_role = node.ruolo_natura

        # Translate roles to real names using legenda
        required_stats = [self.legenda.get(r) for r in iv_roles if r in self.legenda]
        required_nature = self.legenda.get(nature_role) if nature_role in self.legenda else None

        # 3. Base Case: Leaf Node (No parents in plan) or Hole
        if node_id not in self._child_to_parents_map:
            if self.price_manager is None:
                return 999999

            # Determine what we are buying based on what is required
            # A leaf usually has 1 IV OR 1 Nature. If it has more, it's a complex leaf (should be rare in generated plans, usually leaves are atomic).
            # If multiple stats required, we assume we buy a pokemon having ALL (which isn't really supported by the atomic price list),
            # OR we assume the plan generator creates atomic leaves.
            # Generator logic usually creates 1IV leaves.

            # Identify the "Primary" requirement for pricing
            # If it has an IV, we use that Stat Name.
            # If it has only Nature, we use "Natura".

            primary_stat_key = None
            if required_stats:
                primary_stat_key = required_stats[0] # Assume single IV leaf
            elif required_nature:
                primary_stat_key = "Natura"
            else:
                # Should not happen for a required leaf, but if so (Trash mon)
                primary_stat_key = "Base"

            cost = 999999999

            # Calculate Cost Options
            if is_species_mandatory:
                # Must be Female Species
                c = self.price_manager.get_price(primary_stat_key, "Specie", "F")
                cost = min(cost, c)
            else:
                # Can be Male Specie, Male EggGroup, or Ditto
                c_specie_m = self.price_manager.get_price(primary_stat_key, "Specie", "M")
                c_group_m = self.price_manager.get_price(primary_stat_key, "EggGroup", "M")

                # For Ditto, gender is usually X.
                c_ditto = self.price_manager.get_price(primary_stat_key, "Ditto", "X")

                cost = min(cost, c_specie_m, c_group_m, c_ditto)

            return cost

        # 4. Recursive Step: Breeding
        parents = self._child_to_parents_map[node_id]
        p1_id, p2_id = parents[0], parents[1]

        # Breeding Fee
        fee = 20000
        if required_nature is not None:
             # If the child requires a specific nature (carried from parents), use Everstone cost
             fee = 15000

        # Optimization: Swap genders
        cost_A = self.calculate_cost_recursive(p1_id, piano_valutato, True) + \
                 self.calculate_cost_recursive(p2_id, piano_valutato, False)

        cost_B = self.calculate_cost_recursive(p2_id, piano_valutato, True) + \
                 self.calculate_cost_recursive(p1_id, piano_valutato, False)

        return fee + min(cost_A, cost_B)

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
                potential_reqs.append({'req': acc.genitore1, 'id': id(acc.genitore1), 'level': livello.livello_id})
                potential_reqs.append({'req': acc.genitore2, 'id': id(acc.genitore2), 'level': livello.livello_id})

        potential_reqs.sort(key=lambda item: (item['level'], len(item['req'].ruoli_iv), item['req'].ruolo_natura is not None), reverse=True)

        fulfilled_req_ids: Set[int] = set()

        for item in potential_reqs:
            req_id = item['id']
            if req_id in fulfilled_req_ids:
                continue

            richiesto = item['req']

            candidati_validi = []
            for candidato in posseduti_disponibili:
                if self._is_valid_candidate(richiesto, candidato):
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
             piano_valutato.costo_totale = self.calculate_cost_recursive(id(final_node), piano_valutato, True)


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
