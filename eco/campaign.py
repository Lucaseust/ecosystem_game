"""Campagne 2032 : etats persistants, contrats consentis, tirages et comptabilite.

Montants en centiemes de credit ; aucun nombre flottant dans les comptes.
Le registre des participants et le chronometre reutilisent le serveur existant.
"""

import copy
import csv
import hashlib
import io
import json
import secrets
import time
import uuid
import zipfile

from . import rules as R
from .engine import Game as Registry, GameError, new_state as registry_state

VERSION = "campaign-2.0"
RULES_VERSION = "campaign-3.0"
DATES = ["LOBBY", "JANUARY", "APRIL", "JULY", "OCTOBER", "FINAL", "DEBRIEF"]
LABELS = dict(
    zip(
        DATES,
        [
            "Installation de la salle",
            "Janvier–mars 2032",
            "Avril–juin 2032",
            "Juillet–septembre 2032",
            "Octobre–décembre 2032",
            "Décembre · bilan annuel",
            "Débrief",
        ],
        strict=True,
    )
)
PERIOD = {"JANUARY": 1, "APRIL": 2, "JULY": 3, "OCTOBER": 4}
INITIAL = 2000
ROLE_BRIEFS = {
    "MOBI": "Vous ne possédez ni les véhicules, ni l’IA de conduite, ni les stations de recharge, ni les opérations de terrain. Vous formulez la proposition de valeur et vous assemblez l’écosystème.",
    "AUTO": "Votre usine doit réaliser des adaptations spécifiques au projet. Si votre capacité reste disponible hors du service, vous pouvez l’utiliser pour une autre commande.",
    "BRAIN": "Votre technologie est propriétaire et peut être vendue à d’autres clients, dans les limites de vos engagements. Vous décidez de révéler ou non la valeur de votre activité extérieure.",
    "GRID": "L’adaptation de votre infrastructure au projet nécessite des investissements spécifiques.",
    "FLEET": "Vous assurez le fonctionnement quotidien du service : supervision, repositionnement et gestion des incidents, même lorsque toutes les technologies fonctionnent.",
}
CAPEX = {r: n * 100 for r, n in R.COST.items()}
OPEX = dict(MOBI=100, AUTO=200, BRAIN=200, GRID=100, FLEET=200)
OUTSIDE = {r: n * 100 for r, n in R.OUTSIDE.items()}
PROFILES = {
    "MOBI": [
        ("LOCAL", "Service local", 0, "La réservation et la relation client de base."),
        (
            "SUPPORT",
            "Relation client renforcée",
            200,
            "Un revenu commercial supplémentaire de 2 crédits par trimestre de service.",
        ),
    ],
    "AUTO": [
        ("DEDICATED", "Véhicules dédiés", 0, "Les véhicules sont adaptés au territoire."),
        (
            "FLEXIBLE",
            "Véhicules reconfigurables",
            200,
            "Une adaptation ou un remplacement ultérieur coûte 1 crédit de moins.",
        ),
    ],
    "BRAIN": [
        (
            "MOBILE",
            "Licence sans exclusivité",
            0,
            "Une éventuelle offre extérieure reste compatible avec votre licence, à une échéance contractuelle.",
        ),
        (
            "COMMITTED",
            "Licence exclusive jusqu'en décembre",
            0,
            "Votre engagement ajoute 2 crédits au revenu trimestriel du service ; vous renoncez à le quitter avant décembre.",
        ),
    ],
    "GRID": [
        ("BASE", "Recharge pour le pilote", 0, "La capacité nécessaire au service initial."),
        (
            "RESERVE",
            "Capacité de recharge en réserve",
            200,
            "Réduit de 2 crédits le coût d'une extension ou d'une intervention sur l'infrastructure.",
        ),
    ],
    "FLEET": [
        ("LEAN", "Exploitation standard", 0, "Organisation et tests de mise en service de base."),
        (
            "PREPARED",
            "Tests et continuité renforcés",
            200,
            "Réduit le risque d'interruption au lancement et de 2 crédits le coût d'une intervention.",
        ),
    ],
}
EVENTS = {
    "ORDINARY": (
        "La flotte poursuit ses trajets",
        "Aucun événement notable ce trimestre. Un nouvel accord en crédits est nécessaire pour ce tour.",
    ),
    "DEMAND": (
        "La ville demande davantage de trajets",
        "Un quartier voisin souhaite rejoindre votre service. Une extension exige des capacités supplémentaires et un accord sur leur financement.",
    ),
    "PARTNER": (
        "Une autre activité intéresse votre fournisseur d'IA",
        "BRAIN a reçu une proposition privée. Ses droits de mobilité et les engagements déjà signés restent applicables.",
    ),
    "INFRA": (
        "La recharge n'assure plus les trajets",
        "L'infrastructure de recharge est indisponible. La flotte reste à l'arrêt tant qu'une solution n'est pas financée et acceptée.",
    ),
    "AUDIT": (
        "Une nouvelle exigence de certification",
        "Une adaptation doit être réalisée avant de reprendre les trajets. Son coût dépend des interfaces et de la préparation déjà financées.",
    ),
    "PRIVATE_COST": (
        "Les conditions économiques des partenaires évoluent",
        "Un nouvel accord est nécessaire pour ce tour. Chaque entreprise conserve ses informations économiques privées et peut demander à rouvrir la discussion.",
    ),
    "PRICE_DROP": (
        "La ville réduit sa contribution aux trajets",
        "La contribution publique au service diminue jusqu'en décembre. Un nouvel accord doit répartir ces recettes plus faibles en crédits ; les investissements et les engagements restent en place.",
    ),
}
EVENT_WEIGHTS = [
    ("ORDINARY", 0.15),
    ("DEMAND", 0.15),
    ("PARTNER", 0.15),
    ("PRIVATE_COST", 0.20),
    ("PRICE_DROP", 0.15),
    ("INFRA", 0.10),
    ("AUDIT", 0.10),
]
COST_STORIES = {
    "AUTO": (
        "Les pièces de maintenance deviennent plus chères",
        "Votre fournisseur répercute une hausse du prix des composants sur les véhicules déjà déployés.",
    ),
    "GRID": (
        "Votre contrat d'énergie est révisé",
        "Le fournisseur d'énergie augmente le tarif de recharge des navettes.",
    ),
    "FLEET": (
        "L'assurance de l'exploitation est réévaluée",
        "L'assureur relève la prime pour exploiter les navettes autonomes sur votre territoire.",
    ),
}
ACTIONS = {
    "INSTALL": "Constituer et mettre en service la flotte",
    "REVISE": "Réviser le partage des revenus",
    "GROW": "Étendre le service",
    "REPAIR": "Adapter et remettre en service",
    "REPLACE": "Changer de fournisseur",
    "PAUSE": "Suspendre l'exploitation",
    "RESUME": "Reprendre l'exploitation",
    "STANDARDIZE": "Financer des interfaces communes",
    "RETURN": "Réintégrer le partenaire",
}


def new_state(code=None, team_count=2, seed=None):
    state = registry_state(code, team_count)
    state.update(
        schema=VERSION,
        session_id=uuid.uuid4().hex,
        seed=seed or secrets.token_hex(24),
        seed_origin="configured" if seed else "generated",
        journal=[],
        ledger=[],
        requests={},
        rules_version=RULES_VERSION,
    )
    return state


def empty_company():
    return dict(
        cash={r: INITIAL for r in R.ROLES},
        profiles={},
        installed=False,
        architecture=None,
        launch=None,
        contract=None,
        proposal=None,
        revision=0,
        operating=False,
        commissioned=False,
        missing=None,
        replaced=None,
        growth=False,
        incident=None,
        offer=None,
        return_request=None,
        history=[],
        settlements=[],
        created=0,
        revenue=0,
        expenses=0,
        visits=0,
        last_draw=None,
        resolved_dates=[],
        cost_shocks={},
        revenue_adjustment=0,
        quiet_streak=0,
        renegotiation_requests={},
    )


def integer(value, label, low=0, high=100):
    if isinstance(value, bool):
        raise GameError(label + " doit être un entier.")
    try:
        number = int(value)
    except (ValueError, TypeError, OverflowError):
        raise GameError(label + " doit être un entier.") from None
    if str(number) != str(value) or not low <= number <= high:
        raise GameError(label + " est hors limites.")
    return number


def allocations(contract, revenue=4000):
    """Read old saves without rewriting their historical journal."""
    if not contract:
        return {}
    if "allocations" in contract:
        return contract["allocations"]
    base = contract.get("full_capacity_revenue", revenue)
    amounts = {r: base * v // 100 for r, v in contract.get("shares", {}).items()}
    if amounts:
        amounts[next(iter(amounts))] += base - sum(amounts.values())
    return amounts


class Game(Registry):
    def __init__(self, state=None, on_change=None):
        state = state or new_state()
        if state.get("schema") != VERSION:
            raise GameError("Cette sauvegarde appartient à l'ancien jeu à manches.")
        super().__init__(state, on_change)
        for team in self.active_teams():
            c = self.c(team)
            for key in ("proposal", "contract"):
                current = c[key]
                if current and "shares" in current:
                    current["allocations"] = allocations(current, self.gross(team))
                    current.pop("shares")

    def c(self, team):
        return self.state["teams"][team].setdefault("campaign", empty_company())

    def org(self, team, role):
        return self.state["session_id"][:8] + ":" + team + ":" + role

    def snapshot(self, team):
        c = self.c(team)
        result = {
            k: copy.deepcopy(c[k])
            for k in (
                "cash",
                "profiles",
                "installed",
                "architecture",
                "launch",
                "operating",
                "missing",
                "replaced",
                "growth",
                "created",
                "revenue",
                "expenses",
            )
        }
        result.update(
            cost_shocks=copy.deepcopy(c.get("cost_shocks", {})),
            revenue_adjustment=c.get("revenue_adjustment", 0),
            renegotiation_requests=copy.deepcopy(c.get("renegotiation_requests", {})),
        )
        return result

    def record(self, kind, team=None, role=None, message=None, **data):
        self.state["rules_version"] = RULES_VERSION
        node = self.node(team) if team else None
        if team:
            visit_key = self.state["phase"] + ":" + node
            if self.c(team).get("last_node") != visit_key:
                self.c(team)["visits"] += 1
                self.c(team)["last_node"] = visit_key
        event = dict(
            event_id=uuid.uuid4().hex,
            sequence=len(self.state["journal"]) + 1,
            schema_version=VERSION,
            rules_version=RULES_VERSION,
            session_id=self.state["session_id"],
            occurred_at=time.time(),
            economic_date=self.state["phase"],
            ecosystem_id=team,
            org_id=self.org(team, role) if role else None,
            event_type=kind,
            node_id=node,
            visit_id=(team + ":" + str(self.c(team)["visits"])) if team else None,
            decision_id=getattr(self, "_request_id", None),
            public_message=message,
            data=copy.deepcopy(data),
        )
        if team:
            event["state_after"] = self.snapshot(team)
        self.state["journal"].append(event)
        if message and team:
            self.c(team)["history"].append(dict(date=self.state["phase"], text=message))
        return event["event_id"]

    def payment(self, team, role, amount, kind, cause, source="PROJECT"):
        c = self.c(team)
        if c["cash"][role] + amount < 0:
            raise GameError("Le financement de %s est insuffisant." % role)
        c["cash"][role] += amount
        self.state["ledger"].append(
            dict(
                transaction_id=uuid.uuid4().hex,
                session_id=self.state["session_id"],
                economic_date=self.state["phase"],
                ecosystem_id=team,
                org_id=self.org(team, role),
                role=role,
                amount=amount,
                kind=kind,
                source=source,
                cause_id=cause,
            )
        )
        if kind in ("INSTALLATION", "PROFILE", "ADAPTATION", "OPERATION"):
            c["expenses"] -= amount
            c["created"] += amount
        if kind == "REVENUE":
            c["revenue"] += amount
            c["created"] += amount

    def _guard_lobby(self):
        if self.state["phase"] != "LOBBY":
            raise GameError("La répartition des entreprises est figée depuis le début de l'année.")

    def set_team_count(self, n, _internal=False):
        self._guard_lobby()
        if not _internal:
            self.state["auto_teams"] = False
        super().set_team_count(n, _internal)
        for team in self.active_teams():
            self.c(team)

    def reassign(self, token, team, role):
        self._guard_lobby()
        super().reassign(token, team, role)

    def shuffle(self):
        self._guard_lobby()
        super().shuffle()

    def remove_player(self, token):
        with self.lock:
            p = self._player(token)
            team, role = p["team"], p["role"]
            super().remove_player(token)
            proposal = self.c(team)["proposal"]
            if self.is_bot(team, role) and not self.c(team)["installed"]:
                self.c(team)["profiles"].setdefault(role, PROFILES[role][0][0])
            if proposal and proposal["status"] == "OPEN" and self.is_bot(team, role):
                proposal["votes"].pop(role, None)
                self._bots(team)
                self.touch()

    def draw(self, team, channel):
        key = "|".join([self.state["seed"], team, self.state["phase"], channel])
        return int.from_bytes(hashlib.sha256(key.encode()).digest()[:8], "big") / 2**64

    def _playable(self):
        if self.state["phase"] not in PERIOD:
            raise GameError("Les décisions ne sont pas ouvertes à cette date.")

    def _profile_cost(self, role, key):
        return next((p[2] for p in PROFILES[role] if p[0] == key), 0)

    def available(self, team):
        c = self.c(team)
        if self.state["phase"] not in PERIOD:
            return []
        if not c["installed"]:
            return ["INSTALL"]
        if c["incident"]:
            options = ["REPAIR", "PAUSE"]
            if c["incident"]["target"] and not c["replaced"]:
                options.insert(1, "REPLACE")
            return options
        if c["missing"]:
            return (
                (["REPLACE"] if not c["replaced"] else [])
                + (["RETURN"] if c["return_request"] else [])
                + ["PAUSE"]
            )
        options = ["REVISE", "PAUSE"] if c["operating"] else ["RESUME"]
        demand = (
            c["last_draw"]
            and c["last_draw"]["date"] == self.state["phase"]
            and c["last_draw"]["kind"] == "DEMAND"
        )
        if not c["growth"] and c["operating"] and (demand or self.state["phase"] == "OCTOBER"):
            options.append("GROW")
        if c["architecture"] == "INTEGRATED":
            options.append("STANDARDIZE")
        if c["replaced"] and c["return_request"]:
            options.append("RETURN")
        return options

    def quote(self, team, action, architecture=None, launch=None):
        c = self.c(team)
        if action == "INSTALL":
            return (600 if architecture == "MODULAR" else 0) + (300 if launch == "PILOT" else 0)
        if action == "STANDARDIZE":
            return 800
        if action == "GROW":
            return (
                400 if c["profiles"].get("GRID") == "RESERVE" and c["replaced"] != "GRID" else 600
            )
        if action in ("REPAIR", "REPLACE"):
            target = (c["incident"] or {}).get("target") or c["missing"]
            cost = (
                (900 if action == "REPLACE" else 700) if c["architecture"] == "INTEGRATED" else 300
            )
            if target == "GRID" and self.profile_active(team, "GRID", "RESERVE"):
                cost -= 200
            if self.profile_active(team, "AUTO", "FLEXIBLE"):
                cost -= 100
            if self.profile_active(team, "FLEET", "PREPARED"):
                cost -= 200
            return max(100, cost)
        return 0

    def profile_active(self, team, role, profile):
        """A substitute does not inherit an absent company's investments."""
        c = self.c(team)
        return c["profiles"].get(role) == profile and role not in (c["missing"], c["replaced"])

    def gross(self, team):
        c = self.c(team)
        return self.capacity_revenue(team, c["architecture"], c["replaced"], c["growth"])

    def capacity_revenue(self, team, architecture, replaced, growth):
        c = self.c(team)
        value = 4000 if architecture == "INTEGRATED" else 3800
        value += 200 if c["profiles"].get("MOBI") == "SUPPORT" else 0
        value += 200 if c["profiles"].get("BRAIN") == "COMMITTED" and replaced != "BRAIN" else 0
        return max(0, value + (1000 if growth else 0) + c.get("revenue_adjustment", 0))

    def operating_cost(self, team, role):
        return OPEX[role] + self.c(team).get("cost_shocks", {}).get(role, {}).get("increase", 0)

    def can_withdraw(self, team, role):
        c = self.c(team)
        return (
            self.state["phase"] in PERIOD
            and role in c.get("cost_shocks", {})
            and c["operating"]
            and not c["incident"]
            and not c["missing"]
            and not c["replaced"]
        )

    def submit(self, team, role, body):
        if role != "MOBI":
            raise GameError(
                "MOBI publie la proposition ; chaque partenaire consent à son engagement."
            )
        c = self.c(team)
        action = body.get("kind")
        if action not in self.available(team):
            raise GameError("Cette solution n'est pas disponible dans la situation actuelle.")
        arch = body.get("architecture") if action == "INSTALL" else c["architecture"]
        if action == "STANDARDIZE":
            arch = "MODULAR"
        launch = body.get("launch") if action == "INSTALL" else c["launch"]
        if action == "INSTALL" and (
            arch not in ("INTEGRATED", "MODULAR") or launch not in ("EARLY", "PILOT")
        ):
            raise GameError("Choisissez les interfaces et le mode de lancement.")
        target = (
            ((c["incident"] or {}).get("target") or c["missing"])
            if action == "REPLACE"
            else c["replaced"]
        )
        if action == "RETURN":
            target = None
        keys = [r for r in R.ROLES if r != target] + (["ALT"] if target else [])
        revenue = self.capacity_revenue(team, arch, target, c["growth"] or action == "GROW")
        if set(body.get("allocations", {})) != set(keys):
            raise GameError(
                "Les montants en crédits doivent couvrir exactement les entreprises de cet accord."
            )
        amounts = {r: integer(body["allocations"][r], "Recettes de " + r, 0, 10000) for r in keys}
        if sum(amounts.values()) != revenue:
            raise GameError("Répartissez exactement %.2f crédits de recettes." % (revenue / 100))
        if target and amounts["ALT"] < 600:
            raise GameError("Un substitut demande au moins 6 crédits par trimestre.")
        funding = {
            r: integer(body.get("funding", {}).get(r, 0), "Contribution " + r, 0, 10000)
            for r in R.ROLES
        }
        need = self.quote(team, action, arch, launch)
        if sum(funding.values()) != need or target and funding[target]:
            raise GameError(
                "Les contributions doivent financer exactement %.0f crédits, sans facturer le partenaire écarté."
                % (need / 100)
            )
        for r in R.ROLES:
            installation = (
                (CAPEX[r] + self._profile_cost(r, c["profiles"].get(r)))
                if action == "INSTALL"
                else 0
            )
            if c["cash"][r] < funding[r] + installation:
                raise GameError("%s ne dispose pas du financement nécessaire." % r)
        if action == "INSTALL" and set(c["profiles"]) != set(R.ROLES):
            raise GameError("Chaque entreprise doit d'abord choisir son engagement d'installation.")
        if action == "RETURN" and not c["return_request"]:
            raise GameError("Le partenaire doit d'abord proposer son retour.")
        c["revision"] += 1
        proposal = dict(
            revision=c["revision"],
            kind=action,
            architecture=arch,
            launch=launch,
            allocations=amounts,
            funding=funding,
            required=[r for r in R.ROLES if r != target],
            excluded=target,
            votes={},
            status="OPEN",
            date=self.state["phase"],
            cost=need,
        )
        proposal["consequence"] = self.consequence(team, action)
        proposal["full_capacity_revenue"] = self.capacity_revenue(
            team, arch, target, c["growth"] or action == "GROW"
        )
        if action == "INSTALL":
            proposal["consequence"] = (
                "Les essais peuvent interrompre les recettes de la mise en service. "
                + (
                    "Le pilote progressif limite le premier trimestre exploité à 75 % des recettes à pleine capacité, avec un risque d'interruption réduit."
                    if launch == "PILOT"
                    else "L'ouverture vise la pleine capacité dès la validation des essais."
                )
            )
        c["proposal"] = proposal
        self.record(
            "proposal_published",
            team,
            role,
            "MOBI a publié une proposition : " + ACTIONS[action] + ".",
            proposal=proposal,
            available=self.available(team),
        )
        self._bots(team)

    def _bots(self, team):
        c = self.c(team)
        p = c["proposal"]
        if not p or p["status"] != "OPEN":
            return
        for role in p["required"]:
            if self.is_bot(team, role):
                gross = p["full_capacity_revenue"]
                quarters = 5 - PERIOD[self.state["phase"]]
                upfront = p["funding"][role] + (
                    (CAPEX[role] + self._profile_cost(role, c["profiles"][role]))
                    if p["kind"] == "INSTALL"
                    else 0
                )
                lost = (
                    gross // 4
                    if p["kind"] == "INSTALL" and p["launch"] == "PILOT"
                    else gross // 2
                    if p["kind"] == "REPAIR" and c["architecture"] == "INTEGRATED"
                    else gross
                    if p["kind"] == "REPLACE" and c["architecture"] == "INTEGRATED"
                    else 0
                )
                net = (
                    (gross * quarters - lost) * p["allocations"][role] // max(1, gross)
                    - self.operating_cost(team, role) * quarters
                    - upfront
                )
                if p["kind"] == "PAUSE" or p["kind"] == "STANDARDIZE" and not c["operating"]:
                    net = OUTSIDE[role] * quarters - upfront
                p["votes"][role] = "ACCEPT" if net >= OUTSIDE[role] * quarters else "REFUSE"
        if all(p["votes"].get(r) == "ACCEPT" for r in p["required"]):
            self.commit(team)

    def commit(self, team):
        c = self.c(team)
        p = c["proposal"]
        action = p["kind"]
        before = self.snapshot(team)
        cause = uuid.uuid4().hex
        # Revalidation au moment d'engager : une dépense ne peut utiliser un ancien devis.
        if action not in self.available(team):
            raise GameError("La situation a changé. Une nouvelle proposition est nécessaire.")
        if sum(p["funding"].values()) != self.quote(
            team, action, p["architecture"], p["launch"]
        ) or sum(p["allocations"].values()) != self.capacity_revenue(
            team, p["architecture"], p["excluded"], c["growth"] or action == "GROW"
        ):
            raise GameError("Le devis a changé. Publiez une nouvelle proposition en crédits.")
        for r in R.ROLES:
            need = p["funding"][r] + (
                (CAPEX[r] + self._profile_cost(r, c["profiles"][r])) if action == "INSTALL" else 0
            )
            if c["cash"][r] < need:
                raise GameError("Le financement a changé pour %s. Republiez un accord." % r)
        for r in R.ROLES:
            if action == "INSTALL":
                self.payment(team, r, -CAPEX[r], "INSTALLATION", cause)
                extra = self._profile_cost(r, c["profiles"][r])
                if extra:
                    self.payment(team, r, -extra, "PROFILE", cause)
            if p["funding"][r]:
                self.payment(team, r, -p["funding"][r], "ADAPTATION", cause)
        if action == "INSTALL":
            c.update(installed=True, architecture=p["architecture"], launch=p["launch"])
        if action == "GROW":
            c["growth"] = True
            c["growth_trial_pending"] = True
        if action == "STANDARDIZE":
            c["architecture"] = "MODULAR"
        if action == "REPLACE":
            target = (c["incident"] or {}).get("target") or c["missing"]
            c.update(replaced=target, missing=None, return_request=None)
            c["replacement_delay"] = (
                self.state["phase"] if c["architecture"] == "INTEGRATED" else None
            )
        if action == "RETURN":
            c.update(missing=None, replaced=None, return_request=None)
        if action == "REPAIR" and c["architecture"] == "INTEGRATED":
            c["intervention_delay"] = self.state["phase"]
        if action == "PAUSE":
            c["operating"] = False
        elif action in ("INSTALL", "GROW", "REPAIR", "REPLACE", "RESUME", "RETURN"):
            c["operating"] = True
        if action in ("INSTALL", "REPAIR", "REPLACE", "RETURN"):
            c["incident"] = None
        if c["last_draw"] and (
            (c["last_draw"]["kind"] in ("INFRA", "AUDIT") and action in ("REPAIR", "REPLACE"))
            or (c["last_draw"]["kind"] == "DEMAND" and action == "GROW")
        ):
            c["last_draw"]["resolved"] = True
        c["contract"] = copy.deepcopy(
            {
                k: p[k]
                for k in (
                    "revision",
                    "allocations",
                    "funding",
                    "date",
                    "excluded",
                    "full_capacity_revenue",
                )
            }
        )
        c["renegotiation_requests"] = {}
        p["status"] = "APPLIED"
        self.record(
            "contract_committed",
            team,
            message=ACTIONS[action] + " : les entreprises concernées ont accepté.",
            cause_id=cause,
            state_before=before,
            proposal=copy.deepcopy(p),
        )

    def action(self, token, body):
        with self.lock:
            player = self._player(token)
            request_id = body.get("request_id")
            if not isinstance(request_id, str) or not 8 <= len(request_id) <= 100:
                raise GameError("Une référence de décision est nécessaire.")
            fingerprint = hashlib.sha256(json.dumps(body, sort_keys=True).encode()).hexdigest()
            key = token + ":" + request_id
            if key in self.state["requests"]:
                if self.state["requests"][key] != fingerprint:
                    raise GameError("Cette référence a déjà été utilisée pour une autre décision.")
                return
            before = copy.deepcopy(self.state)
            self._request_id = request_id
            try:
                self._playable()
                team, role = player["team"], player["role"]
                c = self.c(team)
                action = body.get("action")
                context = dict(
                    cash=c["cash"][role],
                    profile=c["profiles"].get(role),
                    outside=OUTSIDE[role],
                    available=self.available(team),
                    installation_cost=CAPEX[role],
                    operating_cost=self.operating_cost(team, role),
                    private_shock=copy.deepcopy(c.get("cost_shocks", {}).get(role)),
                    revenue_adjustment=c.get("revenue_adjustment", 0),
                    offer=copy.deepcopy(c["offer"]) if role == "BRAIN" else None,
                    contract=copy.deepcopy(c["contract"]),
                    architecture=c["architecture"],
                    proposal=copy.deepcopy(c["proposal"]),
                    incident=copy.deepcopy(c["incident"]),
                )
                if context["proposal"]:
                    context["own_response"] = context["proposal"]["votes"].get(role)
                    context["proposal"].pop("votes", None)
                if action == "profile":
                    if c["installed"]:
                        raise GameError("Cet investissement est déjà engagé.")
                    choice = body.get("choice")
                    if choice not in [p[0] for p in PROFILES[role]]:
                        raise GameError("Engagement inconnu.")
                    c["profiles"][role] = choice
                    if c["proposal"] and c["proposal"]["status"] == "OPEN":
                        c["proposal"]["status"] = "SUPERSEDED"
                    self.record(
                        "profile_selected",
                        team,
                        role,
                        role + " a précisé son engagement d'installation.",
                        choice=choice,
                        information=context,
                        options=PROFILES[role],
                    )
                elif action == "propose":
                    self.submit(team, role, body)
                elif action == "consent":
                    p = c["proposal"]
                    if not p or p["status"] != "OPEN" or body.get("revision") != p["revision"]:
                        raise GameError(
                            "Cette proposition n'est plus ouverte. Relisez la version courante."
                        )
                    if role not in p["required"] or body.get("choice") not in ("ACCEPT", "REFUSE"):
                        raise GameError(
                            "Vous n'avez pas d'engagement à valider dans cette proposition."
                        )
                    reason = body.get("reason", "")
                    if not isinstance(reason, str) or len(reason) > 400:
                        raise GameError("Votre explication est limitée à 400 caractères.")
                    if reason.strip():
                        c.setdefault("discussion", []).append(
                            dict(
                                role=role,
                                target="ALL",
                                text=reason.strip(),
                                date=self.state["phase"],
                                revision=p["revision"],
                                choice=body["choice"],
                            )
                        )
                    p["votes"][role] = body["choice"]
                    self.record(
                        "consent_submitted",
                        team,
                        role,
                        choice=body["choice"],
                        revision=p["revision"],
                        information=context,
                    )
                    self._bots(team)
                elif action == "claim":
                    text = body.get("text", "")
                    if not isinstance(text, str) or len(text) > 160:
                        raise GameError("Votre message est limité à 160 caractères.")
                    self.state["teams"][team]["claims"][role] = dict(text=text.strip())
                    self.record("message_posted", team, role, text=text.strip())
                elif action in ("discuss", "negotiate"):
                    text = body.get("text", "")
                    target = body.get("target", "ALL")
                    if not isinstance(text, str) or not 1 <= len(text.strip()) <= 400:
                        raise GameError("Expliquez votre décision en 1 à 400 caractères.")
                    if target not in ["ALL", *R.ROLES]:
                        raise GameError("Destinataire inconnu.")
                    entry = dict(
                        role=role,
                        target=target,
                        text=text.strip(),
                        date=self.state["phase"],
                        revision=c["revision"],
                    )
                    if action == "negotiate":
                        entry.update(
                            minimum=integer(body.get("minimum"), "Recettes demandées", 0, 10000),
                            maximum=integer(
                                body.get("maximum"), "Investissement proposé", 0, 10000
                            ),
                        )
                        c.setdefault("positions", {})[role] = copy.deepcopy(entry)
                    c.setdefault("discussion", []).append(entry)
                    self.record(
                        "negotiation_position" if action == "negotiate" else "discussion_posted",
                        team,
                        role,
                        entry=entry,
                    )
                elif action == "leave":
                    offer = c["offer"]
                    if (
                        role != "BRAIN"
                        or not offer
                        or offer["date"] != self.state["phase"]
                        or c["profiles"].get(role) == "COMMITTED"
                        or c["replaced"]
                        or c["missing"]
                    ):
                        raise GameError("Votre contrat ou la situation ne permet pas ce départ.")
                    c.update(missing=role, operating=False)
                    if c["proposal"] and c["proposal"]["status"] == "OPEN":
                        c["proposal"]["status"] = "SUPERSEDED"
                    self.record(
                        "partner_left",
                        team,
                        role,
                        "BRAIN quitte l'exploitation ; ses droits et ses gains antérieurs sont conservés.",
                        information=context,
                    )
                elif action == "return_request":
                    if role not in (c["missing"], c["replaced"]):
                        raise GameError("Votre entreprise occupe déjà sa position.")
                    c["return_request"] = role
                    self.record(
                        "return_requested",
                        team,
                        role,
                        role + " propose son retour ; un nouvel accord est nécessaire.",
                    )
                elif action == "renegotiate":
                    if not c["installed"] or role in (c["missing"], c["replaced"]):
                        raise GameError("Votre entreprise n'est pas engagée dans cet accord.")
                    requests = c.setdefault("renegotiation_requests", {})
                    if role not in requests:
                        requests[role] = dict(
                            date=self.state["phase"], revision=c["contract"]["revision"]
                        )
                        self.record(
                            "renegotiation_requested",
                            team,
                            role,
                            role + " demande à rouvrir la négociation du contrat.",
                            information=context,
                        )
                elif action == "withdraw":
                    if not self.can_withdraw(team, role):
                        raise GameError(
                            "La situation ne permet pas de suspendre votre activité dans la flotte."
                        )
                    c.update(missing=role, operating=False)
                    if c["proposal"] and c["proposal"]["status"] == "OPEN":
                        c["proposal"]["status"] = "SUPERSEDED"
                    self.record(
                        "capacity_withdrawn",
                        team,
                        role,
                        role
                        + " suspend son activité dans la flotte. Le service est interrompu jusqu'à un nouvel accord de retour ou de remplacement.",
                        information=context,
                    )
                else:
                    raise GameError("Action inconnue.")
                self.state["requests"][key] = fingerprint
                self.touch()
            except BaseException:
                self.state.clear()
                self.state.update(before)
                raise
            finally:
                self._request_id = None

    def event_candidates(self, team):
        c = self.c(team)
        eligible = c["installed"] and c["operating"] and not c["incident"] and not c["missing"]
        excluded = {}
        quiet = c.get("quiet_streak", int((c.get("last_draw") or {}).get("kind") == "ORDINARY"))
        for name, _ in EVENT_WEIGHTS:
            if not eligible and name != "ORDINARY":
                excluded[name] = (
                    "Pas de flotte en exploitation disponible pour ce nouvel événement."
                )
            elif name == "ORDINARY" and eligible and quiet:
                excluded[name] = "La période précédente était déjà calme."
            elif name == "DEMAND" and c["growth"]:
                excluded[name] = "L'extension a déjà été réalisée."
            elif name == "PARTNER" and (
                c["replaced"] or c["profiles"].get("BRAIN") == "COMMITTED" or c["offer"]
            ):
                excluded[name] = (
                    "Une nouvelle offre de mobilité n'est pas compatible avec les engagements actuels."
                )
            elif name == "INFRA" and c["replaced"]:
                excluded[name] = "Une autre position est déjà confiée à un substitut."
            elif name == "PRIVATE_COST" and not self.cost_targets(team):
                excluded[name] = "Toutes les entreprises éligibles ont déjà subi cette hausse."
            elif name == "PRICE_DROP" and c.get("revenue_adjustment", 0):
                excluded[name] = "La baisse de contribution publique est déjà en vigueur."
        candidates = [(name, weight) for name, weight in EVENT_WEIGHTS if name not in excluded]
        total = sum(weight for _, weight in candidates)
        return [(name, weight / total) for name, weight in candidates], excluded, eligible

    def cost_targets(self, team):
        c = self.c(team)
        return [
            r
            for r in COST_STORIES
            if r not in c.get("cost_shocks", {}) and r not in (c["missing"], c["replaced"])
        ]

    @staticmethod
    def choose_event(u, weights):
        acc = 0
        for name, weight in weights:
            acc += weight
            if u < acc:
                return name
        return weights[-1][0]

    def _event(self, team):
        c = self.c(team)
        weights, excluded, eligible = self.event_candidates(team)
        u = self.draw(team, "external_event")
        selected = self.choose_event(u, weights)
        c["quiet_streak"] = (
            (c.get("quiet_streak", 0) + 1) if eligible and selected == "ORDINARY" else 0
        )
        c["last_draw"] = dict(
            kind=selected,
            title=EVENTS[selected][0],
            text=EVENTS[selected][1],
            date=self.state["phase"],
        )
        if not c["installed"]:
            c["last_draw"].update(
                title="Le mandat de la ville reste ouvert",
                text="Le premier accord n'a pas encore permis de constituer la flotte. Les ressources et les engagements déjà pris restent disponibles pour votre nouvelle proposition.",
            )
        elif c["incident"] or c["missing"]:
            c["last_draw"].update(
                title="La situation précédente reste à résoudre",
                text="L'activité manquante n'a pas été rétablie. Le passage du calendrier ne répare pas la flotte et ne rembourse pas les investissements.",
            )
        elif not c["operating"]:
            c["last_draw"].update(
                title="Les navettes restent au dépôt",
                text="L'exploitation est suspendue. Les actifs sont conservés ; un accord de reprise reste nécessaire pour facturer des trajets.",
            )
        if selected in ("INFRA", "AUDIT"):
            c["incident"] = dict(kind=selected, target="GRID" if selected == "INFRA" else None)
            c["operating"] = False
        if selected == "PARTNER":
            c["offer"] = dict(date=self.state["phase"], bonus=500)
        shock = None
        if selected in ("PRIVATE_COST", "PRICE_DROP"):
            intensity_u = self.draw(team, "event_intensity")
            level = min(2, int(intensity_u * 3))
            if selected == "PRIVATE_COST":
                targets = self.cost_targets(team)
                target_u = self.draw(team, "event_target")
                role = targets[min(len(targets) - 1, int(target_u * len(targets)))]
                title, text = COST_STORIES[role]
                shock = dict(
                    kind=selected,
                    role=role,
                    date=self.state["phase"],
                    increase=[200, 300, 400][level],
                    title=title,
                    text=text,
                    intensity_u=intensity_u,
                    target_u=target_u,
                    target_candidates=targets,
                    expires="FINAL",
                )
                c.setdefault("cost_shocks", {})[role] = shock
            else:
                decrease = [600, 1000, 1400][level]
                c["revenue_adjustment"] = -decrease
                shock = dict(
                    kind=selected,
                    date=self.state["phase"],
                    adjustment=-decrease,
                    intensity_u=intensity_u,
                    expires="FINAL",
                )
                c["last_draw"]["text"] += (
                    " Les recettes à pleine capacité baissent de %.0f crédits par trimestre et passent à %.0f crédits, avant les frais des entreprises."
                    % (decrease / 100, self.gross(team) / 100)
                )
        self.record(
            "event_drawn",
            team,
            message=c["last_draw"]["title"] + ".",
            channel="external_event",
            candidates=weights,
            base_candidates=EVENT_WEIGHTS,
            excluded=excluded,
            u=u,
            selected=selected,
            original=self.choose_event(u, EVENT_WEIGHTS),
            eligible=eligible,
            intensity=shock,
            origin="RANDOM",
        )
        if shock:
            self.record(
                "shock_applied",
                team,
                shock.get("role"),
                shock=shock,
                public=selected == "PRICE_DROP",
            )

    def _settle(self, team):
        c = self.c(team)
        date = self.state["phase"]
        if date in c["resolved_dates"]:
            return
        c["resolved_dates"].append(date)
        p = c["proposal"]
        if p and p["status"] == "OPEN":
            p["status"] = "EXPIRED"
            self.record(
                "proposal_expired",
                team,
                message="La proposition non acceptée expire. Sans accord pour ce tour, le gain est nul ; aucun contrat précédent n'est reconduit.",
                proposal=copy.deepcopy(p),
            )
        agreed = (
            p
            and p["status"] == "APPLIED"
            and p["date"] == date
            and c["contract"]
            and c["contract"]["date"] == date
        )
        if not agreed:
            message = "Sans accord unanime pour ce tour : 0 crédit de gain, aucun frais d'exploitation ni revenu extérieur. Les investissements déjà payés restent acquis."
            result = dict(
                date=date,
                revenue=0,
                operating=False,
                created=c["created"],
                cash=copy.deepcopy(c["cash"]),
                message=message,
                agreement=False,
            )
            c["settlements"].append(result)
            self.record("quarter_settled", team, message=message, result=result)
            return
        active = c["installed"] and c["operating"] and not c["missing"] and not c["incident"]
        gross = self.gross(team) if active else 0
        cause = uuid.uuid4().hex
        if active and not c["commissioned"]:
            c["commissioned"] = True
            reinforced = self.profile_active(team, "FLEET", "PREPARED")
            probability = (
                (0.03 if reinforced else 0.05)
                if c["launch"] == "PILOT"
                else (0.25 if reinforced else 0.45)
            )
            u = self.draw(team, "commissioning")
            failure = u < probability
            self.record(
                "risk_drawn",
                team,
                channel="commissioning",
                probability=probability,
                u=u,
                selected="INTERRUPTION" if failure else "READY",
                intensity=1,
                origin="RANDOM",
            )
            if failure:
                gross = 0
                self.record(
                    "commissioning_interrupted",
                    team,
                    message="Les essais de mise en service ont interrompu le pilote ce trimestre. Les actifs restent en place.",
                )
            elif c["launch"] == "PILOT":
                gross = gross * 75 // 100
        if c.get("replacement_delay") == date:
            gross = 0
            self.record(
                "replacement_delay",
                team,
                message="L'intégration du substitut mobilise ce trimestre ; les trajets reprendront à la prochaine date.",
            )
        elif c.get("intervention_delay") == date:
            gross //= 2
            self.record(
                "intervention_delay",
                team,
                message="L'intervention sur les interfaces spécifiques a mobilisé la moitié du trimestre : les recettes disponibles sont réduites de moitié.",
            )
        if gross and c.get("growth_trial_pending"):
            probability = (
                0.08
                if self.profile_active(team, "GRID", "RESERVE")
                or self.profile_active(team, "FLEET", "PREPARED")
                else 0.35
            )
            u = self.draw(team, "expansion")
            c["growth_trial_pending"] = False
            self.record(
                "risk_drawn",
                team,
                channel="expansion",
                probability=probability,
                u=u,
                selected="OVERLOAD" if u < probability else "READY",
                intensity=1,
                origin="RANDOM",
            )
            if u < probability:
                gross //= 2
                self.record(
                    "expansion_overload",
                    team,
                    message="La montée en charge a réduit de moitié les trajets facturables de ce trimestre. La capacité financée reste installée.",
                )
        contract = c["contract"]
        amounts = allocations(contract, self.gross(team))
        base = sum(amounts.values())
        payouts = {r: gross * amount // max(1, base) for r, amount in amounts.items()}
        if payouts:
            payouts[next(iter(payouts))] += gross - sum(payouts.values())
        if active and any(
            c["cash"][r] + payouts.get(r, 0) < self.operating_cost(team, r)
            for r in R.ROLES
            if r != c["replaced"]
        ):
            gross, payouts = 0, {}
            c["operating"] = False
            active = False
            self.record(
                "funding_shortfall",
                team,
                message="L'exploitation manque de financement. Les actifs sont conservés ; un nouvel accord est nécessaire.",
            )
        for role in R.ROLES:
            if active and role != c["replaced"]:
                if gross:
                    self.payment(team, role, payouts[role], "REVENUE", cause, "CUSTOMERS")
                self.payment(
                    team,
                    role,
                    -self.operating_cost(team, role),
                    "OPERATION",
                    cause,
                    "OPERATING_COST",
                )
            else:
                outside = OUTSIDE[role]
                if role == "BRAIN" and role in (c["replaced"], c["missing"]) and c["offer"]:
                    outside += c["offer"]["bonus"]
                if role == "AUTO" and c["installed"] and c["profiles"].get(role) == "FLEXIBLE":
                    outside += 100
                if outside:
                    self.payment(team, role, outside, "OUTSIDE", cause, "OTHER_CUSTOMERS")
        if gross and c["replaced"]:
            # Un substitut est un fournisseur exterieur, pas une sixieme entreprise humaine.
            c["expenses"] += payouts["ALT"]
            c["created"] -= payouts["ALT"]
            c["revenue"] += payouts["ALT"]
            c["created"] += payouts["ALT"]
            self.state["ledger"].append(
                dict(
                    transaction_id=uuid.uuid4().hex,
                    session_id=self.state["session_id"],
                    economic_date=date,
                    ecosystem_id=team,
                    org_id=self.org(team, "ALT_" + c["replaced"]),
                    role="ALT",
                    provider_for=c["replaced"],
                    amount=payouts["ALT"],
                    kind="EXTERNAL_SUPPLIER",
                    source="CUSTOMERS",
                    cause_id=cause,
                )
            )
        if not c["installed"]:
            message = "Faute d'accord de lancement, aucun trajet n'a été facturé ce trimestre. Aucune installation n'a été débitée ; les activités extérieures disponibles ont été rémunérées. Ce trimestre de transport ne sera pas rattrapé."
        else:
            message = (
                ("Les trajets ont produit %.2f crédits de recettes ce trimestre." % (gross / 100))
                if gross
                else (
                    "Aucune recette de transport ce trimestre. L'exploitation engagée reste à financer."
                    if active
                    else "Aucune recette de transport ce trimestre ; les activités extérieures disponibles ont été réglées."
                )
            )
        result = dict(
            date=date,
            revenue=gross,
            operating=bool(gross),
            created=c["created"],
            cash=copy.deepcopy(c["cash"]),
            message=message,
        )
        c["settlements"].append(result)
        self.record("quarter_settled", team, message=message, result=result, cause_id=cause)

    def step(self, delta=1):
        if delta != 1:
            raise GameError(
                "Le calendrier avance sans effacer les engagements. Utilisez une nouvelle campagne pour recommencer."
            )
        with self.lock:
            before = copy.deepcopy(self.state)
            try:
                index = DATES.index(self.state["phase"])
                if index == len(DATES) - 1:
                    return
                if self.state["phase"] in PERIOD:
                    for team in self.active_teams():
                        self._settle(team)
                self.state["phase"] = DATES[index + 1]
                for team in self.active_teams():
                    c = self.c(team)
                    if self.state["phase"] == "JANUARY":
                        for role in R.ROLES:
                            if self.is_bot(team, role):
                                c["profiles"].setdefault(role, PROFILES[role][0][0])
                    if self.state["phase"] in ("APRIL", "JULY", "OCTOBER"):
                        self._event(team)
                    message = (
                        LABELS[self.state["phase"]]
                        + " : votre histoire continue avec les engagements déjà pris."
                    )
                    if self.state["phase"] in PERIOD and not c["installed"]:
                        remaining = 5 - PERIOD[self.state["phase"]]
                        message = (
                            LABELS[self.state["phase"]]
                            + f" : le mandat reste ouvert. Il reste {remaining} trimestre{'s' if remaining > 1 else ''}, celui-ci compris, pour exploiter la flotte. Les autres territoires poursuivent leur propre histoire."
                        )
                    self.record("date_opened", team, message=message)
                duration = None if self.state["phase"] in ("FINAL", "DEBRIEF") else 480
                self.state["timer"] = dict(
                    running=False, ends_at=None, remaining=duration, duration=duration
                )
                self.touch()
            except BaseException:
                self.state.clear()
                self.state.update(before)
                raise

    def timer_reset(self):
        with self.lock:
            duration = 480 if self.state["phase"] in PERIOD else None
            self.state["timer"] = dict(
                running=False, ends_at=None, remaining=duration, duration=duration
            )
            self.touch()

    def team_view(self, team, role=None, final=False):
        c = self.c(team)
        p = copy.deepcopy(c["proposal"])
        if p:
            p["allocations"] = copy.deepcopy(allocations(p, self.gross(team)))
            p.pop("shares", None)
            p["answered"] = len(p["votes"])
            p["mine"] = p["votes"].get(role) if role else None
            if p["status"] not in ("APPLIED", "EXPIRED"):
                p.pop("votes")
        seats = {
            r: dict(names=[x["name"] for x in self.seat_of(team, r)], bot=self.is_bot(team, r))
            for r in R.ROLES
        }
        options = [
            dict(
                key=a,
                label=ACTIONS[a],
                cost=self.quote(team, a),
                consequence=self.consequence(team, a),
            )
            for a in self.available(team)
        ]
        contract = copy.deepcopy(c["contract"])
        if contract:
            contract["allocations"] = copy.deepcopy(allocations(contract, self.gross(team)))
            contract.pop("shares", None)
        return dict(
            team=team,
            node=self.node(team),
            seats=seats,
            proposal=p,
            contract=contract,
            agreement_current=bool(
                contract
                and contract["date"] == self.state["phase"]
                and p
                and p["status"] == "APPLIED"
            ),
            positions=copy.deepcopy(c.get("positions", {})),
            discussion=copy.deepcopy(c.get("discussion", [])[-100:]),
            installed=c["installed"],
            operating=c["operating"],
            architecture=c["architecture"],
            launch=c["launch"],
            profile_keys=copy.deepcopy(c["profiles"]),
            profiles={
                r: next(p[1] for p in PROFILES[r] if p[0] == v) for r, v in c["profiles"].items()
            },
            missing=c["missing"],
            replaced=c["replaced"],
            growth=c["growth"],
            incident=copy.deepcopy(c["incident"]),
            news=copy.deepcopy(c["last_draw"])
            if c["last_draw"]
            and c["last_draw"]["date"] == self.state["phase"]
            and not c["last_draw"].get("resolved")
            else None,
            return_request=c["return_request"],
            options=options,
            revenue_adjustment=c.get("revenue_adjustment", 0),
            full_capacity_revenue=self.gross(team) if c["installed"] else None,
            renegotiation_requests=copy.deepcopy(c.get("renegotiation_requests", {})),
            claims=copy.deepcopy(self.state["teams"][team]["claims"]),
            history=copy.deepcopy(c["history"]),
            settlements=copy.deepcopy(c["settlements"])
            if final
            else [
                {k: v for k, v in row.items() if k not in ("cash", "created")}
                for row in c["settlements"]
            ],
            created=c["created"] if final else None,
            revenue=c["revenue"],
            expenses=c["expenses"] if final else None,
            cash=copy.deepcopy(c["cash"]) if final else None,
        )

    def node(self, team):
        c = self.c(team)
        if self.state["phase"] == "LOBBY":
            return "MANDATE"
        if self.state["phase"] in ("FINAL", "DEBRIEF"):
            return "CLOSED"
        if not c["installed"]:
            return "FOUNDING"
        if c["incident"]:
            return "INCIDENT"
        if c["missing"]:
            return "MISSING_PARTNER"
        if not c["operating"]:
            return "PAUSED"
        if (
            c["last_draw"]
            and c["last_draw"]["date"] == self.state["phase"]
            and not c["last_draw"].get("resolved")
            and c["last_draw"]["kind"] in ("DEMAND", "PARTNER")
        ):
            return c["last_draw"]["kind"]
        if c.get("renegotiation_requests"):
            return "RENEGOTIATION"
        if (
            c["last_draw"]
            and c["last_draw"]["date"] == self.state["phase"]
            and c["last_draw"]["kind"] == "PRICE_DROP"
        ):
            return "REVENUE_PRESSURE"
        return "OPERATING" if c["operating"] else "PAUSED"

    def consequence(self, team, action):
        c = self.c(team)
        if action == "STANDARDIZE" and not c["operating"]:
            return "Les interfaces deviendront communes ; l'exploitation restera suspendue jusqu'à un accord de reprise."
        if c["architecture"] == "INTEGRATED":
            if action == "REPLACE":
                return "L'adaptation des interfaces spécifiques occupe ce trimestre : les recettes du transport reprendront à la prochaine date. Les frais d'exploitation restent dus."
            if action == "REPAIR":
                return "La modification des interfaces spécifiques mobilise la moitié du trimestre : les recettes de cette période seront réduites de moitié."
        if action in ("REPAIR", "REPLACE"):
            return "Les interfaces communes permettent la reprise durant ce trimestre, après l'accord et le financement."
        return ""

    def player_view(self, token):
        with self.lock:
            p = self._player(token)
            c = self.c(p["team"])
            role = p["role"]
            final = self.state["phase"] in ("FINAL", "DEBRIEF")
            return dict(
                schema=VERSION,
                rules_version=RULES_VERSION,
                version=self.state["version"],
                server_time=time.time(),
                phase=self.state["phase"],
                phase_label=LABELS[self.state["phase"]],
                timer=copy.deepcopy(self.state["timer"]),
                me=dict(
                    name=p["name"],
                    first_name=p.get("first_name", ""),
                    last_name=p.get("last_name", ""),
                    identity_required=p.get("identity_required", False),
                    role=role,
                    team=p["team"],
                    org_id=self.org(p["team"], role),
                    cash=c["cash"][role],
                    initial=INITIAL,
                    cost=CAPEX[role],
                    operating_cost=self.operating_cost(p["team"], role),
                    base_operating_cost=OPEX[role],
                    outside=OUTSIDE[role],
                    private_shock=copy.deepcopy(c.get("cost_shocks", {}).get(role)),
                    can_withdraw=self.can_withdraw(p["team"], role),
                    profile=c["profiles"].get(role),
                    profile_options=PROFILES[role]
                    if not c["installed"] and self.state["phase"] in PERIOD
                    else [],
                    profile_cost=self._profile_cost(role, c["profiles"].get(role)),
                    transactions=[
                        {k: row[k] for k in ("economic_date", "amount", "kind")}
                        for row in self.state["ledger"]
                        if row["ecosystem_id"] == p["team"] and row["role"] == role
                    ],
                    offer=copy.deepcopy(c["offer"]) if role == "BRAIN" else None,
                    can_leave=role == "BRAIN"
                    and bool(c["offer"])
                    and c["offer"]["date"] == self.state["phase"]
                    and c["profiles"].get(role) != "COMMITTED"
                    and not c["missing"]
                    and not c["replaced"]
                    and self.state["phase"] in PERIOD,
                    outside_position=role in (c["missing"], c["replaced"]),
                    card=dict(brief=ROLE_BRIEFS[role]),
                ),
                team=self.team_view(p["team"], role, final),
            )

    def host_view(self):
        with self.lock:
            final = self.state["phase"] in ("FINAL", "DEBRIEF")
            from .debrief import build as build_debrief

            return dict(
                schema=VERSION,
                rules_version=RULES_VERSION,
                version=self.state["version"],
                server_time=time.time(),
                code=self.state["code"],
                phase=self.state["phase"],
                phase_label=LABELS[self.state["phase"]],
                timer=copy.deepcopy(self.state["timer"]),
                team_count=self.state["team_count"],
                teams={t: self.team_view(t, final=final) for t in self.active_teams()},
                players=[
                    {
                        k: p.get(k)
                        for k in (
                            "id",
                            "name",
                            "first_name",
                            "last_name",
                            "identity_required",
                            "team",
                            "role",
                        )
                    }
                    for p in self.state["players"].values()
                ],
                can_export=final,
                event_count=len(self.state["journal"]),
                debrief=build_debrief(self) if final else None,
            )

    def export(self):
        with self.lock:
            if self.state["phase"] not in ("FINAL", "DEBRIEF"):
                raise GameError(
                    "L'export complet est disponible au bilan, après clôture des décisions privées."
                )
            output = io.BytesIO()
            events = self.state["journal"]

            def csv_text(rows):
                rows = list(rows)
                if not rows:
                    return "\ufeffevent_id\n"
                columns = list(dict.fromkeys(k for row in rows for k in row))
                stream = io.StringIO(newline="")
                writer = csv.DictWriter(stream, fieldnames=columns)
                writer.writeheader()
                for row in rows:
                    writer.writerow(
                        {
                            k: json.dumps(v, ensure_ascii=False)
                            if isinstance(v, (dict, list))
                            else v
                            for k, v in row.items()
                        }
                    )
                return "\ufeff" + stream.getvalue()

            rule_sets = {
                VERSION: dict(
                    event_dates=["APRIL", "JULY"],
                    external_event_weights=dict(
                        ORDINARY=0.2, DEMAND=0.25, PARTNER=0.2, INFRA=0.2, AUDIT=0.15
                    ),
                    event_policy="Incompatible draws become ORDINARY",
                ),
                RULES_VERSION: dict(
                    event_dates=["APRIL", "JULY", "OCTOBER"],
                    external_event_weights=dict(EVENT_WEIGHTS),
                    event_policy="Compatible candidates normalized; no consecutive quiet operating periods; candidates and exclusions logged per draw",
                    private_cost_increases=[200, 300, 400],
                    public_revenue_decreases=[600, 1000, 1400],
                    allocation_unit="integer hundredths of a credit",
                    agreement_required_each_quarter=True,
                    no_agreement_policy="Zero revenue, operating charges and outside income; paid investments preserved",
                ),
            }
            rule_sets["campaign-2.1"] = {
                k: v
                for k, v in rule_sets[RULES_VERSION].items()
                if k
                not in {"allocation_unit", "agreement_required_each_quarter", "no_agreement_policy"}
            }
            version = self.state.get("rules_version", VERSION)
            metadata = dict(
                schema=VERSION,
                rules_version=version,
                engine_rules_version=RULES_VERSION,
                rules_versions_in_journal=sorted({e["rules_version"] for e in events}),
                rule_sets=rule_sets,
                session_id=self.state["session_id"],
                seed=self.state["seed"],
                seed_origin=self.state.get("seed_origin", "generated"),
                dates=LABELS,
                amount_unit="centicredit",
                initial_cash=INITIAL,
                capex=CAPEX,
                opex=OPEX,
                outside=OUTSIDE,
                profiles=PROFILES,
                revenue=dict(INTEGRATED=4000, MODULAR=3800),
                commissioning_risk=dict(
                    EARLY=0.45, EARLY_WITH_PREPARATION=0.25, PILOT=0.05, PILOT_WITH_PREPARATION=0.03
                ),
                expansion_risk=dict(BASE=0.35, PREPARED=0.08),
                **rule_sets[version],
            )
            with zipfile.ZipFile(output, "w", zipfile.ZIP_DEFLATED) as archive:
                archive.writestr(
                    "metadata.json", json.dumps(metadata, ensure_ascii=False, indent=2)
                )
                archive.writestr(
                    "journal.jsonl", "\n".join(json.dumps(e, ensure_ascii=False) for e in events)
                )
                archive.writestr("transactions.csv", csv_text(self.state["ledger"]))
                actors = [
                    dict(
                        session_id=self.state["session_id"],
                        ecosystem_id=t,
                        org_id=self.org(t, r),
                        role=r,
                        kind="PARTICIPANT_COMPANY",
                        initial_cash=INITIAL,
                        participant_ids=[
                            hashlib.sha256(
                                (self.state["session_id"] + p["id"]).encode()
                            ).hexdigest()[:12]
                            for p in self.seat_of(t, r)
                        ],
                        automated=self.is_bot(t, r),
                    )
                    for t in self.active_teams()
                    for r in R.ROLES
                ]
                providers = {
                    (e["ecosystem_id"], e["data"]["proposal"]["excluded"])
                    for e in events
                    if e["event_type"] == "proposal_published" and e["data"]["proposal"]["excluded"]
                }
                actors.extend(
                    dict(
                        session_id=self.state["session_id"],
                        ecosystem_id=t,
                        org_id=self.org(t, "ALT_" + r),
                        role="ALT",
                        provider_for=r,
                        kind="EXTERNAL_SUPPLIER",
                        initial_cash=0,
                        participant_ids=[],
                        automated=True,
                    )
                    for t, r in sorted(providers)
                )
                archive.writestr("acteurs.csv", csv_text(actors))
                decisions, contracts, draws, states = [], [], [], []
                for event in events:
                    data = event["data"]
                    core = {
                        k: event[k]
                        for k in (
                            "event_id",
                            "session_id",
                            "sequence",
                            "economic_date",
                            "ecosystem_id",
                            "org_id",
                            "node_id",
                            "visit_id",
                            "decision_id",
                            "event_type",
                        )
                    }
                    if event["event_type"] in (
                        "profile_selected",
                        "consent_submitted",
                        "partner_left",
                        "return_requested",
                        "renegotiation_requested",
                        "capacity_withdrawn",
                    ):
                        info = data.get("information", {})
                        decisions.append(
                            dict(
                                core,
                                choice=data.get("choice", event["event_type"]),
                                revision=data.get("revision"),
                                cash_available=info.get("cash"),
                                outside_income=info.get("outside"),
                                operating_cost=info.get("operating_cost"),
                                private_shock=info.get("private_shock"),
                                revenue_adjustment=info.get("revenue_adjustment"),
                                private_offer=info.get("offer"),
                                available_options=info.get("available", data.get("options")),
                                information=info,
                            )
                        )
                    if event["event_type"] in (
                        "proposal_published",
                        "contract_committed",
                        "proposal_expired",
                    ):
                        proposal = data["proposal"]
                        for role, amount in allocations(proposal).items():
                            identity = "ALT_" + proposal["excluded"] if role == "ALT" else role
                            contracts.append(
                                dict(
                                    core,
                                    org_id=self.org(event["ecosystem_id"], identity),
                                    role=role,
                                    revision=proposal["revision"],
                                    kind=proposal["kind"],
                                    status=proposal["status"],
                                    revenue_credits=amount / 100,
                                    funding=proposal["funding"].get(role, 0),
                                    funding_credits=proposal["funding"].get(role, 0) / 100,
                                    architecture=proposal["architecture"],
                                    launch=proposal["launch"],
                                    response=proposal.get("votes", {}).get(role),
                                )
                            )
                    if event["event_type"] in ("event_drawn", "risk_drawn"):
                        draws.append(dict(core, **data))
                    if "state_after" in event:
                        snapshot = dict(event["state_after"])
                        cash = snapshot.pop("cash")
                        states.append(
                            dict(core, **snapshot, **{"cash_" + r: cash[r] for r in R.ROLES})
                        )
                archive.writestr("decisions.csv", csv_text(decisions))
                archive.writestr("contrats.csv", csv_text(contracts))
                archive.writestr("tirages.csv", csv_text(draws))
                archive.writestr("etats.csv", csv_text(states))
            return output.getvalue()
