import unittest
import os
from typing import List, Dict, Any

import core_engine
from structures import PokemonPosseduto, PianoValutato, PokemonRichiesto
from plan_evaluator import valuta_piani

def _scrivi_report_piani_valutati(piani: List[PianoValutato], nome_file: str):
    """
    Scrive un file di testo dettagliato usando la mappa di assegnazioni per slot.
    """
    print(f"\n[DEBUG] Scrittura del report di valutazione completo su '{nome_file}'...")
    with open(nome_file, 'w', encoding='utf-8') as f:
        f.write(f"Totale piani analizzati: {len(piani)}\n\n")

        for i, piano_valutato in enumerate(piani):
            piano = piano_valutato.piano_originale
            f.write("-" * 80 + "\n")
            f.write(f"POSIZIONE: {i+1} | ID PIANO: {piano.id_piano} | PUNTEGGIO: {piano_valutato.punteggio:.2f}\n")
            f.write("-" * 80 + "\n")
            
            f.write(f"Legenda Ruoli -> Statistiche: {piano.legenda_ruoli}\n")
            f.write(f"Pokémon Posseduti Usati: {', '.join(sorted(list(piano_valutato.pokemon_usati))) or 'Nessuno'}\n\n")
            
            f.write("Assegnazioni (Requisito -> Posseduto):\n")
            if piano_valutato.mappa_assegnazioni:
                # Ordina gli slot per un report consistente
                sorted_slots = sorted(piano_valutato.mappa_assegnazioni.keys())
                for slot_key in sorted_slots:
                    l_idx, a_idx, p_num = slot_key
                    # Recupera l'oggetto PokemonRichiesto corretto usando lo slot
                    genitore_obj = piano.livelli[l_idx].accoppiamenti[a_idx].genitore1 if p_num == 1 else piano.livelli[l_idx].accoppiamenti[a_idx].genitore2
                    posseduto_id = piano_valutato.mappa_assegnazioni[slot_key]
                    f.write(f"  - {genitore_obj.nome_generico:<15} -> {posseduto_id}\n")
            else:
                f.write("  - Nessuna assegnazione possibile.\n")
            
            f.write("\nStruttura del Piano di Breeding:\n")
            for l_idx, livello in enumerate(piano.livelli):
                f.write(f"  --- Livello {livello.livello_id} ---\n")
                for a_idx, acc in enumerate(livello.accoppiamenti):
                    # Genitore 1
                    slot_key1 = (l_idx, a_idx, 1)
                    genitore1_str = acc.genitore1.nome_generico
                    if slot_key1 in piano_valutato.mappa_assegnazioni:
                        genitore1_str = f"*{piano_valutato.mappa_assegnazioni[slot_key1]}*"

                    # Genitore 2
                    slot_key2 = (l_idx, a_idx, 2)
                    genitore2_str = acc.genitore2.nome_generico
                    if slot_key2 in piano_valutato.mappa_assegnazioni:
                        genitore2_str = f"*{piano_valutato.mappa_assegnazioni[slot_key2]}*"
                    
                    figlio_str = acc.figlio.nome_generico
                    f.write(f"    - {genitore1_str:<25} + {genitore2_str:<25} -> {figlio_str}\n")
            f.write("\n\n")
    print(f"[DEBUG] Report '{nome_file}' creato con successo.")


class TestPlanEvaluator(unittest.TestCase):
    def test_manual_charizard_scenario(self):
        print("\n" + "="*70)
        print("--- ESECUZIONE TEST: SCENARIO CHARIZARD 4IV+N (MANUALE) ---")
        print("="*70)

        pokemon_target = {
            "specie": "Charizard",
            "ivs": ["Attacco Speciale", "Difesa", "Difesa Speciale", "Velocità"],
            "natura": "Adamant"
        }
        print(f"\n[FASE 1] Target: {pokemon_target['specie']} con IVs {pokemon_target['ivs']} e Natura {pokemon_target['natura']}")

        piani_generati = core_engine.esegui_generazione(
            ivs_desiderate=pokemon_target["ivs"],
            natura_desiderata=pokemon_target["natura"]
        )
        self.assertTrue(len(piani_generati) > 0, "Il core_engine non ha generato piani per 4IV+Natura.")

        pokemon_posseduti = [
            PokemonPosseduto(id_utente="P1_M_Ada_AS_V", specie="Charizard", ivs=["Attacco Speciale", "Velocità"], natura="Adamant", sesso="M"),
            PokemonPosseduto(id_utente="P2_M_Quiet_AS_V", specie="Charizard", ivs=["Attacco Speciale", "Velocità"], natura="Quiet", sesso="M"),
            PokemonPosseduto(id_utente="P3_F_Quiet_DS_D", specie="Charizard", ivs=["Difesa Speciale", "Difesa"], natura="Quiet", sesso="F"),
            PokemonPosseduto(id_utente="P4_F_Quiet_V", specie="Charizard", ivs=["Velocità"], natura="Quiet", sesso="F")
        ]
        print("\n[FASE 2] Pokémon Posseduti per la valutazione (scenario Charizard):")
        for p in pokemon_posseduti:
            print(f"  - {p.id_utente}: IVs={sorted(p.ivs) or 'N/A'}, Natura={p.natura or 'N/A'}")

        piani_valutati = valuta_piani(piani_generati, pokemon_posseduti)
        # Il nome del file del report viene aggiornato per non sovrascrivere i vecchi risultati
        _scrivi_report_piani_valutati(piani_valutati, "report_piani_charizard_corretto_finale.txt")
        
        self.assertTrue(len(piani_valutati) > 0, "Il plan_evaluator non ha restituito piani valutati.")
        
        miglior_piano = piani_valutati[0]
        self.assertTrue(miglior_piano.punteggio > 0, "Il piano migliore deve avere un punteggio positivo.")
        self.assertTrue(len(miglior_piano.pokemon_usati) > 0, "Il piano migliore deve usare almeno un pokémon.")
        
        print("\n" + "-"*70)
        print("--- RISULTATO: DETTAGLIO DEL PIANO MIGLIORE (SCENARIO CHARIZARD) ---")
        print(f"Punteggio ottenuto: {miglior_piano.punteggio:.2f}")
        print(f"Pokémon Posseduti utilizzati: {', '.join(sorted(list(miglior_piano.pokemon_usati))) or 'Nessuno'}")
        print("-" * 70)
        
if __name__ == '__main__':
    # Esegue solo il test specifico per evitare errori in altri test non aggiornati
    suite = unittest.TestSuite()
    suite.addTest(TestPlanEvaluator('test_manual_charizard_scenario'))
    runner = unittest.TextTestRunner(verbosity=2)
    runner.run(suite)
