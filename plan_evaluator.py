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

        # 3b. Egg Group Check (For Non-Mandatory / Donor Roles)
        # If not mandatory, and not Ditto, check if species shares Egg Group with Target
        elif role == 'gen2' and posseduto.specie != 'Ditto' and posseduto.specie != self.target_species:
             target_groups = self.pokemon_data.get(self.target_species, [])
             candidate_groups = self.pokemon_data.get(posseduto.specie, [])
             # If disjoint and both have data, fail.
             # If data missing, we allow (fail open) or check strict?
             # Let's check strict intersection if data exists.
             if target_groups and candidate_groups:
                 if set(target_groups).isdisjoint(set(candidate_groups)):
                     return False

        # 4. Gender Check
        target_gender_type = "maschio e femmina"
        if self.target_species in self.gender_data:
            target_gender_type = self.gender_data[self.target_species].get("gender_type", "maschio e femmina").lower()
        elif "Genderless" in self.pokemon_data.get(self.target_species, []):
             target_gender_type = "genderless"

        # Normalize Possessed Gender
        p_sesso = posseduto.sesso
        if p_sesso == 'M': p_sesso = 'Maschio'
        if p_sesso == 'F': p_sesso = 'Femmina'

        # Genderless Target Logic
        if "genderless" in target_gender_type:
            if role == 'gen1':
                # Must be Genderless (Species)
                # Note: Some inputs might treat "Specie M" as generic.
                # But for strict matching, "Genderless" implies no sex.
                # However, user input might label it differently.
                # Let's assume strict "Genderless" or "M" if checking inputs?
                # For owned pokemon, user selects "Maschio/Femmina/Genderless".
                # If target is Beldum, user should set owned to "Genderless".
                # But to be safe against user error (selecting "Maschio" for Beldum), we might relax?
                # No, strict is better.
                if p_sesso != 'Genderless':
                    # Allow relaxation?
                    pass
                # Actually, check logic:
                if p_sesso != 'Genderless':
                     return False
            elif role == 'gen2':
                # Must be Ditto
                if posseduto.specie != 'Ditto':
                    return False

        # Gendered Target Logic
        else:
            if role == 'gen1':
                # Must be Female (Mother)
                if p_sesso != 'Femmina':
                    return False
            elif role == 'gen2':
                # Must be Male (Father) OR Ditto
                # If possessed is Ditto, it can serve as Male partner.
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
        """
        Calculates the cost to select the gender based on the species' gender ratio.
        gender_role: 'F' (Mother), 'M' (Father), or 'X' (Genderless/Any).
        """
        if self.target_species not in self.gender_data:
            return 5000

        data = self.gender_data[self.target_species]
        ratio_str = data.get("gender_ratio", "")
        gender_type = data.get("gender_type", "").lower()

        if "genderless" in gender_type or "solo" in gender_type or "N/A" in ratio_str:
            return 0

        # Parse Ratio
        # "87.5% M, 12.5% F" -> check percentages
        try:
            m_part = ratio_str.split(',')[0].strip() # "87.5% M"
            percentage = float(m_part.split('%')[0]) # 87.5
        except (ValueError, IndexError):
            return 5000

        if percentage == 50.0:
            return 5000
        elif percentage == 87.5: # Starter / Eevee
            if gender_role == 'F': return 21000
            else: return 5000
        elif percentage == 25.0: # Female heavy (Vulpix)
            if gender_role == 'F': return 9000
            else: return 5000

        return 5000

    def calculate_cost_recursive(self, node_id: int, piano_valutato: PianoValutato, is_species_mandatory: bool, required_gender: str = 'F') -> Tuple[int, Dict[int, str]]:
        """
        Calculates the cost to obtain the Pokemon at node_id.
        Returns (Cost, Decisions_Map).
        is_species_mandatory: If True, this Pokemon MUST be the target species (Female).
        required_gender: 'F' (Mother) or 'M' (Father) required for breeding compatibility.
        """
        # 1. Pruning Check: If Owned, Cost is 0
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
            group_name = egg_groups[0] if egg_groups else "EggGroup"

            # Check for Genderless Biological Nature
            target_gender_type = "maschio e femmina"
            if self.target_species in self.gender_data:
                target_gender_type = self.gender_data[self.target_species].get("gender_type", "maschio e femmina").lower()

            is_genderless_species = "genderless" in target_gender_type

            if is_species_mandatory:

                if is_genderless_species:
                    # Genderless Logic: Must buy Species (Base/Stat) + Ditto (Stat/Base)
                    # No "Female" or "Male" logic.
                    # We treat "Specie M" input as generic "Specie" for Genderless in this context.

                    c_specie_stat = self.price_manager.get_price(primary_stat_key, "Specie", "M") # Using M/F field as generic
                    c_specie_base = self.price_manager.get_price("Base", "Specie", "M")

                    c_ditto_stat = self.price_manager.get_price(primary_stat_key, "Ditto", "X")
                    c_ditto_base = self.price_manager.get_price("Base", "Ditto", "X")

                    # Option 1: Species(Stat) + Ditto(Base)
                    opt1 = c_specie_stat + c_ditto_base
                    # Option 2: Species(Base) + Ditto(Stat)
                    opt2 = c_specie_base + c_ditto_stat

                    if opt1 <= opt2:
                        cost = opt1
                        decision_desc = f"Comprare {self.target_species} (Stat) + Ditto (Base) - ${cost}"
                    else:
                        cost = opt2
                        decision_desc = f"Comprare {self.target_species} (Base) + Ditto (Stat) - ${cost}"

                else:
                    # Standard Gendered Logic
                    # Option A: Buy Female Species (Standard)
                    cost_A = self.price_manager.get_price(primary_stat_key, "Specie", "F")

                    # Option B: Buy Male Species + Ditto (Ditto Trick)
                    c_specie_m_stat = self.price_manager.get_price(primary_stat_key, "Specie", "M")
                    c_ditto_base = self.price_manager.get_price("Base", "Ditto", "X")
                    cost_B1 = c_specie_m_stat + c_ditto_base

                    c_specie_m_base = self.price_manager.get_price("Base", "Specie", "M")
                    c_ditto_stat = self.price_manager.get_price(primary_stat_key, "Ditto", "X")
                    cost_B2 = c_specie_m_base + c_ditto_stat

                    if cost_B1 < cost_B2:
                        cost_B = cost_B1
                        desc_B = f"Comprare {self.target_species} ♂ ({primary_stat_key}) + Ditto (Base) - ${cost_B}"
                    else:
                        cost_B = cost_B2
                        desc_B = f"Comprare Ditto ({primary_stat_key}) + {self.target_species} ♂ (Base) - ${cost_B}"

                    # Option C: Buy Female Species (Base) + Male EggGroup (Stat)
                    # This ensures the Line is preserved (Female Species) but gets stats from cheap EggGroup.
                    c_specie_f_base = self.price_manager.get_price("Base", "Specie", "F")
                    c_group_m_stat = self.price_manager.get_price(primary_stat_key, "EggGroup", "M")
                    cost_C = c_specie_f_base + c_group_m_stat
                    desc_C = f"Comprare {self.target_species} ♀ (Base) + {group_name} ♂ ({primary_stat_key}) - ${cost_C}"

                    # Find Min(A, B, C)
                    options = [
                        (cost_A, f"Comprare {self.target_species} ♀\n({primary_stat_key}) - ${cost_A}"),
                        (cost_B, desc_B),
                        (cost_C, desc_C)
                    ]
                    options.sort(key=lambda x: x[0])

                    cost = options[0][0]
                    decision_desc = options[0][1]

            else:
                # Not Mandatory Species (Donor Branch).
                # We can choose between Specie, EggGroup, or Ditto.

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
                    c_specie_f = self.price_manager.get_price(primary_stat_key, "Specie", "F")
                    options.append((c_specie_f, f"Comprare {self.target_species} ♀\n({primary_stat_key}) - ${c_specie_f}"))

                    c_group_f = self.price_manager.get_price(primary_stat_key, "EggGroup", "F")
                    options.append((c_group_f, f"Comprare {group_name} ♀\n({primary_stat_key}) - ${c_group_f}"))

                elif required_gender == 'Ditto':
                    # Specific request for a Ditto (e.g. for Genderless breeding)
                    c_ditto = self.price_manager.get_price(primary_stat_key, "Ditto", "X")
                    options.append((c_ditto, f"Comprare Ditto\n({primary_stat_key}) - ${c_ditto}"))

                elif required_gender == 'Genderless':
                     # Specific request for Genderless Species (e.g. Beldum)
                     # Treat "Specie M" as generic Specie
                     c_specie = self.price_manager.get_price(primary_stat_key, "Specie", "M")
                     options.append((c_specie, f"Comprare {self.target_species}\n({primary_stat_key}) - ${c_specie}"))

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

        # Breeding Fee (Dynamic)
        # We need to decide what Gender we are forcing for the child node.
        # This is passed as 'required_gender' in the *parent's* call to this function.
        # But here, we are calculating the cost of *creating* the current node.
        # The fee is for *this* node's gender selection.
        # Wait, the fee applies to the BREEDING process that creates this node.
        # The gender we select is 'required_gender'.

        fee = self._get_gender_cost(required_gender)

        # Fixed Item Costs
        # 15,000 for Everstone (Nature) + 10,000 for Brace (IV) = 25,000 approx per step?
        # User prompt said: "Tasse Dinamiche... es 5.000$ ... 21.000$".
        # This refers to the Gender Selection Fee.
        # There are also standard breeding item costs (Braces/Everstone).
        # Existing code had: `fee = 20000` or `15000`.
        # PokeMMO costs:
        # - Braces: $10,000 each (usually 2 needed = $20,000, or 1 Brace + Everstone).
        # - Everstone: $5,000? No, usually treated as an item cost.
        # Let's keep the existing base logic for items and ADD the dynamic gender fee.
        # Existing logic:
        # fee = 20000 (2 Braces?)
        # if required_nature is not None: fee = 15000 (1 Brace + Everstone?)
        # Let's respect the existing item cost logic and ADD the gender fee.

        base_item_cost = 20000
        if required_nature is not None:
             base_item_cost = 15000 # Approximation of item costs

        total_breeding_cost = base_item_cost + fee

        # Optimization: Use the mandatory logic
        # Genitore 1 (Mother) inherits the mandatory status of the child IF the child is mandatory.
        # Genitore 2 (Father) is always a donor (not mandatory).

        # Genderless Handling for Recursion
        target_gender_type = "maschio e femmina"
        if self.target_species in self.gender_data:
            target_gender_type = self.gender_data[self.target_species].get("gender_type", "maschio e femmina").lower()
        is_genderless_species = "genderless" in target_gender_type

        if is_genderless_species:
             # If Genderless, we must use Ditto.
             # One parent is Species (Mandatory if child is mandatory), other is Ditto.
             # Ditto is Genderless. Species is Genderless.
             # We pass 'X' or specific roles?
             # _is_valid_candidate checks: Gen1=Genderless, Gen2=Ditto.
             # So we must request Gen1 to be Mandatory Species (Genderless), Gen2 to be Ditto (Not Mandatory Species).
             p1_mandatory = is_species_mandatory
             p2_mandatory = False # Ditto is not the species

             cost_1, decisions_1 = self.calculate_cost_recursive(p1_id, piano_valutato, p1_mandatory, required_gender='Genderless')
             cost_2, decisions_2 = self.calculate_cost_recursive(p2_id, piano_valutato, p2_mandatory, required_gender='Ditto') # Helper to indicate Ditto role

        else:
            # Standard
            p1_mandatory = is_species_mandatory
            p2_mandatory = False

            # Pass Gender Roles: Gen1 is always Female (Mother), Gen2 is always Male (Father)
            cost_1, decisions_1 = self.calculate_cost_recursive(p1_id, piano_valutato, p1_mandatory, required_gender='F')
            cost_2, decisions_2 = self.calculate_cost_recursive(p2_id, piano_valutato, p2_mandatory, required_gender='M')

        total_cost = total_breeding_cost + cost_1 + cost_2
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
