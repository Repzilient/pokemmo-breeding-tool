import itertools
import copy
from typing import List, Dict, Optional, Tuple, Set

from structures import PokemonRichiesto, Accoppiamento, Livello, PianoCompleto

# NOTE: Le funzioni _crea_piano_* sono state mantenute come fornite,
# poiché l'errore risiedeva nella logica di generazione delle strategie
# all'interno di `esegui_generazione`.

def _crea_piano_4iv_natura_strutturato(strategia_genitori_3iv: Tuple[Tuple[str, ...], Tuple[str, ...]]) -> List[Livello]:
    """Crea la struttura di un piano per un Pokémon 4IV+Natura, seguendo il modello corretto a 4 livelli."""
    # Ruoli Canonici: B, G, R, Y per IVs; V per Natura. La strategia viene ignorata.

    # --- Livello 1: Creazione dei componenti 2IV e 1IV+N ---
    b_1iv = PokemonRichiesto(ruoli_iv=('B',))
    g_1iv = PokemonRichiesto(ruoli_iv=('G',))
    r_1iv = PokemonRichiesto(ruoli_iv=('R',))
    y_1iv = PokemonRichiesto(ruoli_iv=('Y',))
    v_natura = PokemonRichiesto(ruolo_natura='V')

    # Risultati del Livello 1 (mappando da piani preeding.txt G,R,B,O -> B,G,R,Y)
    vb_1iv_n = PokemonRichiesto(ruoli_iv=('B',), ruolo_natura='V')    # VG
    bg1_2iv = PokemonRichiesto(ruoli_iv=('B', 'G'))                   # GR1
    br1_2iv = PokemonRichiesto(ruoli_iv=('B', 'R'))                   # GB1
    gr1_2iv = PokemonRichiesto(ruoli_iv=('G', 'R'))                   # RB1
    gy1_2iv = PokemonRichiesto(ruoli_iv=('G', 'Y'))                   # RO1
    bg2_2iv = PokemonRichiesto(ruoli_iv=('B', 'G'))                   # GR2
    br2_2iv = PokemonRichiesto(ruoli_iv=('B', 'R'))                   # GB2

    livello1 = Livello(1, [
        Accoppiamento(v_natura, b_1iv, vb_1iv_n),
        Accoppiamento(b_1iv, g_1iv, bg1_2iv),
        Accoppiamento(b_1iv, r_1iv, br1_2iv),
        Accoppiamento(g_1iv, r_1iv, gr1_2iv),
        Accoppiamento(g_1iv, y_1iv, gy1_2iv),
        Accoppiamento(b_1iv, g_1iv, bg2_2iv),
        Accoppiamento(b_1iv, r_1iv, br2_2iv),
    ])

    # --- Livello 2: Combinazione a 3IV e 2IV+N ---
    vbg_2iv_n = PokemonRichiesto(ruoli_iv=('B', 'G'), ruolo_natura='V') # VGR1
    bgr1_3iv = PokemonRichiesto(ruoli_iv=('B', 'G', 'R'))              # GRB1
    gry_3iv = PokemonRichiesto(ruoli_iv=('G', 'R', 'Y'))               # RBO1
    bgr2_3iv = PokemonRichiesto(ruoli_iv=('B', 'G', 'R'))              # GRB2

    livello2 = Livello(2, [
        Accoppiamento(vb_1iv_n, bg1_2iv, vbg_2iv_n),
        Accoppiamento(bg2_2iv, br1_2iv, bgr1_3iv),
        Accoppiamento(gr1_2iv, gy1_2iv, gry_3iv),
        Accoppiamento(bg2_2iv, br2_2iv, bgr2_3iv),
    ])

    # --- Livello 3: Creazione dei Genitori Finali ---
    vbgr_3iv_n = PokemonRichiesto(ruoli_iv=('B', 'G', 'R'), ruolo_natura='V') # Parent_N
    bgry_4iv = PokemonRichiesto(ruoli_iv=('B', 'G', 'R', 'Y'))              # Parent_IV

    livello3 = Livello(3, [
        Accoppiamento(vbg_2iv_n, bgr1_3iv, vbgr_3iv_n),
        Accoppiamento(gry_3iv, bgr2_3iv, bgry_4iv)
    ])

    # --- Livello 4: Accoppiamento Finale ---
    vbgry_4iv_n = PokemonRichiesto(ruoli_iv=('B', 'G', 'R', 'Y'), ruolo_natura='V') # Target

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
    """Crea la struttura di un piano per un Pokémon 5IV+Natura, seguendo il modello corretto a 5 livelli."""
    # Ruoli Canonici: B,G,R,Y,O per IVs; V per Natura. La strategia viene ignorata.
    # Mappatura da piani preeding.txt: B,G,R,I,O -> B,G,R,Y,O

    # --- Definizione di tutti i Pokémon necessari nel piano ---
    # Livello 0 (Base)
    v_n = PokemonRichiesto(ruolo_natura='V')
    b_1 = PokemonRichiesto(ruoli_iv=('B',))
    g_1 = PokemonRichiesto(ruoli_iv=('G',))
    r_1 = PokemonRichiesto(ruoli_iv=('R',))
    y_1 = PokemonRichiesto(ruoli_iv=('Y',))
    o_1 = PokemonRichiesto(ruoli_iv=('O',))

    # Livello 1 (Componenti)
    bg_2 = PokemonRichiesto(ruoli_iv=('B', 'G'))
    br_2 = PokemonRichiesto(ruoli_iv=('B', 'R'))
    gr_2 = PokemonRichiesto(ruoli_iv=('G', 'R'))
    gy_2 = PokemonRichiesto(ruoli_iv=('G', 'Y'))
    ry_2 = PokemonRichiesto(ruoli_iv=('R', 'Y'))
    ro_2 = PokemonRichiesto(ruoli_iv=('R', 'O'))
    vg_1n = PokemonRichiesto(ruoli_iv=('G',), ruolo_natura='V')

    # Livello 2 (Intermedi)
    bgr_3 = PokemonRichiesto(ruoli_iv=('B', 'G', 'R'))
    gry_3 = PokemonRichiesto(ruoli_iv=('G', 'R', 'Y'))
    ryo_3 = PokemonRichiesto(ruoli_iv=('R', 'Y', 'O'))
    vgr_2n = PokemonRichiesto(ruoli_iv=('G', 'R'), ruolo_natura='V')

    # Livello 3 (Pre-finali)
    bgry_4 = PokemonRichiesto(ruoli_iv=('B', 'G', 'R', 'Y'))
    gryo_4 = PokemonRichiesto(ruoli_iv=('G', 'R', 'Y', 'O'))
    vgry_3n = PokemonRichiesto(ruoli_iv=('G', 'R', 'Y'), ruolo_natura='V')

    # Livello 4 (Genitori Finali)
    bgryo_5 = PokemonRichiesto(ruoli_iv=('B', 'G', 'R', 'Y', 'O'))         # Genitore A
    vgryo_4n = PokemonRichiesto(ruoli_iv=('G', 'R', 'Y', 'O'), ruolo_natura='V') # Genitore B

    # Livello 5 (Target)
    vbgryo_5n = PokemonRichiesto(ruoli_iv=('B', 'G', 'R', 'Y', 'O'), ruolo_natura='V')

    # --- Costruzione dei livelli del piano ---
    livello1 = Livello(1, [
        Accoppiamento(b_1, g_1, bg_2), Accoppiamento(b_1, r_1, br_2),
        Accoppiamento(g_1, r_1, gr_2), Accoppiamento(g_1, y_1, gy_2),
        Accoppiamento(r_1, y_1, ry_2), Accoppiamento(r_1, o_1, ro_2),
        Accoppiamento(v_n, g_1, vg_1n)
    ])

    livello2 = Livello(2, [
        Accoppiamento(bg_2, br_2, bgr_3), Accoppiamento(gr_2, gy_2, gry_3),
        Accoppiamento(ry_2, ro_2, ryo_3), Accoppiamento(vg_1n, gr_2, vgr_2n)
    ])

    livello3 = Livello(3, [
        Accoppiamento(bgr_3, gry_3, bgry_4),
        Accoppiamento(gry_3, ryo_3, gryo_4),
        Accoppiamento(vgr_2n, gry_3, vgry_3n)
    ])

    livello4 = Livello(4, [
        Accoppiamento(bgry_4, gryo_4, bgryo_5),
        Accoppiamento(vgry_3n, gryo_4, vgryo_4n)
    ])

    livello5 = Livello(5, [
        Accoppiamento(bgryo_5, vgryo_4n, vbgryo_5n)
    ])

    return [livello1, livello2, livello3, livello4, livello5]

def _crea_piano_5iv_senza_natura_strutturato(strategia_genitori_4iv: Tuple[Tuple[str, ...], Tuple[str, ...]]) -> List[Livello]:
    """Crea la struttura di un piano per un Pokémon 5IV (senza natura) basata su una specifica strategia di genitori 4IV."""
    rA4iv=tuple(sorted(strategia_genitori_4iv[0])); rB4iv=tuple(sorted(strategia_genitori_4iv[1]))
    r5tgt=tuple(sorted(list(set(rA4iv)|set(rB4iv)))); target_5iv=PokemonRichiesto(ruoli_iv=r5tgt)
    if len(r5tgt) != 5: raise ValueError(f"Strategia genitori 4IV non produce un 5IV. Ruoli uniti: {r5tgt}")
    gen_A_4iv=PokemonRichiesto(ruoli_iv=rA4iv); gen_B_4iv=PokemonRichiesto(ruoli_iv=rB4iv)
    rA4 = rA4iv; gen_A_p1_3iv=PokemonRichiesto(ruoli_iv=tuple(sorted((rA4[0],rA4[1],rA4[2])))); gen_A_p2_3iv=PokemonRichiesto(ruoli_iv=tuple(sorted((rA4[0],rA4[1],rA4[3]))))
    rB4 = rB4iv; gen_B_p1_3iv=PokemonRichiesto(ruoli_iv=tuple(sorted((rB4[0],rB4[1],rB4[2])))); gen_B_p2_3iv=PokemonRichiesto(ruoli_iv=tuple(sorted((rB4[0],rB4[1],rB4[3]))))
    rA_p1_3=gen_A_p1_3iv.ruoli_iv; gen_A_p1_c1_2iv=PokemonRichiesto(ruoli_iv=tuple(sorted((rA_p1_3[0],rA_p1_3[1])))); gen_A_p1_c2_2iv=PokemonRichiesto(ruoli_iv=tuple(sorted((rA_p1_3[0],rA_p1_3[2]))))
    rA_p2_3=gen_A_p2_3iv.ruoli_iv; gen_A_p2_c1_2iv=PokemonRichiesto(ruoli_iv=tuple(sorted((rA_p2_3[0],rA_p2_3[1])))); gen_A_p2_c2_2iv=PokemonRichiesto(ruoli_iv=tuple(sorted((rA_p2_3[0],rA_p2_3[2]))))
    rB_p1_3=gen_B_p1_3iv.ruoli_iv; gen_B_p1_c1_2iv=PokemonRichiesto(ruoli_iv=tuple(sorted((rB_p1_3[0],rB_p1_3[1])))); gen_B_p1_c2_2iv=PokemonRichiesto(ruoli_iv=tuple(sorted((rB_p1_3[0],rB_p1_3[2]))))
    rB_p2_3=gen_B_p2_3iv.ruoli_iv; gen_B_p2_c1_2iv=PokemonRichiesto(ruoli_iv=tuple(sorted((rB_p2_3[0],rB_p2_3[1])))); gen_B_p2_c2_2iv=PokemonRichiesto(ruoli_iv=tuple(sorted((rB_p2_3[0],rB_p2_3[2]))))
    l1_children_2iv_set = {gen_A_p1_c1_2iv, gen_A_p1_c2_2iv, gen_A_p2_c1_2iv, gen_A_p2_c2_2iv, gen_B_p1_c1_2iv, gen_B_p1_c2_2iv, gen_B_p2_c1_2iv, gen_B_p2_c2_2iv}
    livello1_accs = [];
    for pok_2iv in l1_children_2iv_set: iv0,iv1=pok_2iv.ruoli_iv[0],pok_2iv.ruoli_iv[1]; livello1_accs.append(Accoppiamento(PokemonRichiesto(ruoli_iv=(iv0,)), PokemonRichiesto(ruoli_iv=(iv1,)), pok_2iv))
    livello1=Livello(1, livello1_accs)
    livello2=Livello(2, [Accoppiamento(gen_A_p1_c1_2iv, gen_A_p1_c2_2iv, gen_A_p1_3iv), Accoppiamento(gen_A_p2_c1_2iv, gen_A_p2_c2_2iv, gen_A_p2_3iv), Accoppiamento(gen_B_p1_c1_2iv, gen_B_p1_c2_2iv, gen_B_p1_3iv), Accoppiamento(gen_B_p2_c1_2iv, gen_B_p2_c2_2iv, gen_B_p2_3iv)])
    livello3=Livello(3, [Accoppiamento(gen_A_p1_3iv, gen_A_p2_3iv, gen_A_4iv), Accoppiamento(gen_B_p1_3iv, gen_B_p2_3iv, gen_B_4iv)])
    livello4=Livello(4, [Accoppiamento(gen_A_4iv, gen_B_4iv, target_5iv)])
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
                try: lista_piani_base_livelli.append(_crea_piano_4iv_natura_strutturato(strat))
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
                try: lista_piani_base_livelli.append(_crea_piano_4iv_senza_natura_strutturato(strat))
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
                try: lista_piani_base_livelli.append(_crea_piano_5iv_natura_strutturato(strat))
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
