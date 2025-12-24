import copy
import itertools
from typing import List, Dict, Optional, Any, Tuple, Set

from structures import PianoCompleto, PokemonRichiesto, PokemonPosseduto, PianoValutato
from price_manager import PriceManager

class PlanEvaluator:
    """
    A comprehensive and robust class to evaluate breeding plans.
    This version correctly merges the full-tree analysis with the user-defined
    "most efficient match" rule and calculates costs.
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
        """
        Checks if an owned Pokémon is a valid candidate for a requirement.
        It must have AT LEAST the required IVs and the exact Nature if specified.
        """
        ivs_reali_richieste = {self.legenda.get(r) for r in richiesto.ruoli_iv if r in self.legenda}
        if not ivs_reali_richieste.issubset(set(posseduto.ivs)):
            return False

        natura_reale_richiesta = self.legenda.get(richiesto.ruolo_natura) if richiesto.ruolo_natura in self.legenda else None
        if natura_reale_richiesta is not None and posseduto.natura != natura_reale_richiesta:
            return False

        return True

    def _rank_candidate(self, richiesto: PokemonRichiesto, posseduto: PokemonPosseduto) -> Tuple[int, int]:
        """
        Ranks a candidate's efficiency. Lower is better.
        The primary ranking criterion is the number of "wasted" IVs.
        """
        ivs_reali_richieste = {self.legenda.get(r) for r in richiesto.ruoli_iv if r in self.legenda}
        iv_waste = len(posseduto.ivs) - len(ivs_reali_richieste)

        natura_reale_richiesta = self.legenda.get(richiesto.ruolo_natura) if richiesto.ruolo_natura in self.legenda else None
        nature_waste = 1 if natura_reale_richiesta is None and posseduto.natura is not None else 0

        return (iv_waste, nature_waste)

    def _calcola_punteggio_match(self, richiesto: PokemonRichiesto, posseduto: PokemonPosseduto) -> float:
        """Calculates the score for a confirmed assignment, rewarding efficiency."""
        punteggio = 10.0
        punteggio += len(richiesto.ruoli_iv) * 5.0

        natura_reale_richiesta = self.legenda.get(richiesto.ruolo_natura) if richiesto.ruolo_natura in self.legenda else None
        if natura_reale_richiesta is not None and posseduto.natura == natura_reale_richiesta:
            punteggio += 15.0

        iv_waste, _ = self._rank_candidate(richiesto, posseduto)
        if iv_waste == 0:
            punteggio += 5.0  # Higher bonus for perfect IV efficiency
        else:
            punteggio -= iv_waste * 2.0 # Higher penalty for wasting IVs

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
             # Should not happen if build_tree_maps is correct
             return 999999

        # 2. Determine Requirements
        # Note: 'ruoli_iv' are abstract keys (B, G, etc.) mapped in self.legenda
        num_ivs = len(node.ruoli_iv)
        has_nature = node.ruolo_natura is not None

        # Determine Price Type string
        price_type = "Base"
        if num_ivs == 1 and not has_nature:
            price_type = "1IV"
        elif num_ivs == 0 and has_nature:
            price_type = "Solo Natura"
        elif num_ivs == 1 and has_nature:
            price_type = "1IV + Natura"

        # 3. Base Case: Leaf Node (No parents in plan) or Hole
        if node_id not in self._child_to_parents_map:
            # Must Buy
            if self.price_manager is None:
                return 999999

            egg_groups = self.pokemon_data.get(self.target_species, [])
            primary_group = egg_groups[0] if egg_groups else "Mostro" # Fallback

            # Cost if we buy Species (Female usually required for species)
            # User logic: "Femmina determina la specie" -> So if species mandatory, we need Female Species.
            # If species NOT mandatory (Male), we can use EggGroup Male or Ditto.

            cost = 999999999

            if is_species_mandatory:
                # Must be Female Species
                c = self.price_manager.get_price("Specie", self.target_species, "F", price_type)
                cost = min(cost, c)
            else:
                # Can be Male Specie, Male EggGroup, or Ditto
                c_specie_m = self.price_manager.get_price("Specie", self.target_species, "M", price_type)
                c_group_m = self.price_manager.get_price("EggGroup", primary_group, "M", price_type)
                c_ditto = self.price_manager.get_price("Ditto", "Ditto", "X", price_type)

                cost = min(cost, c_specie_m, c_group_m, c_ditto)

            return cost

        # 4. Recursive Step: Breeding
        # Has parents. We are creating this from parents.
        parents = self._child_to_parents_map[node_id]
        p1_id, p2_id = parents[0], parents[1]

        # Breeding Fee
        # Rule: 15k if Nature inherited (Everstone), 20k otherwise (2 Braces)
        # We check if the child has a Nature requirement that matches the Target Nature (implying we are carrying it up).
        # Simplified logic based on prompt: "15.000$ se è necessaria la Pietrastante per la Natura"
        # If this node has a defined Nature role, we assume we are using Everstone.
        fee = 20000
        if has_nature:
            fee = 15000

        # Optimization: We have 2 parents (P1, P2). One must be Female Species (to keep species), one Male Compatible.
        # We don't know which is which in the plan structure, so we calculate both swaps and take min.

        # Case A: P1 is Species(F), P2 is Compatible(M)
        cost_A = self.calculate_cost_recursive(p1_id, piano_valutato, True) + \
                 self.calculate_cost_recursive(p2_id, piano_valutato, False)

        # Case B: P2 is Species(F), P1 is Compatible(M)
        cost_B = self.calculate_cost_recursive(p2_id, piano_valutato, True) + \
                 self.calculate_cost_recursive(p1_id, piano_valutato, False)

        return fee + min(cost_A, cost_B)

    def evaluate(self) -> PianoValutato:
        """
        Executes the full evaluation to find the best set of efficient assignments.
        """
        self._build_tree_maps()
        piano_valutato = PianoValutato(piano_originale=self.piano)
        posseduti_disponibili = list(self.pokemon_posseduti)

        potential_reqs = []
        for livello in self.piano.livelli:
            for acc in livello.accoppiamenti:
                potential_reqs.append({'req': acc.genitore1, 'id': id(acc.genitore1), 'level': livello.livello_id})
                potential_reqs.append({'req': acc.genitore2, 'id': id(acc.genitore2), 'level': livello.livello_id})

        # Ordina i requisiti per livello (dal più alto al più basso) e complessità
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

            # --- MODIFICA CHIAVE ---
            # Assegna il Pokémon usando l'ID univoco del requisito come chiave.
            # Questo è il fix principale.
            score = self._calcola_punteggio_match(richiesto, best_pokemon_assegnato)
            piano_valutato.punteggio += score
            piano_valutato.pokemon_usati.add(best_pokemon_assegnato.id_utente)
            piano_valutato.mappa_assegnazioni[req_id] = best_pokemon_assegnato.id_utente
            posseduti_disponibili.remove(best_pokemon_assegnato)

            # Pruning degli antenati: se copro un figlio, non devo più creare i suoi genitori
            q = [req_id]
            while q:
                req_id_to_prune = q.pop(0)
                if req_id_to_prune not in fulfilled_req_ids:
                    fulfilled_req_ids.add(req_id_to_prune)
                    if req_id_to_prune in self._child_to_parents_map:
                        q.extend(self._child_to_parents_map[req_id_to_prune])

        # --- Calculate Cost ---
        if self.price_manager:
            # Find the root of the tree (Target Pokemon)
            # The piano.livelli[-1].accoppiamenti[0].figlio is usually the final target
            if self.piano.livelli:
                final_node = self.piano.livelli[-1].accoppiamenti[0].figlio
                # We start recursion requiring the final pokemon to be the Target Species
                piano_valutato.costo_totale = self.calculate_cost_recursive(id(final_node), piano_valutato, True)

        return piano_valutato


def valuta_piani(piani_generati: List[PianoCompleto], pokemon_posseduti: List[PokemonPosseduto], price_manager: Optional[PriceManager] = None, target_species: str = "Ditto", pokemon_data: Dict = {}, target_nature: Optional[str] = None) -> List[PianoValutato]:
    """
    Main function to orchestrate the evaluation of all plans.
    """
    piani_valutati = []
    for piano in piani_generati:
        evaluator = PlanEvaluator(piano, list(pokemon_posseduti), price_manager, target_species, pokemon_data, target_nature)
        piano_valutato = evaluator.evaluate()
        piani_valutati.append(piano_valutato)

    # Sort by Punteggio (High to Low), then by Cost (Low to High)
    # Since sort is stable, we sort by Cost first, then by Punteggio
    piani_valutati.sort(key=lambda p: p.costo_totale)
    piani_valutati.sort(key=lambda p: p.punteggio, reverse=True)
    return piani_valutati
