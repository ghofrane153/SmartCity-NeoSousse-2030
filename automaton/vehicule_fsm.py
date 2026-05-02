"""
vehicule_fsm.py
===============
Automate à États Finis — Trajet d'un véhicule autonome

DIAGRAMME :
    STATIONNE ──démarrer──► EN_ROUTE ──arriver──► ARRIVE
                                │                    │
                           panne│                    │stationner
                                ▼                    ▼
                            EN_PANNE ──réparer──► STATIONNE
"""

from transitions import Machine
from datetime import datetime


class VehiculeFSM:
    """
    Gère l'état d'un véhicule autonome pendant son trajet.
    """

    STATES = [
        'STATIONNE',    # Véhicule à l'arrêt, disponible
        'EN_ROUTE',     # Véhicule en déplacement vers sa destination
        'EN_PANNE',     # Véhicule immobilisé suite à une panne
        'ARRIVE',       # Véhicule arrivé à destination
    ]

    TRANSITIONS = [
        {'trigger': 'demarrer',    'source': 'STATIONNE',  'dest': 'EN_ROUTE'},
        {'trigger': 'panne',       'source': 'EN_ROUTE',   'dest': 'EN_PANNE'},
        {'trigger': 'reparer',     'source': 'EN_PANNE',   'dest': 'STATIONNE'},
        {'trigger': 'arriver',     'source': 'EN_ROUTE',   'dest': 'ARRIVE'},
        {'trigger': 'stationner',  'source': 'ARRIVE',     'dest': 'STATIONNE'},
    ]

    def __init__(self, vehicule_id: int, plaque: str = ""):
        self.vehicule_id = vehicule_id
        self.plaque = plaque
        self.trajet_actuel = None
        self.historique = []

        self.machine = Machine(
            model=self,
            states=self.STATES,
            transitions=self.TRANSITIONS,
            initial='STATIONNE',
            auto_transitions=False,
        )
        
        # Enregistrer les callbacks pour chaque état
        self.machine.add_states(
            [
                {'name': 'EN_PANNE', 'on_enter': self._alerte_panne},
                {'name': 'ARRIVE', 'on_enter': self._log_arrivee},
            ]
        )

    def _alerte_panne(self):
        msg = f"🚨 Véhicule {self.plaque} EN PANNE — assistance requise"
        print(msg)
        self.historique.append({'alerte': msg, 'ts': datetime.now().isoformat()})

    def _log_arrivee(self):
        print(f"📍 Véhicule {self.plaque} ARRIVÉ à destination")
        self.historique.append({'event': 'arrivee', 'ts': datetime.now().isoformat()})

    def commencer_trajet(self, origine: str, destination: str) -> dict:
        self.trajet_actuel = {"origine": origine, "destination": destination, "debut": datetime.now().isoformat()}
        return self.appliquer_evenement("demarrer")

    def appliquer_evenement(self, evenement: str) -> dict:
        ancien_etat = self.state
        try:
            getattr(self, evenement)()
            self.historique.append({'evenement': evenement, 'de': ancien_etat, 'vers': self.state})
            return {"succes": True, "ancien_etat": ancien_etat, "nouvel_etat": self.state, "erreur": None}
        except Exception:
            return {"succes": False, "ancien_etat": ancien_etat, "nouvel_etat": ancien_etat,
                    "erreur": f"Transition '{evenement}' impossible depuis '{ancien_etat}'"}

    def to_dict(self) -> dict:
        return {
            "vehicule_id": self.vehicule_id,
            "plaque": self.plaque,
            "etat": self.state,
            "trajet_actuel": self.trajet_actuel,
            "transitions_disponibles": self.machine.get_triggers(self.state),
        }


TABLE_TRANSITION_VEHICULE = """
╔═════════════════╦═══════════════╦═════════════════╗
║  État Actuel    ║  Événement    ║  État Suivant   ║
╠═════════════════╬═══════════════╬═════════════════╣
║  STATIONNE      ║  demarrer     ║  EN_ROUTE       ║
║  EN_ROUTE       ║  arriver      ║  ARRIVE         ║
║  EN_ROUTE       ║  panne        ║  EN_PANNE       ║
║  EN_PANNE       ║  reparer      ║  STATIONNE      ║
║  ARRIVE         ║  stationner   ║  STATIONNE      ║
╚═════════════════╩═══════════════╩═════════════════╝
"""


if __name__ == "__main__":
    print("=== TEST AUTOMATE VEHICULE ===\n")
    print(TABLE_TRANSITION_VEHICULE)

    v = VehiculeFSM(vehicule_id=1, plaque="NS-001-AUTO")

    print("--- Trajet normal ---")
    print(v.commencer_trajet("Gare Sousse", "Aéroport"))
    print(v.appliquer_evenement("arriver"))
    print(v.appliquer_evenement("stationner"))

    print("\n--- Trajet avec panne ---")
    print(v.commencer_trajet("Port", "Université"))
    print(v.appliquer_evenement("panne"))
    print(v.appliquer_evenement("reparer"))
    print(v.appliquer_evenement("demarrer"))
    print(v.appliquer_evenement("arriver"))