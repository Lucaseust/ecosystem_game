# -*- coding: utf-8 -*-
"""Constantes et regles chiffrees du jeu ECOSYSTEM.

Toutes les valeurs proviennent de concept.md. Les seules valeurs ajoutees
(non fixees par le concept) sont signalees par le commentaire AJOUT.
"""

ROLES = ["MOBI", "AUTO", "BRAIN", "GRID", "FLEET"]

# Ordre de remplissage des sieges : les roles les plus structurants d'abord,
# pour qu'une equipe incomplete garde toujours son orchestrateur.
ROLE_PRIORITY = ["MOBI", "FLEET", "BRAIN", "AUTO", "GRID"]

TEAMS = ["BLUE", "GREEN", "RED", "YELLOW", "PURPLE", "ORANGE"]

TEAM_COLORS = {
    "BLUE": "#8dbdd8",
    "GREEN": "#a4cfb7",
    "RED": "#e3a79c",
    "YELLOW": "#dfc58c",
    "PURPLE": "#bcafd6",
    "ORANGE": "#ddba94",
}

# --- Parametres economiques (concept.md sect. 4, 5, 6) ---------------------

RESOURCES = 10  # points de ressources par round

COST = {"MOBI": 3, "AUTO": 5, "BRAIN": 4, "GRID": 4, "FLEET": 5}
OUTSIDE = {"MOBI": 0, "AUTO": 3, "BRAIN": 4, "GRID": 2, "FLEET": 4}

TOTAL_COST = sum(COST.values())  # 21

# Round 1 : repartition imposee (sect. 9)
R1_REVENUE = {"MOBI": 14, "AUTO": 10, "BRAIN": 6, "GRID": 6, "FLEET": 4}

V_BASE = 40  # valeur du service (rounds 1 et 2)

# --- Round 3 : architecture (sect. 23) -------------------------------------

V_PROPRIETARY = 46
V_MODULAR = 40
STANDARD_COST = 6  # cout collectif de la modularite
REPLACE_COST = {"PROPRIETARY": 8, "MODULAR": 2}
DELAY_LOSS = {"PROPRIETARY": 12, "MODULAR": 0}
BRAIN_ADAPTATION = 6  # sect. 26 : mise en conformite de BRAIN

# AJOUT : le concept introduit ALT-AI sans lui donner de prix. On lui applique
# la meme structure que BRAIN (cout 4, option exterieure 4), donc un revenu
# minimal de 8 pour qu'il accepte la position. Cette valeur est annoncee
# publiquement dans la carte de choc : elle n'est pas une information privee.
ALT_AI_COST = 4
ALT_AI_MIN_REVENUE = 8

# --- Chocs du round 3 (trois tirages possibles) ----------------------------
# Le choc est tire au sort pour toute la classe, apres le choix d'architecture.
#
# AJOUT : le concept ne chiffrait qu'un seul choc. Les deux autres reutilisent
# la meme mecanique (remplacer / adapter / abandonner) et les memes constantes
# structurelles (DELAY_LOSS, ALT_AI_COST, ALT_AI_MIN_REVENUE), afin de ne pas
# introduire de nouvelle variable dans le calcul des scores.
#
# Le retard (DELAY_LOSS) frappe l'architecture proprietaire des qu'il faut
# toucher au systeme : remplacer un partenaire (chocs A et B) ou refaire
# certifier l'ensemble (choc C). Sans cela le proprietaire resterait dominant
# en esperance (13 contre 10) et le choix d'architecture n'aurait pas d'enjeu.

INFRA_REPLACE_COST = {"PROPRIETARY": 10, "MODULAR": 4}
REGULATION_COST = {"PROPRIETARY": 8, "MODULAR": 3}

SHOCKS = {
    "AI_FAILURE": {
        "label": "AI FAILURE",
        "target": "BRAIN",  # role rendu indisponible
        "alt": "ALT_AI",
        "alt_label": "ALT-AI",
        "options": ["KEEP", "REPLACE", "ABANDON"],
        "replace_cost": REPLACE_COST,  # {PROPRIETARY: 8, MODULAR: 2}
        "keep_cost": None,  # KEEP = BRAIN paie BRAIN_ADAPTATION
        "delay_on": ("REPLACE",),
    },
    "INFRA_FAILURE": {
        "label": "INFRA FAILURE",
        "target": "GRID",
        "alt": "ALT_INFRA",
        "alt_label": "ALT-INFRA",
        "options": ["REPLACE", "ABANDON"],
        "replace_cost": INFRA_REPLACE_COST,
        "keep_cost": None,
        "delay_on": ("REPLACE",),
    },
    "REGULATION": {
        "label": "NEW REGULATION",
        "target": None,  # personne ne disparait
        "alt": None,
        "alt_label": None,
        "options": ["KEEP", "ABANDON"],  # KEEP = se mettre en conformite
        "replace_cost": None,
        "keep_cost": REGULATION_COST,  # cout collectif reparti entre les cinq
        "delay_on": ("KEEP",),
    },
}

SHOCK_KEYS = list(SHOCKS)

# Annonce faite avant le choix d'architecture : ni le choc ni sa probabilite.
SHOCK_WARNING = "Un changement majeur de l'environnement peut survenir. Vous ne savez pas lequel."

# --- Marche des ecosystemes (entre le round 2 et le choix d'architecture) ---

SWITCH_COST = 2  # ce que BRAIN paie de sa poche pour changer d'ecosysteme
OFFER_MAX = 5  # plafond d'une offre, prelevee sur la part de MOBI

# --- Pouvoirs de role (un seul usage par partie) ---------------------------
#
# AJOUT. Chaque pouvoir est binaire et n'introduit aucune variable continue.
# Les gains et pertes passent par le registre d'ajustements de l'equipe : les
# formules score_simple() et score_round3() restent inchangees.

POWERS = {
    "MOBI": {
        "key": "SUBSIDY",
        "name": "SUBVENTION",
        "text": (
            "Transferez de 1 a 3 points de votre propre part vers un "
            "partenaire. Un seul usage dans la partie."
        ),
        "phases": ("R1_NEGO", "R1_DECIDE", "R3_NEGO", "R3_DECIDE"),
        "max": 3,
    },
    "BRAIN": {
        "key": "EXCLUSIVITY",
        "name": "EXCLUSIVITE",
        "text": (
            "Demandez 3 points a MOBI contre votre engagement a rester "
            "dans cet ecosysteme jusqu'a la fin de la partie. Si MOBI "
            "accepte, vous renoncez a changer d'ecosysteme."
        ),
        "phases": ("R2_NEGO", "R2_DECIDE", "MARKET"),
        "max": 3,
    },
    "AUTO": {
        "key": "MULTIHOMING",
        "name": "MULTI-HOMING",
        "text": (
            "Annoncez que votre usine travaille aussi pour un autre "
            "ecosysteme : +2 points pour vous, -2 points de valeur "
            "collective pour le votre. Vous restez membre."
        ),
        "phases": ("MARKET",),
        "max": 2,
    },
    "GRID": {
        "key": "STANDARD_READY",
        "name": "STANDARD READY",
        "text": (
            "Si l'ecosysteme a choisi MODULAR, votre infrastructure est "
            "deja aux normes : le cout d'adaptation du choc baisse de "
            "2 points."
        ),
        "phases": ("R3_NEGO",),
        "max": 2,
    },
    "FLEET": {
        "key": "VETO",
        "name": "VETO D'ARCHITECTURE",
        "text": (
            "Interdisez l'architecture integree avant son depot. "
            "L'ecosysteme devra choisir l'architecture modulaire. "
            "Un seul usage dans la partie."
        ),
        "phases": ("R3_ARCH",),
        "max": 0,
    },
}

# --- Badges pedagogiques (aucun effet sur les scores) ----------------------

HOLD_UP_SHARE = 0.30  # part des 40 points du round 2 captee par BRAIN

BADGES = {
    "HOLD_UP": ("🎯", "HOLD-UP", "BRAIN a capte au moins 30 % des 40 points du round 2."),
    "FAILED_BARGAIN": (
        "💸",
        "FAILED BARGAIN",
        "L'ecosysteme etait collectivement rentable, mais un acteur est sorti.",
    ),
    "POACHED": ("🏴", "POACHED", "Votre BRAIN est parti pour un autre ecosysteme."),
    "LOCK_IN": (
        "🔒",
        "LOCK-IN",
        "Votre architecture a rendu l'adaptation plus couteuse qu'en modulaire.",
    ),
    "RESILIENT": (
        "🛡",
        "RESILIENT ECOSYSTEM",
        "Architecture modulaire : vous avez encaisse le choc.",
    ),
}

# --- Seuils rationnels (sect. 18) ------------------------------------------


def threshold(role):
    """Revenu minimal pour qu'un acteur prefere l'ecosysteme a son exterieur."""
    return COST[role] + OUTSIDE[role]


THRESHOLDS = {r: threshold(r) for r in ROLES}  # MOBI 3, AUTO 8, BRAIN 8, GRID 6, FLEET 9

# --- Textes de role (sect. 44 a 48) ----------------------------------------

ROLE_CARDS = {
    "MOBI": {
        "title": "Orchestrateur",
        "tagline": "Vous avez imagine le service. Vous ne commandez personne.",
        "controls": [
            "l'application et la marque",
            "la relation client",
            "la reservation et le paiement",
            "une partie des donnees utilisateurs",
        ],
        "brief": (
            "Vous ne possedez ni les vehicules, ni l'IA de conduite, ni les stations "
            "de recharge, ni les operations terrain. Vous formulez la proposition de "
            "valeur et vous assemblez l'ecosysteme."
        ),
        "warning": (
            "Etre orchestrateur ne signifie pas que les autres joueurs doivent vous "
            "obeir. Vous ne pouvez imposer aucune signature."
        ),
        "duty": "Vous remettez le contrat de votre ecosysteme.",
    },
    "AUTO": {
        "title": "Constructeur automobile",
        "tagline": "Vous produisez et adaptez les vehicules.",
        "controls": [
            "la production des vehicules",
            "l'integration du systeme de conduite",
            "la conformite technique",
            "les interfaces vehicule / partenaires",
        ],
        "brief": (
            "Votre usine doit realiser des adaptations specifiques au projet. Si vous "
            "refusez, vous pouvez utiliser vos capacites sur une autre commande."
        ),
        "warning": "",
        "duty": "",
    },
    "BRAIN": {
        "title": "Fournisseur d'IA",
        "tagline": "Votre technologie interesse plusieurs marches.",
        "controls": [
            "le systeme de conduite autonome",
            "les modeles et la cartographie",
            "les flux de donnees temps reel",
        ],
        "brief": (
            "Votre technologie est proprietaire et peut etre vendue a d'autres clients. "
            "Vous pouvez reveler ou non la valeur de votre option exterieure."
        ),
        "warning": "",
        "duty": "",
    },
    "GRID": {
        "title": "Infrastructure",
        "tagline": "Sans energie ni depots, aucune navette ne roule deux jours.",
        "controls": [
            "les stations de recharge",
            "les depots",
            "les infrastructures de maintenance",
            "les interfaces energetiques",
        ],
        "brief": (
            "L'adaptation de votre infrastructure au projet necessite des "
            "investissements specifiques."
        ),
        "warning": "",
        "duty": "",
    },
    "FLEET": {
        "title": "Operateur",
        "tagline": "Sans vous, aucun vehicule n'est exploite commercialement.",
        "controls": [
            "l'exploitation quotidienne",
            "la supervision",
            "le repositionnement des vehicules",
            "la maintenance legere et les incidents",
        ],
        "brief": (
            "Vous assurez que le service existe reellement, tous les jours, meme "
            "lorsque toutes les technologies fonctionnent."
        ),
        "warning": (
            "Votre position est moins visible technologiquement que celles de MOBI ou "
            "BRAIN. Cela ne signifie pas qu'elle est moins importante."
        ),
        "duty": "",
    },
}

VALUE_PROPOSITION = (
    "Permettre a un utilisateur de reserver a la demande une navette autonome, "
    "avec moins de dix minutes d'attente, un trajet fiable et un prix inferieur "
    "a celui d'un taxi."
)

SHOCK_TEXT = [
    "BREAKING NEWS - AI CERTIFICATION FAILURE",
    "Le regulateur vient d'annoncer que la version actuelle du systeme autonome "
    "de BRAIN ne pourra pas obtenir la certification necessaire dans les delais.",
    "BRAIN peut adapter son systeme, mais cette adaptation necessite un "
    "investissement supplementaire de 6 points.",
    "Vous pouvez egalement remplacer BRAIN par ALT-AI, un fournisseur compatible "
    "mais legerement moins performant, qui n'acceptera pas la position en dessous "
    "de 8 points de revenu.",
    "Vous disposez de cinq minutes pour sauver votre ecosysteme.",
]

# --- Phases (sect. 7) -------------------------------------------------------
# key, libelle, duree conseillee en secondes (None = pas de chrono)

PHASES = [
    ("LOBBY", "Accueil et distribution des roles", None),
    ("R1_NEGO", "Round 1 - The Great Idea", 300),
    ("R1_DECIDE", "Round 1 - Decision JOIN / OUT", 60),
    ("R1_RESULTS", "Round 1 - Resultats", None),
    ("R2_NEGO", "Round 2 - Alignment", 480),
    ("R2_DECIDE", "Round 2 - Decision JOIN / OUT", 60),
    ("R2_RESULTS", "Round 2 - Resultats", None),
    ("MARKET", "Ecosystem market", 180),
    ("R3_ARCH", "Round 3 - Choix d'architecture", 180),
    ("R3_SHOCK", "Ecosystem shock", None),
    ("R3_NEGO", "Round 3 - Sauver l'ecosysteme", 300),
    ("R3_DECIDE", "Round 3 - Decision JOIN / OUT", 60),
    ("R3_RESULTS", "Round 3 - Resultats", None),
    ("FINAL", "Tableau final", None),
    ("DEBRIEF", "Debrief", 900),
]

PHASE_KEYS = [p[0] for p in PHASES]
PHASE_LABEL = {p[0]: p[1] for p in PHASES}
PHASE_DURATION = {p[0]: p[2] for p in PHASES}

DECISION_PHASES = {"R1_DECIDE": 1, "R2_DECIDE": 2, "R3_DECIDE": 3}
