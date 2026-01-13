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
        """
        Identifies nodes that MUST be the target species (Female Line).
        Traverses from the root down to the leaves via Genitore 1 (Mother).
        """
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
                # Genitore 1 is mandatory (Mother)
                self._mandatory_species_nodes.add(gen1_id)
                q.append(gen1_id)
                # Genitore 2 is NOT mandatory (Male Donor) - do not add

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

    def _is_valid_candidate(self, richiesto: PokemonRichiesto, posseduto: PokemonPosseduto, req_id: int, role: str) -> bool:
        """
        Validates if a possessed Pokemon can fill the role.
        req_id: The ID of the requirement node.
        role: 'gen1' (Mother/Species) or 'gen2' (Father/Partner).
        """
        # 1. IV Check
        ivs_reali_richieste = {self.legenda.get(r) for r in richiesto.ruoli_iv if r in self.legenda}
        if not ivs_reali_richieste.issubset(set(posseduto.ivs)):
            return False

        # 2. Nature Check
        natura_reale_richiesta = self.legenda.get(richiesto.ruolo_natura) if richiesto.ruolo_natura in self.legenda else None
        if natura_reale_richiesta is not None and posseduto.natura != natura_reale_richiesta:
            return False

        # 3. Species Check
        # If the node is marked as Mandatory Species, the possessed pokemon MUST be the target species.
        if req_id in self._mandatory_species_nodes:
            if posseduto.specie != self.target_species:
                return False

        # 4. Gender Check
        target_gender_type = "maschio e femmina"
        if self.target_species in self.gender_data:
            target_gender_type = self.gender_data[self.target_species].get("gender_type", "maschio e femmina").lower()

        # Genderless Target Logic
        if "genderless" in target_gender_type:
            if role == 'gen1':
                # Must be Genderless
                if posseduto.sesso != 'Genderless':
                    return False
                # If mandatory, we already checked species above.
            elif role == 'gen2':
                # Must be Ditto
                if posseduto.specie != 'Ditto':
                    return False

        # Gendered Target Logic
        else:
            if role == 'gen1':
                # Must be Female (Mother)
                if posseduto.sesso != 'Femmina':
                    return False
            elif role == 'gen2':
                # Must be Male (Father) OR Ditto
                # If possessed is Ditto, it can serve as Male partner.
                if posseduto.specie == 'Ditto':
                    return True
                if posseduto.sesso != 'Maschio':
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

    def calculate_cost_recursive(self, node_id: int, piano_valutato: PianoValutato, is_species_mandatory: bool, required_gender: str = 'F') -> Tuple[int, Dict[int, str]]:
        """
        Calculates the cost to obtain the Pokemon at node_id.
        Returns (Cost, Decisions_Map).
        is_species_mandatory: If True, this Pokemon MUST be the target species (Female).
        required_gender: 'F' (Mother) or 'M' (Father) required for breeding compatibility.
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
            group_name = egg_groups[0] if egg_groups else "EggGroup"

            if is_species_mandatory:
                # Option A: Buy Female Species (Standard)
                cost_A = self.price_manager.get_price(primary_stat_key, "Specie", "F")

                # Option B: Buy Male Species + Ditto (Ditto Trick)
                # This works because Male Species + Ditto = Species Egg
                # Usually we need the stat on one of them.
                # If we buy Species Male with Stat, Ditto can be trash.
                # If we buy Ditto with Stat, Species Male can be trash.
                # Let's assume best case: Cheapest combination.

                # Case B1: Species M (Stat) + Ditto (Trash)
                c_specie_m_stat = self.price_manager.get_price(primary_stat_key, "Specie", "M")
                c_ditto_base = self.price_manager.get_price("Base", "Ditto", "X")
                cost_B1 = c_specie_m_stat + c_ditto_base

                # Case B2: Species M (Trash) + Ditto (Stat)
                c_specie_m_base = self.price_manager.get_price("Base", "Specie", "M")
                c_ditto_stat = self.price_manager.get_price(primary_stat_key, "Ditto", "X")
                cost_B2 = c_specie_m_base + c_ditto_stat

                if cost_B1 < cost_B2:
                    cost_B = cost_B1
                    desc_B = f"Comprare {self.target_species} ♂ ({primary_stat_key}) + Ditto (Base) - ${cost_B}"
                else:
                    cost_B = cost_B2
                    desc_B = f"Comprare Ditto ({primary_stat_key}) + {self.target_species} ♂ (Base) - ${cost_B}"

                # Compare A vs B
                if cost_A <= cost_B:
                    cost = cost_A
                    decision_desc = f"Comprare {self.target_species} ♀\n({primary_stat_key}) - ${cost_A}"
                else:
                    cost = cost_B
                    decision_desc = desc_B

            else:
                # Not Mandatory Species.
                # We can choose between Specie, EggGroup, or Ditto.
                # BUT we must respect the Gender Role required by the breeding pair above!

                options = []

                if required_gender == 'M':
                    # Need a Male Partner (or Ditto)
                    c_specie_m = self.price_manager.get_price(primary_stat_key, "Specie", "M")
                    options.append((c_specie_m, f"Comprare {self.target_species} ♂\n({primary_stat_key}) - ${c_specie_m}"))

                    c_group_m = self.price_manager.get_price(primary_stat_key, "EggGroup", "M")
                    options.append((c_group_m, f"Comprare {group_name} ♂\n({primary_stat_key}) - ${c_group_m}"))

                    c_ditto = self.price_manager.get_price(primary_stat_key, "Ditto", "X")
                    options.append((c_ditto, f"Comprare Ditto\n({primary_stat_key}) - ${c_ditto}"))

                elif required_gender == 'F':
                    # Need a Female Partner (Mother of a donor branch)
                    # Can be Species Female or EggGroup Female.
                    # Ditto cannot be a Mother (unless breeding with Genderless, but here we are in 'Non Mandatory' context).
                    # Actually, if we use Ditto as Gen1, the Species is determined by Gen2 (Male).
                    # But if Gen2 is also a donor (EggGroup), breeding Ditto + EggGroup = EggGroup Egg.
                    # This is valid for a donor branch!

                    c_specie_f = self.price_manager.get_price(primary_stat_key, "Specie", "F")
                    options.append((c_specie_f, f"Comprare {self.target_species} ♀\n({primary_stat_key}) - ${c_specie_f}"))

                    c_group_f = self.price_manager.get_price(primary_stat_key, "EggGroup", "F")
                    options.append((c_group_f, f"Comprare {group_name} ♀\n({primary_stat_key}) - ${c_group_f}"))

                    # Ditto as Mother? Only if Partner is Male.
                    # This gets complicated. Let's stick to simple Female roles for now to fix the Absol bug.
                    # Using EggGroup F is the key fix.

                # Find min
                if options:
                    options.sort(key=lambda x: x[0])
                    cost, decision_desc = options[0]
                else:
                    cost = 999999999 # Should not happen

            return cost, {node_id: decision_desc}

        # 4. Recursive Step: Breeding
        parents = self._child_to_parents_map[node_id]
        p1_id, p2_id = parents[0], parents[1]

        fee = 20000
        if required_nature is not None:
             fee = 15000

        # Optimization: Use the mandatory logic
        # Genitore 1 (Mother) inherits the mandatory status of the child IF the child is mandatory.
        # Genitore 2 (Father) is always a donor (not mandatory).

        # Logic:
        # If Child (current node) is mandatory -> Mother MUST be mandatory.
        # If Child is NOT mandatory -> Mother does NOT need to be mandatory.

        p1_mandatory = is_species_mandatory
        p2_mandatory = False # Fathers are donors

        # Pass Gender Roles: Gen1 is always Female (Mother), Gen2 is always Male (Father)
        cost_1, decisions_1 = self.calculate_cost_recursive(p1_id, piano_valutato, p1_mandatory, required_gender='F')
        cost_2, decisions_2 = self.calculate_cost_recursive(p2_id, piano_valutato, p2_mandatory, required_gender='M')

        total_cost = fee + cost_1 + cost_2
        decisions = {**decisions_1, **decisions_2}

        return total_cost, decisions

    def evaluate(self) -> PianoValutato:
        """
        Executes the full evaluation (assignments only).
        """
        self._build_tree_maps()
        self._identify_mandatory_nodes()
        piano_valutato = PianoValutato(piano_originale=self.piano)
        posseduti_disponibili = list(self.pokemon_posseduti)

        potential_reqs = []
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

            candidati_validi = []
            role = item['role']
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
        piano_valutato.evaluator = evaluator  # Store evaluator
        piani_valutati.append(piano_valutato)

    piani_valutati.sort(key=lambda p: p.punteggio, reverse=True)
    return piani_valutati
