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

    ruoli_genitore_A = tuple(sorted(strategia_genitori_3iv[0]))
    ruoli_genitore_B = tuple(sorted(strategia_genitori_3iv[1]))
    ruoli_4iv = tuple(sorted(list(set(ruoli_genitore_A) | set(ruoli_genitore_B))))
    ruoli_3iv_n = tuple(sorted((ruoli_4iv[0], ruoli_4iv[1], ruoli_4iv[2])))
    target_finale = PokemonRichiesto(ruoli_iv=ruoli_4iv, ruolo_natura='V')
    genitore_4iv_final = PokemonRichiesto(ruoli_iv=ruoli_4iv)
    genitore_3iv_n_final = PokemonRichiesto(ruoli_iv=ruoli_3iv_n, ruolo_natura='V')
    genitore_A_3iv = PokemonRichiesto(ruoli_iv=ruoli_genitore_A)
    genitore_B_3iv = PokemonRichiesto(ruoli_iv=ruoli_genitore_B)
    ruoli_2iv_n = tuple(sorted((ruoli_3iv_n[0], ruoli_3iv_n[1])))
    genitore_2iv_n = PokemonRichiesto(ruoli_iv=ruoli_2iv_n, ruolo_natura='V')
    ruoli_2iv_complemento = tuple(sorted((ruoli_3iv_n[0], ruoli_3iv_n[2])))
    genitore_2iv_complemento = PokemonRichiesto(ruoli_iv=ruoli_2iv_complemento)
    gen_A_p1 = PokemonRichiesto(ruoli_iv=tuple(sorted((ruoli_genitore_A[0], ruoli_genitore_A[1]))))
    gen_A_p2 = PokemonRichiesto(ruoli_iv=tuple(sorted((ruoli_genitore_A[0], ruoli_genitore_A[2]))))
    gen_B_p1 = PokemonRichiesto(ruoli_iv=tuple(sorted((ruoli_genitore_B[0], ruoli_genitore_B[1]))))
    gen_B_p2 = PokemonRichiesto(ruoli_iv=tuple(sorted((ruoli_genitore_B[0], ruoli_genitore_B[2]))))
    gen_2iv_n_p1 = PokemonRichiesto(ruoli_iv=(ruoli_2iv_n[0],), ruolo_natura='V')
    gen_2iv_n_p2 = PokemonRichiesto(ruoli_iv=ruoli_2iv_n)

    b, g, r, y = ruoli_4iv

    livello1 = Livello(1, [
        Accoppiamento(PokemonRichiesto(ruoli_iv=(b,)), PokemonRichiesto(ruoli_iv=(g,)), PokemonRichiesto(ruoli_iv=(b, g))),
        Accoppiamento(PokemonRichiesto(ruoli_iv=(b,)), PokemonRichiesto(ruoli_iv=(r,)), PokemonRichiesto(ruoli_iv=(b, r))),
        Accoppiamento(PokemonRichiesto(ruoli_iv=(b,)), PokemonRichiesto(ruoli_iv=(y,)), PokemonRichiesto(ruoli_iv=(b, y))),
        Accoppiamento(PokemonRichiesto(ruoli_iv=(g,)), PokemonRichiesto(ruoli_iv=(r,)), PokemonRichiesto(ruoli_iv=(g, r))),
        Accoppiamento(PokemonRichiesto(ruoli_iv=(g,)), PokemonRichiesto(ruoli_iv=(y,)), PokemonRichiesto(ruoli_iv=(g, y))),
        Accoppiamento(PokemonRichiesto(ruoli_iv=(r,)), PokemonRichiesto(ruoli_iv=(y,)), PokemonRichiesto(ruoli_iv=(r, y))),
        Accoppiamento(PokemonRichiesto(ruolo_natura='V'), PokemonRichiesto(ruoli_iv=(b,)), PokemonRichiesto(ruoli_iv=(b,), ruolo_natura='V')),
        Accoppiamento(PokemonRichiesto(ruoli_iv=(g,)), PokemonRichiesto(ruoli_iv=(r,)), PokemonRichiesto(ruoli_iv=(g, r))),
    ])
    livello2 = Livello(2, [
        Accoppiamento(gen_A_p1, gen_A_p2, genitore_A_3iv),
        Accoppiamento(gen_B_p1, gen_B_p2, genitore_B_3iv),
        Accoppiamento(gen_2iv_n_p1, gen_2iv_n_p2, genitore_2iv_n),
        Accoppiamento(PokemonRichiesto(ruoli_iv=(g,y)), PokemonRichiesto(ruoli_iv=(r,y)), PokemonRichiesto(ruoli_iv=(g,r,y))),
    ])
    livello3 = Livello(3, [
        Accoppiamento(genitore_A_3iv, genitore_B_3iv, genitore_4iv_final),
        Accoppiamento(genitore_2iv_n, genitore_2iv_complemento, genitore_3iv_n_final),
    ])
    livello4 = Livello(4, [
        Accoppiamento(genitore_4iv_final, genitore_3iv_n_final, target_finale)
    ])
    return [livello1, livello2, livello3, livello4]

def _crea_piano_3iv_natura_strutturato(strategia_3iv: Tuple[str, str, str]) -> List[Livello]:
    iv_a, iv_b, iv_c = strategia_3iv[0], strategia_3iv[1], strategia_3iv[2]
    l1_child1 = PokemonRichiesto(ruoli_iv=tuple(sorted((iv_a, iv_b))))
    l1_accoppiamento1 = Accoppiamento(PokemonRichiesto(ruoli_iv=(iv_a,)), PokemonRichiesto(ruoli_iv=(iv_b,)), l1_child1)
    l1_child2 = PokemonRichiesto(ruoli_iv=(iv_c,), ruolo_natura='V')
    l1_accoppiamento2 = Accoppiamento(PokemonRichiesto(ruoli_iv=(iv_c,)), PokemonRichiesto(ruolo_natura='V'), l1_child2)
    livello1 = Livello(1, [l1_accoppiamento1, l1_accoppiamento2])
    target_finale = PokemonRichiesto(ruoli_iv=tuple(sorted((iv_a, iv_b, iv_c))), ruolo_natura='V')
    livello2 = Livello(2, [Accoppiamento(l1_child1, l1_child2, target_finale)])
    return [livello1, livello2]

def _crea_piano_5iv_natura_strutturato(strategia_5iv: Tuple[str, str, str, str, str]) -> List[Livello]:
    """
    Costruisce un albero di breeding 5IV+N.
    La strategia_5iv è una tupla di 5 ruoli IV, es: ('B', 'G', 'R', 'Y', 'O').
    """
    B, G, R, Y, O = strategia_5iv[0], strategia_5iv[1], strategia_5iv[2], strategia_5iv[3], strategia_5iv[4]
    V = 'V' # Nature Role

    # Target intermediates for the final cross (Level 2 children, Level 3 parents)
    # Ensure roles are sorted as per PokemonRichiesto's __post_init__
    parent_A_target = PokemonRichiesto(ruoli_iv=tuple(sorted((B,G,R))), ruolo_natura=V) # BGR+V
    parent_B_target = PokemonRichiesto(ruoli_iv=tuple(sorted((B,Y,O))))              # BYO

    # Livello 1 (Base components for Parent A and Parent B)
    # For Parent A (BGR+V)
    l1_A_p1_base = PokemonRichiesto(ruoli_iv=(B,))
    l1_A_p2_base = PokemonRichiesto(ruoli_iv=(G,))
    l1_A_child1 = PokemonRichiesto(ruoli_iv=tuple(sorted((B,G)))) # BG
    l1_A_accoppiamento1 = Accoppiamento(l1_A_p1_base, l1_A_p2_base, l1_A_child1)

    l1_A_p3_base = PokemonRichiesto(ruoli_iv=(R,))
    l1_A_p4_base = PokemonRichiesto(ruolo_natura=V) # Pure Nature donor
    l1_A_child2 = PokemonRichiesto(ruoli_iv=(R,), ruolo_natura=V) # R+V
    l1_A_accoppiamento2 = Accoppiamento(l1_A_p3_base, l1_A_p4_base, l1_A_child2)

    # For Parent B (BYO)
    l1_B_p1_base = PokemonRichiesto(ruoli_iv=(B,)) # Same as l1_A_p1_base conceptually
    l1_B_p2_base = PokemonRichiesto(ruoli_iv=(Y,))
    l1_B_child1 = PokemonRichiesto(ruoli_iv=tuple(sorted((B,Y)))) # BY
    l1_B_accoppiamento1 = Accoppiamento(l1_B_p1_base, l1_B_p2_base, l1_B_child1)

    l1_B_p3_base = PokemonRichiesto(ruoli_iv=(O,)) # O
    # l1_B_child2 is just the O Pokemon, conceptually from O + dummy parent
    l1_B_child2 = PokemonRichiesto(ruoli_iv=(O,))
    l1_B_accoppiamento2 = Accoppiamento(l1_B_p3_base, PokemonRichiesto(ruoli_iv=()), l1_B_child2)

    livello1 = Livello(1, [l1_A_accoppiamento1, l1_A_accoppiamento2, l1_B_accoppiamento1, l1_B_accoppiamento2])

    # Level 2 (Constructing Parent A and Parent B)
    # BGR+V from (BG) and (R+V)
    l2_accoppiamento_A = Accoppiamento(l1_A_child1, l1_A_child2, parent_A_target)
    # BYO from (BY) and (O)
    l2_accoppiamento_B = Accoppiamento(l1_B_child1, l1_B_child2, parent_B_target)
    livello2 = Livello(2, [l2_accoppiamento_A, l2_accoppiamento_B])

    # Level 3 (Final Target)
    # BGRYO+V from (BGR+V) and (BYO)
    target_finale = PokemonRichiesto(ruoli_iv=tuple(sorted((B,G,R,Y,O))), ruolo_natura=V)
    livello3 = Livello(3, [Accoppiamento(parent_A_target, parent_B_target, target_finale)])

    return [livello1, livello2, livello3]

def esegui_generazione(num_iv: int, ivs_desiderate: List[str], natura_desiderata: Optional[str]) -> List[PianoCompleto]:
    piani_generati = []
    ha_natura = bool(natura_desiderata)
    CANONICAL_IV_ROLES = ['B', 'G', 'R', 'Y', 'O', 'I']
    nat_role = 'V'

    if len(ivs_desiderate) != num_iv:
        print(f"[ERRORE] Il numero di IVs richiesti ({len(ivs_desiderate)}) non corrisponde al num_iv specificato ({num_iv}).")
        return []
    if not ha_natura:
        print(f"[AVVISO] Questo motore attualmente necessita di una natura specificata.")
        return []

    iv_roles_for_legend = CANONICAL_IV_ROLES[:num_iv]
    permutazioni_stats = list(itertools.permutations(ivs_desiderate))
    id_piano_counter = 0

    if num_iv == 4:
        iv_roles_base = CANONICAL_IV_ROLES[:4]
        combinazioni_3iv = list(itertools.combinations(iv_roles_base, 3))
        strategie_strutturali = []
        for pair in itertools.combinations(combinazioni_3iv, 2):
            unione_ivs = set(pair[0]) | set(pair[1])
            if len(unione_ivs) == 4:
                strategie_strutturali.append(pair)
        if strategie_strutturali:
            print(f"[INFO] Trovate {len(strategie_strutturali)} strategie strutturali per 4IV. Verranno generati {len(strategie_strutturali) * len(permutazioni_stats)} piani totali.")
        for strategia_tuple_3iv_parents in strategie_strutturali:
            for perm in permutazioni_stats:
                id_piano_counter += 1
                legenda = {ruolo: stat for ruolo, stat in zip(iv_roles_for_legend, perm)}
                legenda[nat_role] = natura_desiderata
                piano_struttura = _crea_piano_4iv_natura_strutturato(strategia_tuple_3iv_parents)
                piano = PianoCompleto(
                    id_piano=id_piano_counter,
                    ivs_target=list(ivs_desiderate),
                    natura_target=natura_desiderata,
                    legenda_ruoli=legenda,
                    livelli=copy.deepcopy(piano_struttura)
                )
                piani_generati.append(piano)
    elif num_iv == 3:
        iv_roles_base = CANONICAL_IV_ROLES[:3]
        strategia_3iv_roles = tuple(iv_roles_base)
        print(f"[INFO] Generazione piani per 3IV+Natura in corso... Verranno generati {len(permutazioni_stats)} piani totali.")
        for perm in permutazioni_stats:
            id_piano_counter += 1
            legenda = {ruolo: stat for ruolo, stat in zip(iv_roles_for_legend, perm)}
            legenda[nat_role] = natura_desiderata
            piano_struttura = _crea_piano_3iv_natura_strutturato(strategia_3iv_roles)
            piano = PianoCompleto(
                id_piano=id_piano_counter,
                ivs_target=list(ivs_desiderate),
                natura_target=natura_desiderata,
                legenda_ruoli=legenda,
                livelli=copy.deepcopy(piano_struttura)
            )
            piani_generati.append(piano)
    elif num_iv == 5:
        iv_roles_base = CANONICAL_IV_ROLES[:5]
        strategia_5iv_roles = tuple(iv_roles_base) # e.g., ('B', 'G', 'R', 'Y', 'O')
        print(f"[INFO] Generazione piani per 5IV+Natura in corso... Verranno generati {len(permutazioni_stats)} piani totali.")
        for perm in permutazioni_stats: # perm is a permutation of ivs_desiderate e.g. ("HP", "Atk", "Def", "SpA", "Spe")
            id_piano_counter += 1
            # Legenda maps canonical roles (B,G,R,Y,O) to actual stats from perm
            legenda = {ruolo: stat for ruolo, stat in zip(iv_roles_for_legend, perm)}
            legenda[nat_role] = natura_desiderata

            piano_struttura = _crea_piano_5iv_natura_strutturato(strategia_5iv_roles)

            piano = PianoCompleto(
                id_piano=id_piano_counter,
                ivs_target=list(ivs_desiderate),
                natura_target=natura_desiderata,
                legenda_ruoli=legenda,
                livelli=copy.deepcopy(piano_struttura)
            )
            piani_generati.append(piano)
    else:
        print(f"[ERRORE] Numero di IV ({num_iv}) non supportato.")
        return []

    return piani_generati
