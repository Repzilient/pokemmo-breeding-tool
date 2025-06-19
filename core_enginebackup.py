import itertools
import copy
from typing import List, Dict, Optional

from structures import PokemonRichiesto, Accoppiamento, Livello, PianoCompleto

# --- Piani CON NATURA ---
# Ripristino delle funzioni di generazione dei piani originali.
# La logica qui era corretta e non necessitava di modifiche.

def _crea_piano_5iv_natura() -> List[Livello]:
    """Genera il piano 5IV+N con istanze uniche per ogni genitore."""
    # Livello 1
    l1_accs = [
        Accoppiamento(PokemonRichiesto(ruoli_iv=('B',)), PokemonRichiesto(ruoli_iv=('R',)), PokemonRichiesto(ruoli_iv=('B', 'R'))),
        Accoppiamento(PokemonRichiesto(ruoli_iv=('B',)), PokemonRichiesto(ruoli_iv=('Y',)), PokemonRichiesto(ruoli_iv=('B', 'Y'))),
        Accoppiamento(PokemonRichiesto(ruoli_iv=('R',)), PokemonRichiesto(ruoli_iv=('Y',)), PokemonRichiesto(ruoli_iv=('R', 'Y'))),
        Accoppiamento(PokemonRichiesto(ruoli_iv=('R',)), PokemonRichiesto(ruoli_iv=('G',)), PokemonRichiesto(ruoli_iv=('R', 'G'))),
        Accoppiamento(PokemonRichiesto(ruoli_iv=('R',)), PokemonRichiesto(ruoli_iv=('Y',)), PokemonRichiesto(ruoli_iv=('R', 'Y'))),
        Accoppiamento(PokemonRichiesto(ruoli_iv=('R',)), PokemonRichiesto(ruoli_iv=('G',)), PokemonRichiesto(ruoli_iv=('R', 'G'))),
        Accoppiamento(PokemonRichiesto(ruoli_iv=('Y',)), PokemonRichiesto(ruoli_iv=('G',)), PokemonRichiesto(ruoli_iv=('Y', 'G'))),
        Accoppiamento(PokemonRichiesto(ruoli_iv=('Y',)), PokemonRichiesto(ruoli_iv=('O',)), PokemonRichiesto(ruoli_iv=('Y', 'O'))),
        # Ramo Natura
        Accoppiamento(PokemonRichiesto(ruolo_natura='V'), PokemonRichiesto(ruoli_iv=('R',)), PokemonRichiesto(ruoli_iv=('R',), ruolo_natura='V')),
        Accoppiamento(PokemonRichiesto(ruoli_iv=('R',)), PokemonRichiesto(ruoli_iv=('Y',)), PokemonRichiesto(ruoli_iv=('R', 'Y'))),
        Accoppiamento(PokemonRichiesto(ruoli_iv=('R',)), PokemonRichiesto(ruoli_iv=('Y',)), PokemonRichiesto(ruoli_iv=('R', 'Y'))),
        Accoppiamento(PokemonRichiesto(ruoli_iv=('R',)), PokemonRichiesto(ruoli_iv=('G',)), PokemonRichiesto(ruoli_iv=('R', 'G'))),
        Accoppiamento(PokemonRichiesto(ruoli_iv=('R',)), PokemonRichiesto(ruoli_iv=('Y',)), PokemonRichiesto(ruoli_iv=('R', 'Y'))),
        Accoppiamento(PokemonRichiesto(ruoli_iv=('R',)), PokemonRichiesto(ruoli_iv=('G',)), PokemonRichiesto(ruoli_iv=('R', 'G'))),
        Accoppiamento(PokemonRichiesto(ruoli_iv=('Y',)), PokemonRichiesto(ruoli_iv=('G',)), PokemonRichiesto(ruoli_iv=('Y', 'G'))),
        Accoppiamento(PokemonRichiesto(ruoli_iv=('Y',)), PokemonRichiesto(ruoli_iv=('O',)), PokemonRichiesto(ruoli_iv=('Y', 'O')))
    ]
    livello1 = Livello(1, l1_accs)
    
    # Livello 2
    l2_accs = [
        Accoppiamento(l1_accs[0].figlio, l1_accs[1].figlio, PokemonRichiesto(ruoli_iv=('B', 'R', 'Y'))),
        Accoppiamento(l1_accs[2].figlio, l1_accs[3].figlio, PokemonRichiesto(ruoli_iv=('R', 'Y', 'G'))),
        Accoppiamento(l1_accs[4].figlio, l1_accs[5].figlio, PokemonRichiesto(ruoli_iv=('R', 'Y', 'G'))),
        Accoppiamento(l1_accs[6].figlio, l1_accs[7].figlio, PokemonRichiesto(ruoli_iv=('Y', 'G', 'O'))),
        # Ramo Natura
        Accoppiamento(l1_accs[8].figlio, l1_accs[9].figlio, PokemonRichiesto(ruoli_iv=('R', 'Y'), ruolo_natura='V')),
        Accoppiamento(l1_accs[10].figlio, l1_accs[11].figlio, PokemonRichiesto(ruoli_iv=('R', 'Y', 'G'))),
        Accoppiamento(l1_accs[12].figlio, l1_accs[13].figlio, PokemonRichiesto(ruoli_iv=('R', 'Y', 'G'))),
        Accoppiamento(l1_accs[14].figlio, l1_accs[15].figlio, PokemonRichiesto(ruoli_iv=('Y', 'G', 'O')))
    ]
    livello2 = Livello(2, l2_accs)

    # Livello 3
    l3_accs = [
        Accoppiamento(l2_accs[0].figlio, l2_accs[1].figlio, PokemonRichiesto(ruoli_iv=('B', 'R', 'Y', 'G'))),
        Accoppiamento(l2_accs[2].figlio, l2_accs[3].figlio, PokemonRichiesto(ruoli_iv=('R', 'Y', 'G', 'O'))),
        # Ramo Natura
        Accoppiamento(l2_accs[4].figlio, l2_accs[5].figlio, PokemonRichiesto(ruoli_iv=('R', 'Y', 'G'), ruolo_natura='V')),
        Accoppiamento(l2_accs[6].figlio, l2_accs[7].figlio, PokemonRichiesto(ruoli_iv=('R', 'Y', 'G', 'O')))
    ]
    livello3 = Livello(3, l3_accs)

    # Livello 4
    l4_accs = [
        Accoppiamento(l3_accs[0].figlio, l3_accs[1].figlio, PokemonRichiesto(ruoli_iv=('B', 'R', 'Y', 'G', 'O'))),
        Accoppiamento(l3_accs[2].figlio, l3_accs[3].figlio, PokemonRichiesto(ruoli_iv=('R', 'Y', 'G', 'O'), ruolo_natura='V'))
    ]
    livello4 = Livello(4, l4_accs)

    # Livello 5
    livello5 = Livello(5, [
        Accoppiamento(l4_accs[0].figlio, l4_accs[1].figlio, PokemonRichiesto(ruoli_iv=('B', 'R', 'Y', 'G', 'O'), ruolo_natura='V'))
    ])

    return [livello1, livello2, livello3, livello4, livello5]

def _crea_piano_4iv_natura() -> List[Livello]:
    """Genera il piano 4IV+N con istanze uniche per ogni genitore."""
    l1_accs = [
        Accoppiamento(PokemonRichiesto(ruolo_natura='V'), PokemonRichiesto(ruoli_iv=('B',)), PokemonRichiesto(ruoli_iv=('B',), ruolo_natura='V')),
        Accoppiamento(PokemonRichiesto(ruoli_iv=('B',)), PokemonRichiesto(ruoli_iv=('R',)), PokemonRichiesto(ruoli_iv=('B', 'R'))),
        Accoppiamento(PokemonRichiesto(ruoli_iv=('B',)), PokemonRichiesto(ruoli_iv=('Y',)), PokemonRichiesto(ruoli_iv=('B', 'Y'))),
        Accoppiamento(PokemonRichiesto(ruoli_iv=('R',)), PokemonRichiesto(ruoli_iv=('Y',)), PokemonRichiesto(ruoli_iv=('R', 'Y'))),
        Accoppiamento(PokemonRichiesto(ruoli_iv=('R',)), PokemonRichiesto(ruoli_iv=('G',)), PokemonRichiesto(ruoli_iv=('R', 'G'))),
        Accoppiamento(PokemonRichiesto(ruoli_iv=('B',)), PokemonRichiesto(ruoli_iv=('R',)), PokemonRichiesto(ruoli_iv=('B', 'R'))),
        Accoppiamento(PokemonRichiesto(ruoli_iv=('B',)), PokemonRichiesto(ruoli_iv=('R',)), PokemonRichiesto(ruoli_iv=('B', 'R'))),
        Accoppiamento(PokemonRichiesto(ruoli_iv=('B',)), PokemonRichiesto(ruoli_iv=('Y',)), PokemonRichiesto(ruoli_iv=('B', 'Y')))
    ]
    livello1 = Livello(1, l1_accs)

    l2_accs = [
        Accoppiamento(l1_accs[0].figlio, l1_accs[1].figlio, PokemonRichiesto(ruoli_iv=('B', 'R'), ruolo_natura='V')),
        Accoppiamento(l1_accs[5].figlio, l1_accs[2].figlio, PokemonRichiesto(ruoli_iv=('B', 'R', 'Y'))),
        Accoppiamento(l1_accs[3].figlio, l1_accs[4].figlio, PokemonRichiesto(ruoli_iv=('R', 'Y', 'G'))),
        Accoppiamento(l1_accs[6].figlio, l1_accs[7].figlio, PokemonRichiesto(ruoli_iv=('B', 'R', 'Y')))
    ]
    livello2 = Livello(2, l2_accs)

    l3_accs = [
        Accoppiamento(l2_accs[0].figlio, l2_accs[1].figlio, PokemonRichiesto(ruoli_iv=('B', 'R', 'Y'), ruolo_natura='V')),
        Accoppiamento(l2_accs[3].figlio, l2_accs[2].figlio, PokemonRichiesto(ruoli_iv=('B', 'R', 'Y', 'G')))
    ]
    livello3 = Livello(3, l3_accs)

    livello4 = Livello(4, [
        Accoppiamento(l3_accs[0].figlio, l3_accs[1].figlio, PokemonRichiesto(ruoli_iv=('B', 'R', 'Y', 'G'), ruolo_natura='V'))
    ])
    
    return [livello1, livello2, livello3, livello4]

def genera_piano_specifico(num_iv: int, natura: bool) -> List[Livello]:
    """Seleziona la funzione corretta per generare il piano richiesto."""
    if natura:
        if num_iv == 5: return _crea_piano_5iv_natura()
        if num_iv == 4: return _crea_piano_4iv_natura()
        # Aggiungere altre condizioni per 3IV, 2IV, etc.
    else:
        # Aggiungere condizioni per piani senza natura
        pass
    return []

def esegui_generazione(ivs_desiderate: List[str], natura_desiderata: Optional[str]) -> List[PianoCompleto]:
    piani_generati = []
    num_iv = len(ivs_desiderate)
    ha_natura = bool(natura_desiderata)
    
    CANONICAL_IV_ROLES = ['B', 'R', 'Y', 'G', 'O', 'I']
    nat_role = 'V'
    
    iv_roles_for_legend = CANONICAL_IV_ROLES[:num_iv]
    permutazioni_iv = list(itertools.permutations(ivs_desiderate))
    
    id_piano_counter = 0
    for perm in permutazioni_iv:
        id_piano_counter += 1
        legenda = {ruolo: stat for ruolo, stat in zip(iv_roles_for_legend, perm)}
        if ha_natura:
            legenda[nat_role] = natura_desiderata
            
        piano_struttura = genera_piano_specifico(num_iv, ha_natura)
        if not piano_struttura:
            continue

        # Usiamo deepcopy per garantire che ogni piano abbia istanze di oggetti completamente nuove
        piano = PianoCompleto(
            id_piano=id_piano_counter,
            ivs_target=list(ivs_desiderate),
            natura_target=natura_desiderata,
            legenda_ruoli=legenda,
            livelli=copy.deepcopy(piano_struttura)
        )Add commentMore actions
        piani_generati.append(piano)

    return piani_generati
