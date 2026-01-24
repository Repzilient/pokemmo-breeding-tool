import os
import json
import logging
import copy
from typing import List, Set, Dict, Any

# Import core modules
# Assuming we are running from 'c:\Users\Administrator\Desktop\github'
from structures import PokemonPosseduto, PokemonRichiesto, PianoValutato
from price_manager import PriceManager
from core_engine import esegui_generazione
from plan_evaluator import PlanEvaluator, valuta_piani

def load_data():
    """Carica i dati JSON una sola volta."""
    print("[INIT] Loading System Data...")
    try:
        with open(os.path.join('data', 'pokemon_data.json'), 'r', encoding='utf-8') as f:
            pokemon_data = json.load(f)
        with open(os.path.join('data', 'pokemon_gender.json'), 'r', encoding='utf-8') as f:
            gender_data_list = json.load(f)
            gender_data = {entry['name']: entry for entry in gender_data_list}
        print("Data loaded successfully.\n")
        return pokemon_data, gender_data
    except Exception as e:
        print(f"Failed to load data: {e}")
        return {}, {}

def run_test_scenario(
    scenario_id: int,
    scenario_name: str,
    target_species: str,
    target_nature: str,
    target_ivs: List[str],
    owned_pokemons: List[Dict[str, Any]],
    price_config: Dict[str, int], # { "Species_M": 1000, "Group_M": 500 ... }
    pokemon_data: Dict,
    gender_data: Dict,
    detailed_prices: Dict = None # Optional: Full price map per stat
):
    print("="*60)
    print(f"SCENARIO {scenario_id}: {scenario_name}")
    print(f"TARGET: {target_species} ({target_nature}) {target_ivs}")
    print("="*60)

    # 1. SETUP OWNED POKEMON
    owned_list = []
    for p_data in owned_pokemons:
        p = PokemonPosseduto(
            id_utente=p_data.get("id", f"OWNED_{len(owned_list)+1}"),
            specie=p_data.get("specie", target_species),
            sesso=p_data.get("sesso", "Maschio"),
            natura=p_data.get("natura"),
            ivs=p_data.get("ivs", [])
        )
        owned_list.append(p)
    print(f"[1] Owned Pokemon: {len(owned_list)}")
    for p in owned_list:
        print(f"    - {p.specie} ({p.sesso}) {p.ivs} {p.natura if p.natura else ''}")

    # 2. GENERATION
    print(f"[2] Generating Plans for {len(target_ivs)}IV + Nature...")
    piani_generati = esegui_generazione(target_ivs, target_nature)
    if not piani_generati:
        print("[FAIL] No plans generated!")
        return
    print(f"    Generated {len(piani_generati)} raw plans.")

    # 3. EVALUATION (Phase 1)
    # Allows assignments of Owned Pokemon
    piani_valutati = valuta_piani(piani_generati, owned_list, target_species, pokemon_data, gender_data)
    candidates = piani_valutati[:20] # Top 20 based on scoring
    print(f"[3] Selected {len(candidates)} candidates for pricing.")

    # 4. SETUP PRICES
    print("[4] Configuring Prices...")
    pm = PriceManager()
    pm.clear() # Ensure clean slate

    if detailed_prices:
        # detailed_prices = {"Base": {"Specie_M": 100, ...}, "PS": ...}
        for stat, prices in detailed_prices.items():
            # Handle Specie
            if "Specie_M" in prices: pm.set_price(stat, "Specie", "M", prices["Specie_M"])
            if "Specie_F" in prices: pm.set_price(stat, "Specie", "F", prices["Specie_F"])
            if "Ditto" in prices: pm.set_price(stat, "Ditto", "X", prices["Ditto"])
            
            # Handle Egg Groups (Generic)
            if "EggGroup_M" in prices:
                # Apply to generic groups and specific for target
                egg_groups = pokemon_data.get(target_species, [])
                # Also explicit "Monster", "Dragon", etc.
                common_groups = ["Monster", "Dragon", "Field", "Water A", "Water B", "Bug", "Flying", "Chaos", "Mineral", "Humanoid"]
                
                val_m = prices["EggGroup_M"]
                val_f = prices.get("EggGroup_F", 999999999)

                for group in set(egg_groups + common_groups):
                    pm.set_price(stat, group, "M", val_m)
                    if val_f != 999999999:
                        pm.set_price(stat, group, "F", val_f)

    else:
        # Default Prices (Fallback)
        DEFAULT_PRICES = {
            "Specie_M": 5000, "Specie_F": 5000,
            "EggGroup_M": 2000, "EggGroup_F": 5000,
            "Ditto": 4000
        }
        
        # Merge defaults with scenario config
        final_prices = DEFAULT_PRICES.copy()
        final_prices.update(price_config)
    
        # Apply prices to all relevant stats
        stats_to_price = ["Base", "Natura"] + target_ivs
        
        # Specific Egg Groups for this species
        egg_groups = pokemon_data.get(target_species, [])
        
        for stat in stats_to_price:
            # Base Prices
            pm.set_price(stat, "Specie", "M", final_prices["Specie_M"])
            pm.set_price(stat, "Specie", "F", final_prices["Specie_F"])
            pm.set_price(stat, "Ditto", "X", final_prices["Ditto"])
            
            # Egg Groups (Apply generic "EggGroup" price to specific groups)
            for group in egg_groups:
                 pm.set_price(stat, group, "M", final_prices["EggGroup_M"])
                 pm.set_price(stat, group, "F", final_prices["EggGroup_F"])
                 
            # Generic fallback for logic that queries "Monster" explicitly if not in list
            # (Just cover common ones to be safe)
            common_groups = ["Monster", "Dragon", "Field", "Water A", "Water B", "Bug", "Flying", "Chaos", "Mineral"]
            for group in common_groups:
                 pm.set_price(stat, group, "M", final_prices["EggGroup_M"])
                 pm.set_price(stat, group, "F", final_prices["EggGroup_F"])

    # 5. COST CALCULATION (Phase 2)
    print("[5] Calculating Final Costs...")
    for p_val in candidates:
        ev = PlanEvaluator(
            p_val.piano_originale,
            owned_list,
            pm,
            target_species,
            pokemon_data,
            target_nature,
            gender_data
        )
        ev._build_tree_maps()
        ev._identify_mandatory_nodes()
        ev.update_cost(p_val) # Runs calculate_cost_recursive respecting assignments

    # Sort by Cost
    candidates.sort(key=lambda p: p.punteggio, reverse=True) # Score first
    candidates.sort(key=lambda p: p.costo_totale) # Then Cost ascending

    best_plan = candidates[0]

    # 6. OUTPUT
    print("\n" + "-"*30)
    print(f"RESULT: {scenario_name}")
    print(f"BEST SCORE: {best_plan.punteggio}")
    print(f"TOTAL COST: ${best_plan.costo_totale:,}")
    print(f"POKEMON USED: {len(best_plan.pokemon_usati)}/{len(owned_list)}")
    print("-"*30)
    
    # Short visualization
    # Full visualization
    print("FULL PLAN DETAILS:")
    piano = best_plan.piano_originale
    
    for i, livello in enumerate(piano.livelli):
        print(f"--- Level {i+1} ---")
        for acc in livello.accoppiamenti:
            # Helper to get display name
            def get_name(node):
                nid = id(node)
                if nid in best_plan.mappa_assegnazioni:
                    uid = best_plan.mappa_assegnazioni[nid]
                    return f"[OWNED: {uid}]"
                if nid in best_plan.mappa_acquisti:
                    return best_plan.mappa_acquisti[nid].strip()
                return "???"
                
            p1 = get_name(acc.genitore1)
            p2 = get_name(acc.genitore2)
            
            try:
                print(f"    {p1} + {p2}")
            except UnicodeEncodeError:
                p1_safe = p1.encode('ascii', 'ignore').decode('ascii')
                p2_safe = p2.encode('ascii', 'ignore').decode('ascii')
                print(f"    {p1_safe} + {p2_safe}")
        print("") # Spacer between levels


def main():
    pokemon_data, gender_data = load_data()
    if not pokemon_data: return

    # --- SCENARIO 7: User Sableye (Detailed Prices) ---
    # Target: Sableye (Hasty) [PS, Velocità]
    # Prices: Vary per stat.
    
    detailed_prices = {
        "Base": {"Specie_M": 2979, "Specie_F": 1999, "EggGroup_M": 1500, "EggGroup_F": 1000, "Ditto": 4800},
        "Natura": {"Specie_M": 7777, "Specie_F": 3000, "EggGroup_M": 2997, "EggGroup_F": 1200, "Ditto": 4800},
        "PS": {"Specie_M": 3500, "Specie_F": 9998, "EggGroup_M": 3500, "EggGroup_F": 1200, "Ditto": 5099},
        "Velocità": {"Specie_M": 7699, "Specie_F": 9499, "EggGroup_M": 7699, "EggGroup_F": 1200, "Ditto": 7000}
    }

    run_test_scenario(
        7, "User Sableye Log",
        "Sableye", "Hasty", ["PS", "Velocità"],
        [], # No owned
        {}, # Flat config ignored if detailed is passed
        pokemon_data, gender_data,
        detailed_prices=detailed_prices
    )

if __name__ == "__main__":
    main()
