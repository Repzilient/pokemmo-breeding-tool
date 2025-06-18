import copy
import itertools
from typing import List, Dict, Optional, Any, Tuple, Set

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
        self._child_to_parents_map: Dict[int, List[int]] = {}

    def _build_tree_maps(self):
        """Creates a map to find the parents of any child node in the tree."""
        for livello in self.piano.livelli:
            for acc in livello.accoppiamenti:
                self._child_to_parents_map[id(acc.figlio)] = [id(acc.genitore1), id(acc.genitore2)]

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
        for l_idx, livello in enumerate(self.piano.livelli):
            for a_idx, acc in enumerate(livello.accoppiamenti):
                potential_reqs.append({'slot': (l_idx, a_idx, 1), 'req': acc.genitore1, 'id': id(acc.genitore1), 'level': l_idx})
                potential_reqs.append({'slot': (l_idx, a_idx, 2), 'req': acc.genitore2, 'id': id(acc.genitore2), 'level': l_idx})
        
        potential_reqs.sort(key=lambda item: (item['level'], len(item['req'].ruoli_iv), item['req'].ruolo_natura is not None), reverse=True)

        fulfilled_req_ids: Set[int] = set()

        for item in potential_reqs:
            req_id = item['id']
            if req_id in fulfilled_req_ids:
                continue

            richiesto = item['req']
            
            # Find all valid candidates and rank them
            candidati_validi = []
            for candidato in posseduti_disponibili:
                if self._is_valid_candidate(richiesto, candidato):
                    rank = self._rank_candidate(richiesto, candidato)
                    candidati_validi.append({'pokemon': candidato, 'rank': rank})
            
            if not candidati_validi:
                continue

            # Choose the best candidate (lowest rank)
            candidati_validi.sort(key=lambda x: x['rank'])
            best_candidate = candidati_validi[0]
            best_pokemon_assegnato = best_candidate['pokemon']
            
            # Assign the best candidate
            score = self._calcola_punteggio_match(richiesto, best_pokemon_assegnato)
            piano_valutato.punteggio += score
            piano_valutato.pokemon_usati.add(best_pokemon_assegnato.id_utente)
            piano_valutato.mappa_assegnazioni[item['slot']] = best_pokemon_assegnato.id_utente
            posseduti_disponibili.remove(best_pokemon_assegnato)

            # Prune ancestors
            q = [req_id]
            while q:
                req_id_to_prune = q.pop(0)
                if req_id_to_prune not in fulfilled_req_ids:
                    fulfilled_req_ids.add(req_id_to_prune)
                    if req_id_to_prune in self._child_to_parents_map:
                        q.extend(self._child_to_parents_map[req_id_to_prune])
        
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
