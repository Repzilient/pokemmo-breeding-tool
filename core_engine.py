import itertools
import copy
from typing import List, Dict, Optional, Tuple, Set

from structures import PokemonRichiesto, Accoppiamento, Livello, PianoCompleto

# NOTE: Le funzioni _crea_piano_* sono state mantenute come fornite,
# poiché l'errore risiedeva nella logica di generazione delle strategie
# all'interno di `esegui_generazione`.

def _crea_piano_4iv_natura_strutturato(strategia_genitori_3iv: Tuple[Tuple[str, ...], Tuple[str, ...]]) -> List[Livello]:
    """Crea la struttura di un piano per un Pokémon 4IV+Natura basata su una specifica strategia di genitori 3IV."""
    ruoli_genitore_A = tuple(sorted(strategia_genitori_3iv[0])); ruoli_genitore_B = tuple(sorted(strategia_genitori_3iv[1]))
    ruoli_4iv = tuple(sorted(list(set(ruoli_genitore_A) | set(ruoli_genitore_B)))); ruoli_3iv_n = tuple(sorted((ruoli_4iv[0], ruoli_4iv[1], ruoli_4iv[2])))
    target_finale = PokemonRichiesto(ruoli_iv=ruoli_4iv, ruolo_natura='V'); genitore_4iv_final = PokemonRichiesto(ruoli_iv=ruoli_4iv); genitore_3iv_n_final = PokemonRichiesto(ruoli_iv=ruoli_3iv_n, ruolo_natura='V')
    genitore_A_3iv = PokemonRichiesto(ruoli_iv=ruoli_genitore_A); genitore_B_3iv = PokemonRichiesto(ruoli_iv=ruoli_genitore_B)
    ruoli_2iv_n = tuple(sorted((ruoli_3iv_n[0], ruoli_3iv_n[1]))); genitore_2iv_n = PokemonRichiesto(ruoli_iv=ruoli_2iv_n, ruolo_natura='V')
    ruoli_2iv_complemento = tuple(sorted((ruoli_3iv_n[0], ruoli_3iv_n[2]))); genitore_2iv_complemento = PokemonRichiesto(ruoli_iv=ruoli_2iv_complemento)
    gen_A_p1 = PokemonRichiesto(ruoli_iv=tuple(sorted((ruoli_genitore_A[0], ruoli_genitore_A[1])))); gen_A_p2 = PokemonRichiesto(ruoli_iv=tuple(sorted((ruoli_genitore_A[0], ruoli_genitore_A[2]))))
    gen_B_p1 = PokemonRichiesto(ruoli_iv=tuple(sorted((ruoli_genitore_B[0], ruoli_genitore_B[1])))); gen_B_p2 = PokemonRichiesto(ruoli_iv=tuple(sorted((ruoli_genitore_B[0], ruoli_genitore_B[2]))))
    gen_2iv_n_p1 = PokemonRichiesto(ruoli_iv=(ruoli_2iv_n[0],), ruolo_natura='V'); gen_2iv_n_p2 = PokemonRichiesto(ruoli_iv=ruoli_2iv_n)
    livello1_roles = ruoli_4iv
    livello1 = Livello(1, [Accoppiamento(PokemonRichiesto(ruoli_iv=(livello1_roles[0],)), PokemonRichiesto(ruoli_iv=(livello1_roles[1],)), PokemonRichiesto(ruoli_iv=(livello1_roles[0], livello1_roles[1]))), Accoppiamento(PokemonRichiesto(ruoli_iv=(livello1_roles[0],)), PokemonRichiesto(ruoli_iv=(livello1_roles[2],)), PokemonRichiesto(ruoli_iv=(livello1_roles[0], livello1_roles[2]))), Accoppiamento(PokemonRichiesto(ruoli_iv=(livello1_roles[0],)), PokemonRichiesto(ruoli_iv=(livello1_roles[3],)), PokemonRichiesto(ruoli_iv=(livello1_roles[0], livello1_roles[3]))), Accoppiamento(PokemonRichiesto(ruoli_iv=(livello1_roles[1],)), PokemonRichiesto(ruoli_iv=(livello1_roles[2],)), PokemonRichiesto(ruoli_iv=(livello1_roles[1], livello1_roles[2]))), Accoppiamento(PokemonRichiesto(ruoli_iv=(livello1_roles[1],)), PokemonRichiesto(ruoli_iv=(livello1_roles[3],)), PokemonRichiesto(ruoli_iv=(livello1_roles[1], livello1_roles[3]))), Accoppiamento(PokemonRichiesto(ruoli_iv=(livello1_roles[2],)), PokemonRichiesto(ruoli_iv=(livello1_roles[3],)), PokemonRichiesto(ruoli_iv=(livello1_roles[2], livello1_roles[3]))), Accoppiamento(PokemonRichiesto(ruolo_natura='V'), PokemonRichiesto(ruoli_iv=(livello1_roles[0],)), PokemonRichiesto(ruoli_iv=(livello1_roles[0],), ruolo_natura='V')), Accoppiamento(PokemonRichiesto(ruoli_iv=(livello1_roles[1],)), PokemonRichiesto(ruoli_iv=(livello1_roles[2],)), PokemonRichiesto(ruoli_iv=(livello1_roles[1], livello1_roles[2]))),])
    livello2 = Livello(2, [Accoppiamento(gen_A_p1, gen_A_p2, genitore_A_3iv), Accoppiamento(gen_B_p1, gen_B_p2, genitore_B_3iv), Accoppiamento(gen_2iv_n_p1, gen_2iv_n_p2, genitore_2iv_n), Accoppiamento(livello1.accoppiamenti[0].figlio, livello1.accoppiamenti[3].figlio, PokemonRichiesto(ruoli_iv=tuple(sorted(set(livello1.accoppiamenti[0].figlio.ruoli_iv) | set(livello1.accoppiamenti[3].figlio.ruoli_iv)))))])
    livello3 = Livello(3, [Accoppiamento(genitore_A_3iv, genitore_B_3iv, genitore_4iv_final), Accoppiamento(genitore_2iv_n, genitore_2iv_complemento, genitore_3iv_n_final)])
    livello4 = Livello(4, [Accoppiamento(genitore_4iv_final, genitore_3iv_n_final, target_finale)])
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
    """Crea la struttura di un piano per un Pokémon 5IV+Natura."""
    all_5_iv_roles = tuple(sorted(strategia_5iv_n[0])); nature_branch_4_iv_roles = tuple(sorted(strategia_5iv_n[1]))
    if len(all_5_iv_roles)!=5 or len(nature_branch_4_iv_roles)!=4 or not set(nature_branch_4_iv_roles).issubset(set(all_5_iv_roles)): raise ValueError("Strategia 5IV+N non valida.")
    target_5iv_n = PokemonRichiesto(ruoli_iv=all_5_iv_roles, ruolo_natura='V'); gen_l4_p1_5iv = PokemonRichiesto(ruoli_iv=all_5_iv_roles); gen_l4_p2_4iv_n = PokemonRichiesto(ruoli_iv=nature_branch_4_iv_roles, ruolo_natura='V')
    r5 = all_5_iv_roles; gen_l3_p1_4iv = PokemonRichiesto(ruoli_iv=tuple(r5[:4])); gen_l3_p2_4iv = PokemonRichiesto(ruoli_iv=tuple(list(r5[:3]) + [r5[4]]))
    nb4r = nature_branch_4_iv_roles; gen_l3_p3_3iv_n = PokemonRichiesto(ruoli_iv=tuple(nb4r[:3]), ruolo_natura='V'); gen_l3_p4_3iv = PokemonRichiesto(ruoli_iv=tuple(list(nb4r[:2]) + [nb4r[3]]))
    p1_4iv_r = gen_l3_p1_4iv.ruoli_iv; gen_l2_p1_3iv = PokemonRichiesto(ruoli_iv=tuple(p1_4iv_r[:3])); gen_l2_p2_3iv = PokemonRichiesto(ruoli_iv=tuple(list(p1_4iv_r[:2]) + [p1_4iv_r[3]]))
    p2_4iv_r = gen_l3_p2_4iv.ruoli_iv; gen_l2_p3_3iv = PokemonRichiesto(ruoli_iv=tuple(p2_4iv_r[:3])); gen_l2_p4_3iv = PokemonRichiesto(ruoli_iv=tuple(list(p2_4iv_r[:2]) + [p2_4iv_r[3]]))
    p3_3iv_n_r = gen_l3_p3_3iv_n.ruoli_iv; gen_l2_p5_2iv_n = PokemonRichiesto(ruoli_iv=tuple(p3_3iv_n_r[:2]), ruolo_natura='V'); gen_l2_p6_2iv = PokemonRichiesto(ruoli_iv=tuple(list(p3_3iv_n_r[:1]) + [p3_3iv_n_r[2]]))
    p4_3iv_r = gen_l3_p4_3iv.ruoli_iv; gen_l2_p7_2iv = PokemonRichiesto(ruoli_iv=tuple(p4_3iv_r[:2])); gen_l2_p8_2iv = PokemonRichiesto(ruoli_iv=tuple(list(p4_3iv_r[:1]) + [p4_3iv_r[2]]))
    l1_base_roles = all_5_iv_roles; livello1_accs = []
    for i in range(len(l1_base_roles)):
        for j in range(i + 1, len(l1_base_roles)): role1, role2 = l1_base_roles[i], l1_base_roles[j]; livello1_accs.append(Accoppiamento(PokemonRichiesto(ruoli_iv=(role1,)), PokemonRichiesto(ruoli_iv=(role2,)), PokemonRichiesto(ruoli_iv=tuple(sorted((role1,role2))))))
    for role1 in l1_base_roles: livello1_accs.append(Accoppiamento(PokemonRichiesto(ruolo_natura='V'), PokemonRichiesto(ruoli_iv=(role1,)), PokemonRichiesto(ruoli_iv=(role1,), ruolo_natura='V')))
    livello1 = Livello(1, livello1_accs)
    l2_children = [gen_l2_p1_3iv, gen_l2_p2_3iv, gen_l2_p3_3iv, gen_l2_p4_3iv, gen_l2_p5_2iv_n, gen_l2_p6_2iv, gen_l2_p7_2iv, gen_l2_p8_2iv]
    livello2_accs = []
    for child_pok in l2_children:
        p_roles = child_pok.ruoli_iv; p_nat = child_pok.ruolo_natura
        if len(p_roles) == 3: parent1_roles = tuple(sorted((p_roles[0],p_roles[1]))); parent2_roles = tuple(sorted((p_roles[0],p_roles[2]))); livello2_accs.append(Accoppiamento(PokemonRichiesto(ruoli_iv=parent1_roles), PokemonRichiesto(ruoli_iv=parent2_roles), child_pok))
        elif len(p_roles) == 2 and p_nat: parent1_roles = (p_roles[0],); parent1_nat = 'V'; parent2_roles = tuple(sorted((p_roles[0],p_roles[1]))); livello2_accs.append(Accoppiamento(PokemonRichiesto(ruoli_iv=parent1_roles, ruolo_natura=parent1_nat), PokemonRichiesto(ruoli_iv=parent2_roles), child_pok))
        elif len(p_roles) == 2 and not p_nat: parent1_roles = (p_roles[0],); parent2_roles = (p_roles[1],); livello2_accs.append(Accoppiamento(PokemonRichiesto(ruoli_iv=parent1_roles), PokemonRichiesto(ruoli_iv=parent2_roles), child_pok))
    livello2 = Livello(2, livello2_accs)
    livello3 = Livello(3, [ Accoppiamento(gen_l2_p1_3iv, gen_l2_p2_3iv, gen_l3_p1_4iv), Accoppiamento(gen_l2_p3_3iv, gen_l2_p4_3iv, gen_l3_p2_4iv), Accoppiamento(gen_l2_p5_2iv_n, gen_l2_p6_2iv, gen_l3_p3_3iv_n), Accoppiamento(gen_l2_p7_2iv, gen_l2_p8_2iv, gen_l3_p4_3iv) ])
    livello4 = Livello(4, [ Accoppiamento(gen_l3_p1_4iv, gen_l3_p2_4iv, gen_l4_p1_5iv), Accoppiamento(gen_l3_p3_3iv_n, gen_l3_p4_3iv, gen_l4_p2_4iv_n) ])
    livello5 = Livello(5, [ Accoppiamento(gen_l4_p1_5iv, gen_l4_p2_4iv_n, target_5iv_n) ])
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
    """Crea la struttura di un piano per un Pokémon 3IV+Natura."""
    target_roles=tuple(sorted(strategia_3iv_n[0])); p1_2iv_n_roles=tuple(sorted(strategia_3iv_n[1])); p2_2iv_roles=tuple(sorted(strategia_3iv_n[2]))
    if len(target_roles) != 3 or len(p1_2iv_n_roles) != 2 or len(p2_2iv_roles) != 2: raise ValueError("Strategia 3IV+N non valida: dimensioni ruoli errate.")
    if not (set(p1_2iv_n_roles) | set(p2_2iv_roles)) == set(target_roles): raise ValueError("Strategia 3IV+N non valida: unione genitori non corrisponde al target.")
    if len(set(p1_2iv_n_roles) & set(p2_2iv_roles)) != 1: raise ValueError("Strategia 3IV+N non valida: i genitori 2IV devono condividere esattamente un ruolo IV.")
    target_3iv_n=PokemonRichiesto(ruoli_iv=target_roles,ruolo_natura='V'); parent_2iv_n=PokemonRichiesto(ruoli_iv=p1_2iv_n_roles,ruolo_natura='V'); parent_2iv=PokemonRichiesto(ruoli_iv=p2_2iv_roles)
    p1_1iv_n=PokemonRichiesto(ruoli_iv=(p1_2iv_n_roles[0],),ruolo_natura='V'); p1_1iv=PokemonRichiesto(ruoli_iv=(p1_2iv_n_roles[1],))
    p2_c1_1iv=PokemonRichiesto(ruoli_iv=(p2_2iv_roles[0],)); p2_c2_1iv=PokemonRichiesto(ruoli_iv=(p2_2iv_roles[1],))
    livello1=Livello(1,[Accoppiamento(p1_1iv_n,p1_1iv,parent_2iv_n),Accoppiamento(p2_c1_1iv,p2_c2_1iv,parent_2iv)])
    livello2=Livello(2,[Accoppiamento(parent_2iv_n,parent_2iv,target_3iv_n)])
    livello3_display=Livello(3,[Accoppiamento(target_3iv_n,PokemonRichiesto(),target_3iv_n)]) # Convenzione per la visualizzazione
    return [livello1,livello2,livello3_display]

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
    """Crea la struttura di un piano per un Pokémon 2IV+Natura."""
    target_2_iv_roles = tuple(sorted(strategia_2iv_n[0]))
    role_for_1iv_n_parent = strategia_2iv_n[1]

    if len(target_2_iv_roles) != 2:
        raise ValueError("Strategia 2IV+N non valida: target_2_iv_roles deve avere 2 ruoli.")
    if role_for_1iv_n_parent not in target_2_iv_roles:
        raise ValueError("Strategia 2IV+N non valida: role_for_1iv_n_parent non è nei ruoli target.")

    other_role = target_2_iv_roles[1] if target_2_iv_roles[0] == role_for_1iv_n_parent else target_2_iv_roles[0]

    target_2iv_n = PokemonRichiesto(ruoli_iv=target_2_iv_roles, ruolo_natura='V')
    parent_1iv_n = PokemonRichiesto(ruoli_iv=(role_for_1iv_n_parent,), ruolo_natura='V')
    parent_1iv = PokemonRichiesto(ruoli_iv=(other_role,))

    # Questo è un processo di breeding a livello singolo.
    livello1 = Livello(1, [
        Accoppiamento(parent_1iv_n, parent_1iv, target_2iv_n)
    ])

    return [livello1]


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
