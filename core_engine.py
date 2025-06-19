import itertools
import copy
from typing import List, Dict, Optional, Tuple

from structures import PokemonRichiesto, Accoppiamento, Livello, PianoCompleto

def _crea_piano_4iv_natura_strutturato(strategia_genitori_3iv: Tuple[Tuple[str, ...], Tuple[str, ...]]) -> List[Livello]:
    """
    Costruisce un albero di breeding 4IV+N rispettando la rigida struttura 8-4-2-1.
    La logica interna viene adattata in base alla strategia di accoppiamento fornita,
    correggendo l'errore di progressione del ramo natura.
    """
    
    # 1. Deconstruct the strategy to define the main components
    ruoli_genitore_A = tuple(sorted(strategia_genitori_3iv[0]))
    ruoli_genitore_B = tuple(sorted(strategia_genitori_3iv[1]))

    # Define the 4IV pokemon, which is the union of the two 3IV parents
    ruoli_4iv = tuple(sorted(list(set(ruoli_genitore_A) | set(ruoli_genitore_B))))
    
    # Define a consistent 3IV+N parent. We use the first 3 roles of the 4IV target.
    # E.g., if target is BGRY, the 3IV+N parent will have B, G, R.
    ruoli_3iv_n = tuple(sorted((ruoli_4iv[0], ruoli_4iv[1], ruoli_4iv[2])))

    # --- TOP-DOWN DEFINITION OF COMPONENTS ---
    
    # Livello 4 (Target)
    target_finale = PokemonRichiesto(ruoli_iv=ruoli_4iv, ruolo_natura='V')

    # Livello 3 (Final Parents)
    genitore_4iv_final = PokemonRichiesto(ruoli_iv=ruoli_4iv)
    genitore_3iv_n_final = PokemonRichiesto(ruoli_iv=ruoli_3iv_n, ruolo_natura='V')
    
    # Livello 2 (Parents for L3)
    genitore_A_3iv = PokemonRichiesto(ruoli_iv=ruoli_genitore_A)
    genitore_B_3iv = PokemonRichiesto(ruoli_iv=ruoli_genitore_B)
    
    # To make genitore_3iv_n_final (e.g., V-B-G-R), we need a 2IV+N and a 2IV.
    # Let's make V-B-G [2IV+N] and B-R [2IV]
    ruoli_2iv_n = tuple(sorted((ruoli_3iv_n[0], ruoli_3iv_n[1])))
    genitore_2iv_n = PokemonRichiesto(ruoli_iv=ruoli_2iv_n, ruolo_natura='V')
    
    ruoli_2iv_complemento = tuple(sorted((ruoli_3iv_n[0], ruoli_3iv_n[2])))
    genitore_2iv_complemento = PokemonRichiesto(ruoli_iv=ruoli_2iv_complemento)

    # Livello 1 (Parents for L2)
    # Deconstruct the L2 parents to find which 2IV and 1IV+N are needed.
    gen_A_p1 = PokemonRichiesto(ruoli_iv=tuple(sorted((ruoli_genitore_A[0], ruoli_genitore_A[1]))))
    gen_A_p2 = PokemonRichiesto(ruoli_iv=tuple(sorted((ruoli_genitore_A[0], ruoli_genitore_A[2]))))
    
    gen_B_p1 = PokemonRichiesto(ruoli_iv=tuple(sorted((ruoli_genitore_B[0], ruoli_genitore_B[1]))))
    gen_B_p2 = PokemonRichiesto(ruoli_iv=tuple(sorted((ruoli_genitore_B[0], ruoli_genitore_B[2]))))
    
    # Parents for genitore_2iv_n (e.g., V-B-G) are V-B [1IV+N] and B-G [2IV]
    gen_2iv_n_p1 = PokemonRichiesto(ruoli_iv=(ruoli_2iv_n[0],), ruolo_natura='V')
    gen_2iv_n_p2 = PokemonRichiesto(ruoli_iv=ruoli_2iv_n)
    
    # --- BOTTOM-UP ASSEMBLY (Constructing the actual tree) ---
    
    b, g, r, y = ruoli_4iv # Assign for readability
    
    # Livello 1: Create a standard base of 8 pairings.
    # This base is rich enough to contain all 2IV/1IV+N components needed above.
    livello1 = Livello(1, [
        Accoppiamento(PokemonRichiesto(ruoli_iv=(b,)), PokemonRichiesto(ruoli_iv=(g,)), PokemonRichiesto(ruoli_iv=(b, g))),
        Accoppiamento(PokemonRichiesto(ruoli_iv=(b,)), PokemonRichiesto(ruoli_iv=(r,)), PokemonRichiesto(ruoli_iv=(b, r))),
        Accoppiamento(PokemonRichiesto(ruoli_iv=(b,)), PokemonRichiesto(ruoli_iv=(y,)), PokemonRichiesto(ruoli_iv=(b, y))),
        Accoppiamento(PokemonRichiesto(ruoli_iv=(g,)), PokemonRichiesto(ruoli_iv=(r,)), PokemonRichiesto(ruoli_iv=(g, r))),
        Accoppiamento(PokemonRichiesto(ruoli_iv=(g,)), PokemonRichiesto(ruoli_iv=(y,)), PokemonRichiesto(ruoli_iv=(g, y))),
        Accoppiamento(PokemonRichiesto(ruoli_iv=(r,)), PokemonRichiesto(ruoli_iv=(y,)), PokemonRichiesto(ruoli_iv=(r, y))),
        Accoppiamento(PokemonRichiesto(ruolo_natura='V'), PokemonRichiesto(ruoli_iv=(b,)), PokemonRichiesto(ruoli_iv=(b,), ruolo_natura='V')),
        Accoppiamento(PokemonRichiesto(ruoli_iv=(g,)), PokemonRichiesto(ruoli_iv=(r,)), PokemonRichiesto(ruoli_iv=(g, r))), # Filler
    ])
    
    # Livello 2: Create the 4 intermediate parents for L3.
    livello2 = Livello(2, [
        Accoppiamento(gen_A_p1, gen_A_p2, genitore_A_3iv),
        Accoppiamento(gen_B_p1, gen_B_p2, genitore_B_3iv),
        Accoppiamento(gen_2iv_n_p1, gen_2iv_n_p2, genitore_2iv_n),
        Accoppiamento(PokemonRichiesto(ruoli_iv=(g,y)), PokemonRichiesto(ruoli_iv=(r,y)), PokemonRichiesto(ruoli_iv=(g,r,y))), # Filler 3IV
    ])
    
    # Livello 3: Create the 2 final parents for L4. THIS IS THE CRITICAL FIX.
    livello3 = Livello(3, [
        Accoppiamento(genitore_A_3iv, genitore_B_3iv, genitore_4iv_final),
        Accoppiamento(genitore_2iv_n, genitore_2iv_complemento, genitore_3iv_n_final),
    ])
    
    # Livello 4: Final pairing.
    livello4 = Livello(4, [
        Accoppiamento(genitore_4iv_final, genitore_3iv_n_final, target_finale)
    ])
    
    return [livello1, livello2, livello3, livello4]

def esegui_generazione(ivs_desiderate: List[str], natura_desiderata: Optional[str]) -> List[PianoCompleto]:
    """
    Motore principale per la generazione dei piani.
    Genera tutte le permutazioni di statistiche per ogni strategia strutturale valida.
    """
    piani_generati = []
    num_iv = len(ivs_desiderate)
    ha_natura = bool(natura_desiderata)
    
    CANONICAL_IV_ROLES = ['B', 'G', 'R', 'Y', 'O', 'I'] # Changed order for consistency
    nat_role = 'V'

    if not ha_natura or num_iv != 4:
        print(f"[AVVISO] Questo motore supporta solo 4IV+Natura. Richiesto: {num_iv}IV, Natura: {ha_natura}")
        return []

    iv_roles_for_legend = CANONICAL_IV_ROLES[:num_iv]
    permutazioni_stats = list(itertools.permutations(ivs_desiderate))
    
    id_piano_counter = 0

    iv_roles_base = CANONICAL_IV_ROLES[:4]
    
    # 1. Trova tutte le combinazioni di 3 ruoli IV
    combinazioni_3iv = list(itertools.combinations(iv_roles_base, 3))
    
    # 2. Trova tutte le 6 coppie di set 3IV che possono generare un 4IV (unione = 4)
    strategie_strutturali = []
    for pair in itertools.combinations(combinazioni_3iv, 2):
        unione_ivs = set(pair[0]) | set(pair[1])
        if len(unione_ivs) == 4:
            strategie_strutturali.append(pair)
    
    print(f"[INFO] Trovate {len(strategie_strutturali)} strategie strutturali per 4IV. Verranno generati {len(strategie_strutturali) * len(permutazioni_stats)} piani totali.")

    # 3. Itera su ogni STRATEGIA
    for strategia in strategie_strutturali:
        # E per ogni STRATEGIA, itera su ogni PERMUTAZIONE DI STATS
        for perm in permutazioni_stats:
            id_piano_counter += 1
            legenda = {ruolo: stat for ruolo, stat in zip(iv_roles_for_legend, perm)}
            legenda[nat_role] = natura_desiderata
            
            piano_struttura = _crea_piano_4iv_natura_strutturato(strategia)
            
            piano = PianoCompleto(
                id_piano=id_piano_counter,
                ivs_target=list(ivs_desiderate),
                natura_target=natura_desiderata,
                legenda_ruoli=legenda,
                livelli=copy.deepcopy(piano_struttura)
            )
            piani_generati.append(piano)

    return piani_generati
