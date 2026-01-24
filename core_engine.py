import itertools
import copy
from typing import List, Dict, Optional, Tuple, Set

from structures import PokemonRichiesto, Accoppiamento, Livello, PianoCompleto

def _mirror_structure(livelli_originali: List[Livello]) -> List[Livello]:
    """
    Creates a deep copy of the plan structure and swaps genitore1 (Mother/Species)
    and genitore2 (Father/Donor) for every coupling.
    This ensures that plans are evaluated for both gender configurations.
    """
    livelli_new = copy.deepcopy(livelli_originali)
    for livello in livelli_new:
        for acc in livello.accoppiamenti:
            acc.genitore1, acc.genitore2 = acc.genitore2, acc.genitore1
    return livelli_new

# NOTE: Le funzioni _crea_piano_* sono state mantenute come fornite,
# poiché l'errore risiedeva nella logica di generazione delle strategie
# all'interno di `esegui_generazione`.

def _crea_piano_4iv_natura_strutturato(strategia_genitori_3iv: Tuple[Tuple[str, ...], Tuple[str, ...]]) -> List[Livello]:
    """
    Crea la struttura di un piano per un Pokémon 4IV+Natura, seguendo la logica esplicita
    e il numero di accoppiamenti richiesti dall'utente, che prevede la creazione di
    istanze multiple di Pokémon intermedi.
    """
    # --- Ruoli Canonici ---
    V, B, G, R, Y = 'V', 'B', 'G', 'R', 'Y'

    # --- Livello 0 (Base Pokémon) ---
    # Definiamo i Pokémon base con 1 IV o solo Natura.
    # Ne serviranno istanze multiple, ma le definiamo una volta per chiarezza.
    v_n_base = PokemonRichiesto(ruolo_natura=V)
    b_1iv_base = PokemonRichiesto(ruoli_iv=(B,))
    g_1iv_base = PokemonRichiesto(ruoli_iv=(G,))
    r_1iv_base = PokemonRichiesto(ruoli_iv=(R,))
    y_1iv_base = PokemonRichiesto(ruoli_iv=(Y,))

    # --- Livello 1: Creazione di istanze multiple di intermedi 2IV e 1IV+N ---
    # Come da logica utente, creiamo duplicati per ogni accoppiamento successivo.
    vb_1iv_n = PokemonRichiesto(ruoli_iv=(B,), ruolo_natura=V)

    bg_2iv_instances = [PokemonRichiesto(ruoli_iv=(B, G)) for _ in range(3)]
    gr_2iv_instances = [PokemonRichiesto(ruoli_iv=(G, R)) for _ in range(3)]
    gy_2iv_instances = [PokemonRichiesto(ruoli_iv=(G, Y)) for _ in range(1)]

    livello1 = Livello(1, [
        Accoppiamento(v_n_base, b_1iv_base, vb_1iv_n),
        # 3 accoppiamenti per creare 3 BG[2IV]
        Accoppiamento(b_1iv_base, g_1iv_base, bg_2iv_instances[0]),
        Accoppiamento(b_1iv_base, g_1iv_base, bg_2iv_instances[1]),
        Accoppiamento(b_1iv_base, g_1iv_base, bg_2iv_instances[2]),
        # 3 accoppiamenti per creare 3 GR[2IV]
        Accoppiamento(g_1iv_base, r_1iv_base, gr_2iv_instances[0]),
        Accoppiamento(g_1iv_base, r_1iv_base, gr_2iv_instances[1]),
        Accoppiamento(g_1iv_base, r_1iv_base, gr_2iv_instances[2]),
        # 1 accoppiamento per creare 1 GY[2IV]
        Accoppiamento(g_1iv_base, y_1iv_base, gy_2iv_instances[0]),
    ])

    # --- Livello 2: Combinazione a 3IV e 2IV+N ---
    vbg_2iv_n = PokemonRichiesto(ruoli_iv=(B, G), ruolo_natura=V)
    bgr_3iv_instance_1 = PokemonRichiesto(ruoli_iv=(B, G, R))
    bgr_3iv_instance_2 = PokemonRichiesto(ruoli_iv=(B, G, R))
    gry_3iv = PokemonRichiesto(ruoli_iv=(G, R, Y))

    livello2 = Livello(2, [
        Accoppiamento(vb_1iv_n, bg_2iv_instances[0], vbg_2iv_n),
        Accoppiamento(bg_2iv_instances[1], gr_2iv_instances[0], bgr_3iv_instance_1),
        Accoppiamento(bg_2iv_instances[2], gr_2iv_instances[1], bgr_3iv_instance_2),
        Accoppiamento(gr_2iv_instances[2], gy_2iv_instances[0], gry_3iv),
    ])

    # --- Livello 3: Creazione dei genitori finali (4IV e 3IV+N) ---
    vbgr_3iv_n = PokemonRichiesto(ruoli_iv=(B, G, R), ruolo_natura=V)
    bgry_4iv = PokemonRichiesto(ruoli_iv=(B, G, R, Y))

    livello3 = Livello(3, [
        Accoppiamento(vbg_2iv_n, bgr_3iv_instance_1, vbgr_3iv_n),
        Accoppiamento(bgr_3iv_instance_2, gry_3iv, bgry_4iv),
    ])

    # --- Livello 4: Accoppiamento Finale ---
    vbgry_4iv_n = PokemonRichiesto(ruoli_iv=(B, G, R, Y), ruolo_natura=V)

    livello4 = Livello(4, [
        Accoppiamento(vbgr_3iv_n, bgry_4iv, vbgry_4iv_n)
    ])

    return [livello1, livello2, livello3, livello4]

def _crea_piano_4iv_senza_natura_strutturato(strategia_genitori_3iv: Tuple[Tuple[str, ...], Tuple[str, ...]]) -> List[Livello]:
    """Crea la struttura di un piano per un Pokémon 4IV (senza natura) basata su una specifica strategia di genitori 3IV."""
    ruoli_genitore_A = tuple(sorted(strategia_genitori_3iv[0])); ruoli_genitore_B = tuple(sorted(strategia_genitori_3iv[1]))
    ruoli_4iv_target = tuple(sorted(list(set(ruoli_genitore_A) | set(ruoli_genitore_B)))); target_4iv = PokemonRichiesto(ruoli_iv=ruoli_4iv_target)
    if len(ruoli_4iv_target) != 4: raise ValueError(f"Strategia non produce 4IV: {ruoli_4iv_target}")
    genitore_A_3iv = PokemonRichiesto(ruoli_iv=ruoli_genitore_A); genitore_B_3iv = PokemonRichiesto(ruoli_iv=ruoli_genitore_B)
    gen_A_p1_2iv = PokemonRichiesto(ruoli_iv=tuple(sorted((ruoli_genitore_A[0], ruoli_genitore_A[1])))); gen_A_p2_2iv = PokemonRichiesto(ruoli_iv=tuple(sorted((ruoli_genitore_A[0], ruoli_genitore_A[2]))))
    gen_B_p1_2iv = PokemonRichiesto(ruoli_iv=tuple(sorted((ruoli_genitore_B[0], ruoli_genitore_B[1])))); gen_B_p2_2iv = PokemonRichiesto(ruoli_iv=tuple(sorted((ruoli_genitore_B[0], ruoli_genitore_B[2]))))
    livello1 = Livello(1, [Accoppiamento(PokemonRichiesto(ruoli_iv=(gen_A_p1_2iv.ruoli_iv[0],)), PokemonRichiesto(ruoli_iv=(gen_A_p1_2iv.ruoli_iv[1],)), gen_A_p1_2iv), Accoppiamento(PokemonRichiesto(ruoli_iv=(gen_A_p2_2iv.ruoli_iv[0],)), PokemonRichiesto(ruoli_iv=(gen_A_p2_2iv.ruoli_iv[1],)), gen_A_p2_2iv), Accoppiamento(PokemonRichiesto(ruoli_iv=(gen_B_p1_2iv.ruoli_iv[0],)), PokemonRichiesto(ruoli_iv=(gen_B_p1_2iv.ruoli_iv[1],)), gen_B_p1_2iv), Accoppiamento(PokemonRichiesto(ruoli_iv=(gen_B_p2_2iv.ruoli_iv[0],)), PokemonRichiesto(ruoli_iv=(gen_B_p2_2iv.ruoli_iv[1],)), gen_B_p2_2iv)])
    livello2 = Livello(2, [Accoppiamento(gen_A_p1_2iv, gen_A_p2_2iv, genitore_A_3iv), Accoppiamento(gen_B_p1_2iv, gen_B_p2_2iv, genitore_B_3iv)])
    livello3 = Livello(3, [Accoppiamento(genitore_A_3iv, genitore_B_3iv, target_4iv)])
    return [livello1, livello2, livello3]

def _crea_piano_5iv_natura_strutturato(strategia_5iv_n: Tuple[Tuple[str, ...], Tuple[str, ...]]) -> List[Livello]:
    """Crea la struttura di un piano per un Pokémon 5IV+Natura, seguendo un albero genealogico esplicito e senza riutilizzo."""
    # Ruoli Canonici: B,G,R,Y,O per IVs; V per Natura. 'Y' sostituisce 'I' del piano utente.

    # --- Livello 0 (Base): Pokémon con 1IV o solo Natura ---
    # Totali necessari calcolati dall'albero di dipendenze:
    # V(1), B(2), G(11), R(10), Y(6), O(2)
    # Derivazione:
    # L2->L1 richiede: BG(1), BR(1), VG(1), GR(5), GY(4), RY(2), RO(2)
    # Totale Base:
    # B: BG(1) + BR(1) = 2
    # G: BG(1) + VG(1) + GR(5) + GY(4) = 11
    # R: BR(1) + GR(5) + RY(2) + RO(2) = 10
    # Y: GY(4) + RY(2) = 6
    # O: RO(2) = 2
    # V: VG(1) = 1

    v_n = PokemonRichiesto(ruolo_natura='V')
    # Usiamo pop() quindi le liste sono invertite per comodità
    g_1 = [PokemonRichiesto(ruoli_iv=('G',)) for _ in range(11)]
    r_1 = [PokemonRichiesto(ruoli_iv=('R',)) for _ in range(10)]
    y_1 = [PokemonRichiesto(ruoli_iv=('Y',)) for _ in range(6)]
    o_1 = [PokemonRichiesto(ruoli_iv=('O',)) for _ in range(2)]
    b_1 = [PokemonRichiesto(ruoli_iv=('B',)) for _ in range(2)]

    # --- Livello 1: Creazione dei componenti 2IV e 1IV+N ---
    vg_1n = PokemonRichiesto(ruoli_iv=('G',), ruolo_natura='V')
    bg_2 = PokemonRichiesto(ruoli_iv=('B', 'G'))
    br_2 = PokemonRichiesto(ruoli_iv=('B', 'R'))
    gr_2 = [PokemonRichiesto(ruoli_iv=('G', 'R')) for _ in range(5)]
    gy_2 = [PokemonRichiesto(ruoli_iv=('G', 'Y')) for _ in range(4)]
    ry_2 = [PokemonRichiesto(ruoli_iv=('R', 'Y')) for _ in range(2)]
    ro_2 = [PokemonRichiesto(ruoli_iv=('R', 'O')) for _ in range(2)]

    livello1 = Livello(1, [
        Accoppiamento(v_n, g_1.pop(), vg_1n),
        Accoppiamento(b_1.pop(), g_1.pop(), bg_2),
        Accoppiamento(b_1.pop(), r_1.pop(), br_2),
    ] + [Accoppiamento(g_1.pop(), r_1.pop(), p) for p in gr_2]
      + [Accoppiamento(g_1.pop(), y_1.pop(), p) for p in gy_2]
      + [Accoppiamento(r_1.pop(), y_1.pop(), p) for p in ry_2]
      + [Accoppiamento(r_1.pop(), o_1.pop(), p) for p in ro_2]
    )

    # --- Livello 2: Combinazione a 3IV e 2IV+N ---
    bgr_3 = PokemonRichiesto(ruoli_iv=('B', 'G', 'R'))
    gry_3 = [PokemonRichiesto(ruoli_iv=('G', 'R', 'Y')) for _ in range(4)]
    ryo_3 = [PokemonRichiesto(ruoli_iv=('R', 'Y', 'O')) for _ in range(2)]
    vgr_2n = PokemonRichiesto(ruoli_iv=('G', 'R'), ruolo_natura='V')

    livello2 = Livello(2, [
        Accoppiamento(bg_2, br_2, bgr_3),
        Accoppiamento(vg_1n, gr_2.pop(), vgr_2n),
    ] + [Accoppiamento(gr_2.pop(), gy_2.pop(), p) for p in gry_3]
      + [Accoppiamento(ry_2.pop(), ro_2.pop(), p) for p in ryo_3]
    )

    # --- Livello 3: Creazione dei Pokémon 4IV e 3IV+N ---
    bgry_4 = PokemonRichiesto(ruoli_iv=('B', 'G', 'R', 'Y'))
    gory_4 = [PokemonRichiesto(ruoli_iv=('G', 'O', 'R', 'Y')) for _ in range(2)]
    vgry_3n = PokemonRichiesto(ruoli_iv=('G', 'R', 'Y'), ruolo_natura='V')

    livello3 = Livello(3, [
        Accoppiamento(bgr_3, gry_3.pop(), bgry_4),
        Accoppiamento(vgr_2n, gry_3.pop(), vgry_3n),
        Accoppiamento(gry_3.pop(), ryo_3.pop(), gory_4[0]),
        Accoppiamento(gry_3.pop(), ryo_3.pop(), gory_4[1]),
    ])

    # --- Livello 4: Genitori Finali ---
    bgory_5 = PokemonRichiesto(ruoli_iv=('B', 'G', 'R', 'Y', 'O'))
    vgory_4n = PokemonRichiesto(ruoli_iv=('G', 'R', 'Y', 'O'), ruolo_natura='V')

    livello4 = Livello(4, [
        Accoppiamento(bgry_4, gory_4[0], bgory_5),
        Accoppiamento(vgry_3n, gory_4[1], vgory_4n)
    ])

    # --- Livello 5 (Target) ---
    vbgory_5n = PokemonRichiesto(ruoli_iv=('B', 'G', 'R', 'Y', 'O'), ruolo_natura='V')
    livello5 = Livello(5, [Accoppiamento(bgory_5, vgory_4n, vbgory_5n)])

    return [livello1, livello2, livello3, livello4, livello5]

def _crea_piano_5iv_senza_natura_strutturato(strategia_genitori_4iv: Tuple[Tuple[str, ...], Tuple[str, ...]]) -> List[Livello]:
    """
    Crea la struttura di un piano per un Pokémon 5IV (senza natura) basata su una
    specifica strategia di genitori 4IV, garantendo che ogni Pokémon intermedio
    sia un'istanza unica per evitare riutilizzi impliciti.
    """
    ruoli_genitore_A_4iv = tuple(sorted(strategia_genitori_4iv[0]))
    ruoli_genitore_B_4iv = tuple(sorted(strategia_genitori_4iv[1]))

    ruoli_target_5iv = tuple(sorted(list(set(ruoli_genitore_A_4iv) | set(ruoli_genitore_B_4iv))))
    if len(ruoli_target_5iv) != 5:
        raise ValueError(f"La strategia dei genitori 4IV non produce un 5IV. Ruoli uniti: {ruoli_target_5iv}")

    # --- Livello 4 (Target) ---
    target_5iv = PokemonRichiesto(ruoli_iv=ruoli_target_5iv)
    genitore_A_4iv = PokemonRichiesto(ruoli_iv=ruoli_genitore_A_4iv)
    genitore_B_4iv = PokemonRichiesto(ruoli_iv=ruoli_genitore_B_4iv)
    livello4 = Livello(4, [Accoppiamento(genitore_A_4iv, genitore_B_4iv, target_5iv)])

    # --- Livello 3 (Genitori 4IV) ---
    # Decomposizione del genitore A
    rA4 = ruoli_genitore_A_4iv
    gen_A_p1_3iv = PokemonRichiesto(ruoli_iv=tuple(sorted((rA4[0], rA4[1], rA4[2]))))
    gen_A_p2_3iv = PokemonRichiesto(ruoli_iv=tuple(sorted((rA4[0], rA4[1], rA4[3])))) # Potrebbe essere anche (rA4[0], rA4[2], rA4[3]), la logica originale usa questa combinazione
    # Decomposizione del genitore B
    rB4 = ruoli_genitore_B_4iv
    gen_B_p1_3iv = PokemonRichiesto(ruoli_iv=tuple(sorted((rB4[0], rB4[1], rB4[2]))))
    gen_B_p2_3iv = PokemonRichiesto(ruoli_iv=tuple(sorted((rB4[0], rB4[1], rB4[3]))))

    livello3 = Livello(3, [
        Accoppiamento(gen_A_p1_3iv, gen_A_p2_3iv, genitore_A_4iv),
        Accoppiamento(gen_B_p1_3iv, gen_B_p2_3iv, genitore_B_4iv)
    ])

    # --- Livello 2 (Genitori 3IV) ---
    # Decomposizione dei 4 genitori 3IV in 8 genitori 2IV.
    # Ogni Pokémon qui è un'istanza distinta, anche se ha gli stessi IV.
    rA_p1_3 = gen_A_p1_3iv.ruoli_iv
    gen_A_p1_c1_2iv = PokemonRichiesto(ruoli_iv=tuple(sorted((rA_p1_3[0], rA_p1_3[1]))))
    gen_A_p1_c2_2iv = PokemonRichiesto(ruoli_iv=tuple(sorted((rA_p1_3[0], rA_p1_3[2]))))

    rA_p2_3 = gen_A_p2_3iv.ruoli_iv
    gen_A_p2_c1_2iv = PokemonRichiesto(ruoli_iv=tuple(sorted((rA_p2_3[0], rA_p2_3[1]))))
    gen_A_p2_c2_2iv = PokemonRichiesto(ruoli_iv=tuple(sorted((rA_p2_3[0], rA_p2_3[2]))))

    rB_p1_3 = gen_B_p1_3iv.ruoli_iv
    gen_B_p1_c1_2iv = PokemonRichiesto(ruoli_iv=tuple(sorted((rB_p1_3[0], rB_p1_3[1]))))
    gen_B_p1_c2_2iv = PokemonRichiesto(ruoli_iv=tuple(sorted((rB_p1_3[0], rB_p1_3[2]))))

    rB_p2_3 = gen_B_p2_3iv.ruoli_iv
    gen_B_p2_c1_2iv = PokemonRichiesto(ruoli_iv=tuple(sorted((rB_p2_3[0], rB_p2_3[1]))))
    gen_B_p2_c2_2iv = PokemonRichiesto(ruoli_iv=tuple(sorted((rB_p2_3[0], rB_p2_3[2]))))

    livello2 = Livello(2, [
        Accoppiamento(gen_A_p1_c1_2iv, gen_A_p1_c2_2iv, gen_A_p1_3iv),
        Accoppiamento(gen_A_p2_c1_2iv, gen_A_p2_c2_2iv, gen_A_p2_3iv),
        Accoppiamento(gen_B_p1_c1_2iv, gen_B_p1_c2_2iv, gen_B_p1_3iv),
        Accoppiamento(gen_B_p2_c1_2iv, gen_B_p2_c2_2iv, gen_B_p2_3iv)
    ])

    # --- Livello 1 (Genitori 2IV) ---
    # Creazione degli 8 genitori 2IV a partire da genitori 1IV.
    # Ogni accoppiamento è esplicito.
    accoppiamenti_l1 = [
        Accoppiamento(PokemonRichiesto(ruoli_iv=(gen_A_p1_c1_2iv.ruoli_iv[0],)), PokemonRichiesto(ruoli_iv=(gen_A_p1_c1_2iv.ruoli_iv[1],)), gen_A_p1_c1_2iv),
        Accoppiamento(PokemonRichiesto(ruoli_iv=(gen_A_p1_c2_2iv.ruoli_iv[0],)), PokemonRichiesto(ruoli_iv=(gen_A_p1_c2_2iv.ruoli_iv[1],)), gen_A_p1_c2_2iv),
        Accoppiamento(PokemonRichiesto(ruoli_iv=(gen_A_p2_c1_2iv.ruoli_iv[0],)), PokemonRichiesto(ruoli_iv=(gen_A_p2_c1_2iv.ruoli_iv[1],)), gen_A_p2_c1_2iv),
        Accoppiamento(PokemonRichiesto(ruoli_iv=(gen_A_p2_c2_2iv.ruoli_iv[0],)), PokemonRichiesto(ruoli_iv=(gen_A_p2_c2_2iv.ruoli_iv[1],)), gen_A_p2_c2_2iv),
        Accoppiamento(PokemonRichiesto(ruoli_iv=(gen_B_p1_c1_2iv.ruoli_iv[0],)), PokemonRichiesto(ruoli_iv=(gen_B_p1_c1_2iv.ruoli_iv[1],)), gen_B_p1_c1_2iv),
        Accoppiamento(PokemonRichiesto(ruoli_iv=(gen_B_p1_c2_2iv.ruoli_iv[0],)), PokemonRichiesto(ruoli_iv=(gen_B_p1_c2_2iv.ruoli_iv[1],)), gen_B_p1_c2_2iv),
        Accoppiamento(PokemonRichiesto(ruoli_iv=(gen_B_p2_c1_2iv.ruoli_iv[0],)), PokemonRichiesto(ruoli_iv=(gen_B_p2_c1_2iv.ruoli_iv[1],)), gen_B_p2_c1_2iv),
        Accoppiamento(PokemonRichiesto(ruoli_iv=(gen_B_p2_c2_2iv.ruoli_iv[0],)), PokemonRichiesto(ruoli_iv=(gen_B_p2_c2_2iv.ruoli_iv[1],)), gen_B_p2_c2_2iv),
    ]
    livello1 = Livello(1, accoppiamenti_l1)

    return [livello1, livello2, livello3, livello4]

def _crea_piano_3iv_natura_strutturato(strategia_3iv_n: Tuple[Tuple[str, ...], Tuple[str, ...], Tuple[str, ...]]) -> List[Livello]:
    """Crea la struttura di un piano per un Pokémon 3IV+Natura, seguendo il modello corretto a 3 livelli."""
    # La strategia passata è ignorata perché basata su un modello errato.
    # Si costruisce il piano usando ruoli canonici (B, G, R per IVs), che verranno poi mappati.

    # Ruoli Canonici: B, G, R per IVs; V per Natura.

    # --- Livello 1: Creazione dei componenti base ---
    b_1iv = PokemonRichiesto(ruoli_iv=('B',))
    g_1iv = PokemonRichiesto(ruoli_iv=('G',))
    r_1iv = PokemonRichiesto(ruoli_iv=('R',))
    v_natura = PokemonRichiesto(ruolo_natura='V')

    # Risultati del Livello 1
    vb_1iv_n = PokemonRichiesto(ruoli_iv=('B',), ruolo_natura='V')
    bg1_2iv = PokemonRichiesto(ruoli_iv=('B', 'G'))
    bg2_2iv = PokemonRichiesto(ruoli_iv=('B', 'G')) # Necessario un duplicato per il piano
    br_2iv = PokemonRichiesto(ruoli_iv=('B', 'R'))

    livello1 = Livello(1, [
        Accoppiamento(v_natura, b_1iv, vb_1iv_n),
        Accoppiamento(b_1iv, g_1iv, bg1_2iv),
        Accoppiamento(b_1iv, g_1iv, bg2_2iv),
        Accoppiamento(b_1iv, r_1iv, br_2iv),
    ])

    # --- Livello 2: Creazione dei genitori finali ---
    vbg_2iv_n = PokemonRichiesto(ruoli_iv=('B', 'G'), ruolo_natura='V') # Genitore Natura
    bgr_3iv = PokemonRichiesto(ruoli_iv=('B', 'G', 'R')) # Genitore IV

    livello2 = Livello(2, [
        Accoppiamento(vb_1iv_n, bg1_2iv, vbg_2iv_n),
        Accoppiamento(bg2_2iv, br_2iv, bgr_3iv)
    ])

    # --- Livello 3: Accoppiamento finale ---
    vbgr_3iv_n = PokemonRichiesto(ruoli_iv=('B', 'G', 'R'), ruolo_natura='V') # Target

    livello3 = Livello(3, [
        Accoppiamento(vbg_2iv_n, bgr_3iv, vbgr_3iv_n)
    ])

    return [livello1, livello2, livello3]

def _crea_piano_3iv_senza_natura_strutturato(strategia_3iv: Tuple[Tuple[str, ...], Tuple[str, ...], Tuple[str, ...]]) -> List[Livello]:
    """Crea la struttura di un piano per un Pokémon 3IV (senza natura)."""
    target_roles=tuple(sorted(strategia_3iv[0])); p1_2iv_roles=tuple(sorted(strategia_3iv[1])); p2_2iv_roles=tuple(sorted(strategia_3iv[2]))
    if len(target_roles) != 3 or len(p1_2iv_roles) != 2 or len(p2_2iv_roles) != 2: raise ValueError("Strategia 3IV non valida: dimensioni ruoli errate.")
    if not (set(p1_2iv_roles) | set(p2_2iv_roles)) == set(target_roles): raise ValueError("Strategia 3IV non valida: unione genitori non corrisponde al target.")
    if len(set(p1_2iv_roles) & set(p2_2iv_roles)) != 1: raise ValueError("Strategia 3IV non valida: i genitori 2IV devono condividere esattamente un ruolo IV.")
    target_3iv=PokemonRichiesto(ruoli_iv=target_roles); parent1_2iv=PokemonRichiesto(ruoli_iv=p1_2iv_roles); parent2_2iv=PokemonRichiesto(ruoli_iv=p2_2iv_roles)
    p1_c1_1iv=PokemonRichiesto(ruoli_iv=(p1_2iv_roles[0],)); p1_c2_1iv=PokemonRichiesto(ruoli_iv=(p1_2iv_roles[1],))
    p2_c1_1iv=PokemonRichiesto(ruoli_iv=(p2_2iv_roles[0],)); p2_c2_1iv=PokemonRichiesto(ruoli_iv=(p2_2iv_roles[1],))
    livello1=Livello(1,[Accoppiamento(p1_c1_1iv,p1_c2_1iv,parent1_2iv),Accoppiamento(p2_c1_1iv,p2_c2_1iv,parent2_2iv)])
    livello2=Livello(2,[Accoppiamento(parent1_2iv,parent2_2iv,target_3iv)])
    return [livello1,livello2]

def _crea_piano_2iv_natura_strutturato(strategia_2iv_n: Tuple[Tuple[str, ...], str]) -> List[Livello]:
    """Crea la struttura di un piano per un Pokémon 2IV+Natura, seguendo lo schema a 2 livelli."""
    target_2_iv_roles = tuple(sorted(strategia_2iv_n[0]))
    # L'IV del genitore con natura, che funge da "ponte"
    bridge_iv_role = strategia_2iv_n[1]

    if len(target_2_iv_roles) != 2:
        raise ValueError("Strategia 2IV+N non valida: target_2_iv_roles deve avere 2 ruoli.")
    if bridge_iv_role not in target_2_iv_roles:
        raise ValueError("Strategia 2IV+N non valida: bridge_iv_role non è nei ruoli target.")

    # --- Definizione dei Pokémon nel piano ---

    # Target Finale
    target_2iv_n = PokemonRichiesto(ruoli_iv=target_2_iv_roles, ruolo_natura='V')

    # Genitori Finali (Livello 2)
    # Genitore con 1 IV + Natura
    parent_1iv_n = PokemonRichiesto(ruoli_iv=(bridge_iv_role,), ruolo_natura='V')
    # Genitore con 2 IV
    parent_2iv = PokemonRichiesto(ruoli_iv=target_2_iv_roles)

    # Nonni (Livello 1)
    # Nonni per il genitore con natura
    grandparent_nature = PokemonRichiesto(ruolo_natura='V')
    grandparent_bridge_iv = PokemonRichiesto(ruoli_iv=(bridge_iv_role,))

    # Nonni per il genitore con 2 IV
    grandparent_iv_1 = PokemonRichiesto(ruoli_iv=(target_2_iv_roles[0],))
    grandparent_iv_2 = PokemonRichiesto(ruoli_iv=(target_2_iv_roles[1],))

    # --- Creazione dei Livelli ---

    livello1 = Livello(1, [
        # Accoppiamento per creare Parent_N [VG (1IV+N)]
        Accoppiamento(grandparent_nature, grandparent_bridge_iv, parent_1iv_n),
        # Accoppiamento per creare Parent_IV [GR (2IV)]
        Accoppiamento(grandparent_iv_1, grandparent_iv_2, parent_2iv)
    ])

    livello2 = Livello(2, [
        # Accoppiamento finale per ottenere il target
        Accoppiamento(parent_1iv_n, parent_2iv, target_2iv_n)
    ])

    return [livello1, livello2]


def esegui_generazione(ivs_desiderate: List[str], natura_desiderata: Optional[str]) -> List[PianoCompleto]:
    """
    Funzione principale per generare tutti i possibili piani di breeding per un dato set di IV e natura.
    Seleziona la strategia appropriata e genera piani permutando le statistiche reali.
    """
    piani_generati: List[PianoCompleto] = []
    num_iv = len(ivs_desiderate)
    ha_natura = bool(natura_desiderata)

    CANONICAL_IV_ROLES = ['B', 'G', 'R', 'Y', 'O', 'I']
    NATURA_ROLE = 'V'

    iv_roles_for_legend = CANONICAL_IV_ROLES[:num_iv]
    permutazioni_stats = list(itertools.permutations(ivs_desiderate))

    id_piano_counter = 0
    lista_piani_base_livelli: List[List[Livello]] = []

    # Inizializza le liste di strategie per verifiche successive
    strategie_4iv_natura: List[Tuple[Tuple[str, ...], Tuple[str, ...]]] = []
    strategie_4iv_senza_natura: List[Tuple[Tuple[str, ...], Tuple[str, ...]]] = []
    strategie_5iv_natura: List[Tuple[Tuple[str, ...], Tuple[str, ...]]] = []
    strategie_5iv_senza_natura: List[Tuple[Tuple[str, ...], Tuple[str, ...]]] = []
    strategie_3iv_natura: List[Tuple[Tuple[str,...], Tuple[str,...], Tuple[str,...]]] = []
    strategie_3iv_senza_natura: List[Tuple[Tuple[str,...], Tuple[str,...], Tuple[str,...]]] = []
    strategie_2iv_natura: List[Tuple[Tuple[str,...], str]] = []


    print(f"[INFO] Inizio generazione per {num_iv}IV, Natura: {ha_natura}")

    if num_iv == 4 and ha_natura:
        iv_roles_base_4iv = CANONICAL_IV_ROLES[:4]
        combinazioni_3iv = list(itertools.combinations(iv_roles_base_4iv, 3))
        for pair in itertools.combinations(combinazioni_3iv, 2):
            if len(set(pair[0]) | set(pair[1])) == 4: strategie_4iv_natura.append(pair)
        if not strategie_4iv_natura: print(f"[AVVISO] Nessuna strategia 4IV+Natura.")
        else:
            print(f"[INFO] Trovate {len(strategie_4iv_natura)} strategie 4IV+Natura.")
            for strat in strategie_4iv_natura:
                try:
                    base_plan = _crea_piano_4iv_natura_strutturato(strat)
                    lista_piani_base_livelli.append(base_plan)
                    lista_piani_base_livelli.append(_mirror_structure(base_plan))
                except Exception as e: print(f"[ERRORE] Gen piano 4IV+N: {strat}, {e}")

    elif num_iv == 4 and not ha_natura:
        iv_roles_base_4iv = CANONICAL_IV_ROLES[:4]
        combinazioni_3iv = list(itertools.combinations(iv_roles_base_4iv, 3))
        for pair in itertools.combinations(combinazioni_3iv, 2):
            if len(set(pair[0]) | set(pair[1])) == 4: strategie_4iv_senza_natura.append(pair)
        if not strategie_4iv_senza_natura: print(f"[AVVISO] Nessuna strategia 4IV senza Natura.")
        else:
            print(f"[INFO] Trovate {len(strategie_4iv_senza_natura)} strategie 4IV senza Natura.")
            for strat in strategie_4iv_senza_natura:
                try:
                    base_plan = _crea_piano_4iv_senza_natura_strutturato(strat)
                    lista_piani_base_livelli.append(base_plan)
                    lista_piani_base_livelli.append(_mirror_structure(base_plan))
                except Exception as e: print(f"[ERRORE] Gen piano 4IV S/N: {strat}, {e}")

    elif num_iv == 5 and ha_natura:
        iv_roles_base_5iv = tuple(CANONICAL_IV_ROLES[:5])
        if len(iv_roles_base_5iv) < 5 : print(f"[ERRORE] Ruoli base IV ({len(iv_roles_base_5iv)}) insuff per 5IV+N.")
        else:
            for combo_4_roles in itertools.combinations(iv_roles_base_5iv, 4):
                strategie_5iv_natura.append( (iv_roles_base_5iv, tuple(sorted(combo_4_roles))) )
        if not strategie_5iv_natura: print(f"[AVVISO] Nessuna strategia 5IV+Natura.")
        else:
            print(f"[INFO] Trovate {len(strategie_5iv_natura)} strategie 5IV+Natura.")
            for strat in strategie_5iv_natura:
                try:
                    base_plan = _crea_piano_5iv_natura_strutturato(strat)
                    lista_piani_base_livelli.append(base_plan)
                    lista_piani_base_livelli.append(_mirror_structure(base_plan))
                except Exception as e: print(f"[ERRORE] Gen piano 5IV+N: {strat}, {e}")

    elif num_iv == 5 and not ha_natura:
        iv_roles_base_5iv = tuple(CANONICAL_IV_ROLES[:5])
        added_strategies_set: Set[Tuple[Tuple[str, ...], Tuple[str, ...]]] = set()
        if len(iv_roles_base_5iv) < 5: print(f"[ERRORE] Ruoli base IV ({len(iv_roles_base_5iv)}) insuff per 5IV S/N.")
        else:
            for parent_A_roles_tuple in itertools.combinations(iv_roles_base_5iv, 4):
                parent_A_roles_set = set(parent_A_roles_tuple)
                missing_role_set = set(iv_roles_base_5iv) - parent_A_roles_set
                if not missing_role_set: continue
                missing_role = list(missing_role_set)[0]
                for common_3_roles_tuple in itertools.combinations(parent_A_roles_tuple, 3):
                    parent_B_roles_list = list(common_3_roles_tuple)
                    parent_B_roles_list.append(missing_role)
                    parent_B_roles_tuple = tuple(sorted(parent_B_roles_list))
                    if len(set(parent_B_roles_tuple)) == 4:
                        s_A = tuple(sorted(parent_A_roles_tuple))
                        s_B = tuple(sorted(parent_B_roles_tuple))
                        if s_A == s_B: continue

                        # --- CORREZIONE APPLICATA QUI ---
                        # L'originale `tuple(sorted((s_A, s_B)))` confondeva Pylance.
                        # Questa versione è più esplicita e garantisce un tuple di dimensione 2,
                        # mantenendo l'ordinamento per l'univocità.
                        strategy = (s_A, s_B) if s_A < s_B else (s_B, s_A)
                        
                        if strategy not in added_strategies_set:
                            strategie_5iv_senza_natura.append(strategy)
                            added_strategies_set.add(strategy)

        if not strategie_5iv_senza_natura:
            print(f"[AVVISO] Nessuna strategia strutturale trovata per 5IV senza Natura.")
        else:
            print(f"[INFO] Trovate {len(strategie_5iv_senza_natura)} strategie strutturali per 5IV senza Natura.")
            for strategia_tuple in strategie_5iv_senza_natura:
                try:
                    piani_base = _crea_piano_5iv_senza_natura_strutturato(strategia_tuple)
                    lista_piani_base_livelli.append(piani_base)
                    lista_piani_base_livelli.append(_mirror_structure(piani_base))
                except Exception as e: print(f"[ERRORE] Gen piano 5IV S/N: {strategia_tuple}, {e}")

    elif num_iv == 3 and ha_natura:
        target_3_iv_roles = tuple(CANONICAL_IV_ROLES[:3])
        for i in range(3):
            common_role = target_3_iv_roles[i]
            other_r = [r for idx, r in enumerate(target_3_iv_roles) if idx != i]
            roles_for_2iv_n_parent = tuple(sorted((common_role, other_r[0])))
            roles_for_2iv_parent = tuple(sorted((common_role, other_r[1])))
            strategie_3iv_natura.append( (target_3_iv_roles, roles_for_2iv_n_parent, roles_for_2iv_parent) )

        if not strategie_3iv_natura:
            print(f"[AVVISO] Nessuna strategia strutturale trovata per 3IV+Natura.")
        else:
            print(f"[INFO] Trovate {len(strategie_3iv_natura)} strategie strutturali per 3IV+Natura.")
            for strategia_tuple in strategie_3iv_natura:
                try:
                    piani_base = _crea_piano_3iv_natura_strutturato(strategia_tuple)
                    lista_piani_base_livelli.append(piani_base)
                    lista_piani_base_livelli.append(_mirror_structure(piani_base))
                except Exception as e: print(f"[ERRORE] Gen piano 3IV+N: {strategia_tuple}, {e}")

    elif num_iv == 3 and not ha_natura:
        target_3_iv_roles = tuple(CANONICAL_IV_ROLES[:3])
        for i in range(3):
            common_role = target_3_iv_roles[i]
            other_roles = [r for idx, r in enumerate(target_3_iv_roles) if idx != i]
            parent1_2iv_roles = tuple(sorted((common_role, other_roles[0])))
            parent2_2iv_roles = tuple(sorted((common_role, other_roles[1])))
            strategie_3iv_senza_natura.append( (target_3_iv_roles, parent1_2iv_roles, parent2_2iv_roles) )

        if not strategie_3iv_senza_natura:
            print(f"[AVVISO] Nessuna strategia strutturale trovata per 3IV senza Natura.")
        else:
            print(f"[INFO] Trovate {len(strategie_3iv_senza_natura)} strategie strutturali per 3IV senza Natura.")
            for strategia_tuple in strategie_3iv_senza_natura:
                try:
                    piani_base = _crea_piano_3iv_senza_natura_strutturato(strategia_tuple)
                    lista_piani_base_livelli.append(piani_base)
                    lista_piani_base_livelli.append(_mirror_structure(piani_base))
                except Exception as e: print(f"[ERRORE] Gen piano 3IV S/N: {strategia_tuple}, {e}")

    elif num_iv == 2 and ha_natura:
        target_2_iv_roles = tuple(CANONICAL_IV_ROLES[:2])
        if len(target_2_iv_roles) == 2:
            strategie_2iv_natura.append( (target_2_iv_roles, target_2_iv_roles[0]) )
            strategie_2iv_natura.append( (target_2_iv_roles, target_2_iv_roles[1]) )

        if not strategie_2iv_natura:
            print(f"[AVVISO] Nessuna strategia strutturale trovata per 2IV+Natura.")
        else:
            print(f"[INFO] Trovate {len(strategie_2iv_natura)} strategie strutturali per 2IV+Natura.")
            for strategia_tuple in strategie_2iv_natura:
                try:
                    piani_base = _crea_piano_2iv_natura_strutturato(strategia_tuple)
                    lista_piani_base_livelli.append(piani_base)
                    lista_piani_base_livelli.append(_mirror_structure(piani_base))
                except Exception as e: print(f"[ERRORE] Gen piano 2IV+N: {strategia_tuple}, {e}")

    else:
        print(f"[AVVISO] La generazione per {num_iv}IV, Natura: {ha_natura} non è supportata o implementata.")

    if not lista_piani_base_livelli:
        if (num_iv in [2,3,4,5]):
             print(f"[AVVISO] Nessun piano base VALIDO generato per la richiesta: {num_iv}IV, Natura: {ha_natura}.")
        return []

    for piano_struttura_livelli in lista_piani_base_livelli:
        if not piano_struttura_livelli:
            print("[AVVISO] Saltata una struttura di piano base vuota/nulla.")
            continue
        for perm in permutazioni_stats:
            id_piano_counter += 1
            legenda = {r:s for r,s in zip(iv_roles_for_legend, perm)}
            if ha_natura:
                if not natura_desiderata:
                    print("[ERRORE] Natura richiesta ma non specificata. Piano saltato.")
                    continue
                legenda[NATURA_ROLE] = natura_desiderata
            piani_generati.append(PianoCompleto(id_piano_counter, list(ivs_desiderate), natura_desiderata, legenda, copy.deepcopy(piano_struttura_livelli)))

    if piani_generati:
        nat_s = (('+ ' + natura_desiderata) if ha_natura and natura_desiderata
                 else (' senza natura' if not ha_natura else ''))
        print(f"[INFO] Generati {len(piani_generati)} piani completi per {num_iv}IVs{nat_s}.")
    elif lista_piani_base_livelli:
        print(f"[AVVISO] Strutture di piano base erano disponibili ma nessun piano finale è stato generato per {num_iv}IV, Natura: {ha_natura}.")
    return piani_generati
