import copy
import itertools
from typing import List, Dict, Optional, Any, Tuple, Set
from collections import defaultdict

from structures import PianoCompleto, PokemonRichiesto, PokemonPosseduto, PianoValutato
from price_manager import PriceManager

class PlanEvaluator:
    """
    A comprehensive and robust class to evaluate breeding plans.
    """

    def __init__(self, piano: PianoCompleto, pokemon_posseduti: List[PokemonPosseduto], price_manager: Optional[PriceManager] = None, target_species: str = "Ditto", pokemon_data: Dict = {}, target_nature: Optional[str] = None, gender_data: Dict = {}):
        self.piano = piano
        self.pokemon_posseduti = pokemon_posseduti
        self.legenda = piano.legenda_ruoli
        self.price_manager = price_manager
        self.target_species = target_species
        self.pokemon_data = pokemon_data
        self.target_nature = target_nature
        self.gender_data = gender_data
        self._child_to_parents_map: Dict[int, List[int]] = {}
        self._node_map: Dict[int, PokemonRichiesto] = {}
        self._mandatory_species_nodes: Set[int] = set()

    def _identify_mandatory_nodes(self):
        if not self.piano.livelli:
            return

        final_node = self.piano.livelli[-1].accoppiamenti[0].figlio
        self._mandatory_species_nodes.add(id(final_node))

        q = [id(final_node)]
        while q:
            curr_id = q.pop(0)
            if curr_id in self._child_to_parents_map:
                parents = self._child_to_parents_map[curr_id]
                gen1_id = parents[0]
                self._mandatory_species_nodes.add(gen1_id)
                q.append(gen1_id)

    def _ensure_unique_nodes(self):
        generated_ids = set()
        ref_counts = defaultdict(int)

        for livello in self.piano.livelli:
            for acc in livello.accoppiamenti:
                generated_ids.add(id(acc.figlio))
                ref_counts[id(acc.genitore1)] += 1
                ref_counts[id(acc.genitore2)] += 1

        for livello in self.piano.livelli:
            for acc in livello.accoppiamenti:
                if id(acc.genitore1) not in generated_ids:
                    if ref_counts[id(acc.genitore1)] > 1:
                        acc.genitore1 = copy.copy(acc.genitore1)
                if id(acc.genitore2) not in generated_ids:
                    if ref_counts[id(acc.genitore2)] > 1:
                        acc.genitore2 = copy.copy(acc.genitore2)

    def _build_tree_maps(self):
        self._ensure_unique_nodes()
        for livello in self.piano.livelli:
            for acc in livello.accoppiamenti:
                self._child_to_parents_map[id(acc.figlio)] = [id(acc.genitore1), id(acc.genitore2)]
                self._node_map[id(acc.genitore1)] = acc.genitore1
                self._node_map[id(acc.genitore2)] = acc.genitore2
                self._node_map[id(acc.figlio)] = acc.figlio

    def _is_valid_candidate(self, richiesto: PokemonRichiesto, posseduto: PokemonPosseduto, req_id: int, role: str) -> bool:
        ivs_reali_richieste = {self.legenda.get(r) for r in richiesto.ruoli_iv if r in self.legenda}
        if not ivs_reali_richieste.issubset(set(posseduto.ivs)):
            return False

        natura_reale_richiesta = self.legenda.get(richiesto.ruolo_natura) if richiesto.ruolo_natura in self.legenda else None
        if natura_reale_richiesta is not None and posseduto.natura != natura_reale_richiesta:
            return False

        if role == 'root' or req_id in self._mandatory_species_nodes:
            if posseduto.specie != self.target_species:
                return False

        elif role == 'gen2' and posseduto.specie != 'Ditto' and posseduto.specie != self.target_species:
             target_groups = self.pokemon_data.get(self.target_species, [])
             candidate_groups = self.pokemon_data.get(posseduto.specie, [])
             if target_groups and candidate_groups:
                 if set(target_groups).isdisjoint(set(candidate_groups)):
                     return False

        if role == 'root':
            return True

        target_gender_type = "maschio e femmina"
        if self.target_species in self.gender_data:
            target_gender_type = self.gender_data[self.target_species].get("gender_type", "maschio e femmina").lower()
        elif "Genderless" in self.pokemon_data.get(self.target_species, []):
             target_gender_type = "genderless"

        p_sesso = posseduto.sesso
        if p_sesso == 'M': p_sesso = 'Maschio'
        if p_sesso == 'F': p_sesso = 'Femmina'

        if "genderless" in target_gender_type:
            if role == 'gen1':
                if p_sesso != 'Genderless':
                     return False
            elif role == 'gen2':
                if posseduto.specie != 'Ditto':
                    return False
        else:
            if role == 'gen1':
                if p_sesso != 'Femmina':
                    return False
            elif role == 'gen2':
                if posseduto.specie == 'Ditto':
                    return True
                if p_sesso != 'Maschio':
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

    def _get_gender_cost(self, gender_role: str) -> int:
        if self.target_species not in self.gender_data:
            return 5000
        data = self.gender_data[self.target_species]
        ratio_str = data.get("gender_ratio", "")
        gender_type = data.get("gender_type", "").lower()
        if "genderless" in gender_type or "solo" in gender_type or "N/A" in ratio_str:
            return 0
        try:
            m_part = ratio_str.split(',')[0].strip()
            percentage = float(m_part.split('%')[0])
        except (ValueError, IndexError):
            return 5000
        if percentage == 50.0:
            return 5000
        elif percentage == 87.5:
            if gender_role == 'F': return 21000
            else: return 5000
        elif percentage == 25.0:
            if gender_role == 'F': return 9000
            else: return 5000
        return 5000

    def _check_owned_ingredient(self, stat_key: str, species_type: str, gender: str) -> bool:
        """
        Checks if the user owns a Pokémon that can serve as this ingredient.
        stat_key: 'PS', 'Attacco', 'Base'
        species_type: 'Specie' (Target), 'EggGroup', 'Ditto'
        gender: 'M', 'F', 'X'
        """
        target_groups = self.pokemon_data.get(self.target_species, [])

        for p in self.pokemon_posseduti:
            # Check Species Compatibility
            is_compatible = False
            if species_type == 'Specie':
                if p.specie == self.target_species: is_compatible = True
            elif species_type == 'Ditto':
                if p.specie == 'Ditto': is_compatible = True
            elif species_type == 'EggGroup':
                # Check egg group overlap
                p_groups = self.pokemon_data.get(p.specie, [])
                if p.specie != 'Ditto' and p_groups and target_groups:
                    if not set(target_groups).isdisjoint(set(p_groups)):
                        is_compatible = True

            if not is_compatible: continue

            # Check Gender
            p_sesso = p.sesso
            if p_sesso == 'M': p_sesso = 'Maschio'
            if p_sesso == 'F': p_sesso = 'Femmina'

            gender_match = False
            if gender == 'X': gender_match = True
            elif gender == 'M' and p_sesso == 'Maschio': gender_match = True
            elif gender == 'F' and p_sesso == 'Femmina': gender_match = True

            if not gender_match: continue

            # Check Stat/Role
            # If stat_key is 'Base', any match is fine (assuming trash is ok)
            # If stat_key is specific (e.g. 'PS'), check IVs
            if stat_key == 'Base':
                return True
            elif stat_key == 'Natura':
                if p.natura == self.target_nature: return True # Assuming target_nature matches requirement context
            elif stat_key in p.ivs:
                return True

        return False

    def _get_price_or_owned(self, stat_key, category, gender) -> int:
        if self._check_owned_ingredient(stat_key, category, gender):
            return 0
        return self.price_manager.get_price(stat_key, category, gender)

    def calculate_cost_recursive(self, node_id: int, piano_valutato: PianoValutato, is_species_mandatory: bool, required_gender: str = 'F') -> Tuple[int, Dict[int, str]]:
        if node_id in piano_valutato.mappa_assegnazioni:
            return 0, {}

        node = self._node_map.get(node_id)
        if not node: return 999999999, {}

        iv_roles = node.ruoli_iv
        nature_role = node.ruolo_natura
        required_stats = [self.legenda.get(r) for r in iv_roles if r in self.legenda]
        required_nature = self.legenda.get(nature_role) if nature_role in self.legenda else None

        if node_id not in self._child_to_parents_map:
            if self.price_manager is None: return 999999999, {}

            primary_stat_key = required_stats[0] if required_stats else ("Natura" if required_nature else "Base")
            cost = 999999999
            decision_desc = "Sconosciuto"
            egg_groups = self.pokemon_data.get(self.target_species, [])
            group_name = egg_groups[0] if egg_groups else "EggGroup"

            target_gender_type = "maschio e femmina"
            if self.target_species in self.gender_data:
                target_gender_type = self.gender_data[self.target_species].get("gender_type", "maschio e femmina").lower()
            elif "Genderless" in self.pokemon_data.get(self.target_species, []):
                 target_gender_type = "genderless"
            is_genderless_species = "genderless" in target_gender_type

            if is_species_mandatory:
                if is_genderless_species:
                    c_specie_stat = self._get_price_or_owned(primary_stat_key, "Specie", "M") # Treat M input as generic
                    c_specie_base = self._get_price_or_owned("Base", "Specie", "M")
                    c_ditto_stat = self._get_price_or_owned(primary_stat_key, "Ditto", "X")
                    c_ditto_base = self._get_price_or_owned("Base", "Ditto", "X")

                    opt1 = c_specie_stat + c_ditto_base
                    opt2 = c_specie_base + c_ditto_stat

                    if opt1 <= opt2:
                        cost = opt1
                        decision_desc = f"Comprare {self.target_species} (Stat) + Ditto (Base) - ${cost}"
                    else:
                        cost = opt2
                        decision_desc = f"Comprare {self.target_species} (Base) + Ditto (Stat) - ${cost}"
                else:
                    cost_A = self._get_price_or_owned(primary_stat_key, "Specie", "F")

                    c_specie_m_stat = self._get_price_or_owned(primary_stat_key, "Specie", "M")
                    c_ditto_base = self._get_price_or_owned("Base", "Ditto", "X")
                    cost_B1 = c_specie_m_stat + c_ditto_base

                    c_specie_m_base = self._get_price_or_owned("Base", "Specie", "M")
                    c_ditto_stat = self._get_price_or_owned(primary_stat_key, "Ditto", "X")
                    cost_B2 = c_specie_m_base + c_ditto_stat

                    cost_B = min(cost_B1, cost_B2)
                    desc_B = f"Comprare {self.target_species} ♂ + Ditto - ${cost_B}"

                    c_specie_f_base = self._get_price_or_owned("Base", "Specie", "F")
                    c_group_m_stat = self._get_price_or_owned(primary_stat_key, "EggGroup", "M")
                    cost_C = c_specie_f_base + c_group_m_stat
                    desc_C = f"Comprare {self.target_species} ♀ (Base) + {group_name} ♂ ({primary_stat_key}) - ${cost_C}"

                    options = [(cost_A, f"Comprare {self.target_species} ♀\n({primary_stat_key}) - ${cost_A}"), (cost_B, desc_B), (cost_C, desc_C)]
                    options.sort(key=lambda x: x[0])
                    cost, decision_desc = options[0]
            else:
                options = []
                if required_gender == 'M':
                    c_specie_m = self._get_price_or_owned(primary_stat_key, "Specie", "M")
                    options.append((c_specie_m, f"Comprare {self.target_species} ♂\n({primary_stat_key}) - ${c_specie_m}"))
                    c_group_m = self._get_price_or_owned(primary_stat_key, "EggGroup", "M")
                    options.append((c_group_m, f"Comprare {group_name} ♂\n({primary_stat_key}) - ${c_group_m}"))
                    c_ditto = self._get_price_or_owned(primary_stat_key, "Ditto", "X")
                    options.append((c_ditto, f"Comprare Ditto\n({primary_stat_key}) - ${c_ditto}"))
                elif required_gender == 'F':
                    c_specie_f = self._get_price_or_owned(primary_stat_key, "Specie", "F")
                    options.append((c_specie_f, f"Comprare {self.target_species} ♀\n({primary_stat_key}) - ${c_specie_f}"))
                    c_group_f = self._get_price_or_owned(primary_stat_key, "EggGroup", "F")
                    options.append((c_group_f, f"Comprare {group_name} ♀\n({primary_stat_key}) - ${c_group_f}"))
                elif required_gender == 'Ditto':
                    c_ditto = self._get_price_or_owned(primary_stat_key, "Ditto", "X")
                    options.append((c_ditto, f"Comprare Ditto\n({primary_stat_key}) - ${c_ditto}"))
                elif required_gender == 'Genderless':
                     c_specie = self._get_price_or_owned(primary_stat_key, "Specie", "M")
                     options.append((c_specie, f"Comprare {self.target_species}\n({primary_stat_key}) - ${c_specie}"))

                if options:
                    options.sort(key=lambda x: x[0])
                    cost, decision_desc = options[0]

            return cost, {node_id: decision_desc}

        parents = self._child_to_parents_map[node_id]
        p1_id, p2_id = parents[0], parents[1]

        fee = self._get_gender_cost(required_gender)
        base_item_cost = 20000
        if required_nature is not None: base_item_cost = 15000
        total_breeding_cost = base_item_cost + fee

        target_gender_type = "maschio e femmina"
        if self.target_species in self.gender_data:
            target_gender_type = self.gender_data[self.target_species].get("gender_type", "maschio e femmina").lower()
        elif "Genderless" in self.pokemon_data.get(self.target_species, []):
             target_gender_type = "genderless"
        is_genderless_species = "genderless" in target_gender_type

        if is_genderless_species:
             p1_mandatory = is_species_mandatory
             p2_mandatory = False
             cost_1, decisions_1 = self.calculate_cost_recursive(p1_id, piano_valutato, p1_mandatory, required_gender='Genderless')
             cost_2, decisions_2 = self.calculate_cost_recursive(p2_id, piano_valutato, p2_mandatory, required_gender='Ditto')
        else:
            p1_mandatory = is_species_mandatory
            p2_mandatory = False
            cost_1, decisions_1 = self.calculate_cost_recursive(p1_id, piano_valutato, p1_mandatory, required_gender='F')
            cost_2, decisions_2 = self.calculate_cost_recursive(p2_id, piano_valutato, p2_mandatory, required_gender='M')

        total_cost = total_breeding_cost + cost_1 + cost_2
        decisions = {**decisions_1, **decisions_2}
        return total_cost, decisions

    def evaluate(self) -> PianoValutato:
        self._build_tree_maps()
        self._identify_mandatory_nodes()
        piano_valutato = PianoValutato(piano_originale=self.piano)
        posseduti_disponibili = list(self.pokemon_posseduti)

        potential_reqs = []
        # Add root node
        if self.piano.livelli:
            final_acc = self.piano.livelli[-1].accoppiamenti[0]
            root_node = final_acc.figlio
            potential_reqs.append({'req': root_node, 'id': id(root_node), 'level': self.piano.livelli[-1].livello_id + 1, 'role': 'root'})

        for livello in self.piano.livelli:
            for acc in livello.accoppiamenti:
                potential_reqs.append({'req': acc.genitore1, 'id': id(acc.genitore1), 'level': livello.livello_id, 'role': 'gen1'})
                potential_reqs.append({'req': acc.genitore2, 'id': id(acc.genitore2), 'level': livello.livello_id, 'role': 'gen2'})

        potential_reqs.sort(key=lambda item: (item['level'], len(item['req'].ruoli_iv), item['req'].ruolo_natura is not None), reverse=True)

        fulfilled_req_ids: Set[int] = set()

        for item in potential_reqs:
            req_id = item['id']
            if req_id in fulfilled_req_ids:
                continue

            richiesto = item['req']
            role = item['role']

            candidati_validi = []
            for candidato in posseduti_disponibili:
                if self._is_valid_candidate(richiesto, candidato, req_id, role):
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
        if self.price_manager and self.piano.livelli:
             final_node = self.piano.livelli[-1].accoppiamenti[0].figlio
             cost, decisions = self.calculate_cost_recursive(id(final_node), piano_valutato, True)
             piano_valutato.costo_totale = cost
             piano_valutato.mappa_acquisti = decisions

def valuta_piani(piani_generati: List[PianoCompleto], pokemon_posseduti: List[PokemonPosseduto]) -> List[PianoValutato]:
    piani_valutati = []
    for piano in piani_generati:
        evaluator = PlanEvaluator(piano, list(pokemon_posseduti))
        piano_valutato = evaluator.evaluate()
        piani_valutati.append(piano_valutato)

    piani_valutati.sort(key=lambda p: p.punteggio, reverse=True)
    return piani_valutati
