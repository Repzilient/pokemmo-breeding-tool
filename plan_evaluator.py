import copy
import itertools
from typing import List, Dict, Optional, Any, Tuple, Set, Union

from structures import PianoCompleto, PokemonRichiesto, PokemonPosseduto, PianoValutato

class PlanEvaluator:
    """
    A comprehensive and robust class to evaluate breeding plans.
    This version correctly merges the full-tree analysis with the user-defined
    "most efficient match" rule.
    """

    def __init__(self, piano: PianoCompleto, pokemon_posseduti: List[PokemonPosseduto]):
        self.piano = piano
        self.pokemon_posseduti = pokemon_posseduti
        self.legenda = piano.legenda_ruoli
        # Maps id(child_obj) to list of parent SlotIDs (strings)
        self._child_to_parents_map: Dict[int, List[str]] = {}
        # Maps SlotID (str) to ObjectID (int) required at that slot
        self._slot_to_req_obj_map: Dict[str, int] = {}

    def _get_slot_id(self, acc_id: int, side: int) -> str:
        """Generates a unique slot ID for a requirement in a coupling."""
        return f"{acc_id}_{side}"

    def _build_tree_maps(self):
        """Creates a map to find the parents of any child node in the tree."""
        for livello in self.piano.livelli:
            for acc in livello.accoppiamenti:
                child_id = id(acc.figlio)
                acc_id = id(acc)
                # Map the child OBJECT to the SLOTS that produce it
                parent1_slot = self._get_slot_id(acc_id, 1)
                parent2_slot = self._get_slot_id(acc_id, 2)
                self._child_to_parents_map[child_id] = [parent1_slot, parent2_slot]

                # Also map slots to their required objects
                self._slot_to_req_obj_map[parent1_slot] = id(acc.genitore1)
                self._slot_to_req_obj_map[parent2_slot] = id(acc.genitore2)

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
                acc_id = id(acc)
                # Use Slot ID instead of Object ID to identify requirements
                potential_reqs.append({
                    'req': acc.genitore1,
                    'id': self._get_slot_id(acc_id, 1),
                    'obj_id': id(acc.genitore1),
                    'level': livello.livello_id
                })
                potential_reqs.append({
                    'req': acc.genitore2,
                    'id': self._get_slot_id(acc_id, 2),
                    'obj_id': id(acc.genitore2),
                    'level': livello.livello_id
                })

        # Ordina i requisiti per livello (dal più alto al più basso) e complessità
        potential_reqs.sort(key=lambda item: (item['level'], len(item['req'].ruoli_iv), item['req'].ruolo_natura is not None), reverse=True)

        fulfilled_slot_ids: Set[str] = set()

        for item in potential_reqs:
            slot_id = item['id']
            if slot_id in fulfilled_slot_ids:
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

            # Map SlotID -> PokemonID
            piano_valutato.mappa_assegnazioni[slot_id] = best_pokemon_assegnato.id_utente # type: ignore

            posseduti_disponibili.remove(best_pokemon_assegnato)

            # Recursive pruning implementation:
            # We already handled the current assignment (slot_id).
            fulfilled_slot_ids.add(slot_id)

            # Now we prune parents of the object required at this slot.
            q_objs = [item['obj_id']]
            while q_objs:
                curr_obj_id = q_objs.pop(0)
                if curr_obj_id in self._child_to_parents_map:
                    parent_slots = self._child_to_parents_map[curr_obj_id]
                    for ps in parent_slots:
                        if ps not in fulfilled_slot_ids:
                            fulfilled_slot_ids.add(ps)
                            # Find the object required at parent slot 'ps' to continue recursion
                            if ps in self._slot_to_req_obj_map:
                                q_objs.append(self._slot_to_req_obj_map[ps])

        return piano_valutato


def valuta_piani(piani_generati: List[PianoCompleto], pokemon_posseduti: List[PokemonPosseduto]) -> List[PianoValutato]:
    """
    Main function to orchestrate the evaluation of all plans.
    """
    piani_valutati = []
    for piano in piani_generati:
        evaluator = PlanEvaluator(piano, list(pokemon_posseduti))
        piano_valutato = evaluator.evaluate()
        piani_valutati.append(piano_valutato)

    piani_valutati.sort(key=lambda p: p.punteggio, reverse=True)
    return piani_valutati
