# -*- coding: utf-8 -*-
"""Machine a etats et calcul des scores du jeu ECOSYSTEM."""

import secrets
import time
import threading

from . import rules as R


class GameError(Exception):
    """Erreur de regle renvoyee telle quelle au client."""


# ---------------------------------------------------------------------------
# Construction de l'etat
# ---------------------------------------------------------------------------


def _empty_round(n):
    rd = {
        "decisions": {},  # role -> "JOIN" / "OUT"
        "locked": False,
        "result": None,
        "revision": 0,
        "signals": {},  # intentions publiques, jamais des votes
        "history": [],  # versions successives du contrat du round
    }
    if n == 1:
        rd["contract"] = dict(R.R1_REVENUE)
    if n == 2:
        rd["contract"] = None
    if n == 3:
        rd["architecture"] = None
        rd["standard"] = {}
        rd["resolution"] = None
        rd["contract"] = None
        rd["integration"] = {}
        rd["shock"] = None
    return rd


def _empty_team():
    return {
        "claims": {},  # role -> {"amount": int|None, "text": str}
        "rounds": {"1": _empty_round(1), "2": _empty_round(2), "3": _empty_round(3)},
        # registre d'ajustements : les pouvoirs et le marche ecrivent ici, ce
        # qui laisse score_simple() et score_round3() totalement inchangees
        "adjust": {r: 0 for r in R.ROLES},
        "eco_adjust": 0,
        "powers": {},  # role -> {"used": bool, "detail": str, "t": float}
        "veto": False,  # FLEET a interdit PROPRIETARY
        "exclusive": False,  # BRAIN s'est engage : plus d'offre acceptable
        "pending_exclusive": False,
        "lost_brain": False,  # BRAIN parti au marche
    }


def new_state(code=None, team_count=2):
    return {
        "code": code or _code(),
        "host_key": secrets.token_urlsafe(9),
        "created": time.time(),
        "version": 1,
        "phase": "LOBBY",
        "team_count": team_count,
        "auto_teams": True,
        "players": {},
        "teams": {t: _empty_team() for t in R.TEAMS[:team_count]},
        "timer": {"running": False, "ends_at": None, "remaining": None, "duration": None},
        "market": _empty_market(),
        "shock": None,  # tire au sort pour toute la classe
        "log": [],
    }


def _empty_market():
    return {
        "offers": {},  # equipe offrante -> {equipe ciblee: points}
        "decisions": {},  # equipe du BRAIN -> "STAY" | equipe de destination
        "resolved": False,
        "moves": [],  # [{"brain": nom, "from": T, "to": T, "price": int}]
        "voided": [],  # acceptations annulees faute de place
    }


def _code():
    alphabet = "ABCDEFGHJKLMNPQRSTUVWXYZ"
    return "".join(secrets.choice(alphabet) for _ in range(4))


# ---------------------------------------------------------------------------
# Le jeu
# ---------------------------------------------------------------------------


def migrate(state):
    """Complete un etat sauvegarde avec les champs ajoutes depuis.

    Une partie enregistree avant le marche, les pouvoirs et les trois chocs
    doit pouvoir etre rechargee sans perdre les scores deja acquis.
    """
    ref = new_state()
    for key in ("market", "shock"):
        state.setdefault(key, ref[key])
    for p in state.get("players", {}).values():
        p.setdefault("first_name", "")
        p.setdefault("last_name", "")
        p.setdefault("identity_required", not (p["first_name"] and p["last_name"]))
    empty = _empty_team()
    for team in state.get("teams", {}).values():
        for key, val in empty.items():
            if key == "rounds":
                continue
            team.setdefault(key, val if not isinstance(val, dict) else dict(val))
        for r in R.ROLES:
            team["adjust"].setdefault(r, 0)
        team["rounds"].get("3", {}).setdefault("shock", None)
        for rd in team["rounds"].values():
            rd.setdefault("revision", 0)
            rd.setdefault("signals", {})
            rd.setdefault("history", [])
    return state


class Game:
    def __init__(self, state=None, on_change=None):
        self.state = migrate(state) if state else new_state()
        self.lock = threading.RLock()
        self.cond = threading.Condition(self.lock)
        self._on_change = on_change

    # -- infrastructure -----------------------------------------------------

    def touch(self, message=None):
        """Incremente la version et reveille les clients en long-poll."""
        self.state["version"] += 1
        if message:
            self.state["log"].append({"t": time.time(), "m": message})
            self.state["log"] = self.state["log"][-200:]
        self.cond.notify_all()
        if self._on_change:
            self._on_change(self.state)

    def wait_for_change(self, since, timeout=25.0):
        with self.cond:
            deadline = time.time() + timeout
            while self.state["version"] <= since:
                left = deadline - time.time()
                if left <= 0:
                    break
                self.cond.wait(left)
            return self.state["version"]

    # -- joueurs ------------------------------------------------------------

    def active_teams(self):
        return R.TEAMS[: self.state["team_count"]]

    def seat_of(self, team, role):
        return [
            p for p in self.state["players"].values() if p["team"] == team and p["role"] == role
        ]

    def seat_map(self):
        """(team, role) -> liste de joueurs."""
        m = {(t, r): [] for t in self.active_teams() for r in R.ROLES}
        for p in self.state["players"].values():
            m.setdefault((p["team"], p["role"]), []).append(p)
        return m

    def is_bot(self, team, role):
        return not self.seat_of(team, role)

    def _pick_seat(self):
        """Equilibre les equipes, en remplissant les roles par ordre de priorite."""
        teams = self.active_teams()
        seats = self.seat_map()
        counts = {t: sum(len(seats[(t, r)]) for r in R.ROLES) for t in teams}

        # 1. un siege totalement vide, dans l'equipe la moins peuplee
        best = None
        for t in sorted(teams, key=lambda x: (counts[x], teams.index(x))):
            for role in R.ROLE_PRIORITY:
                if not seats[(t, role)]:
                    best = (t, role)
                    break
            if best:
                break
        if best:
            return best

        # 2. tout est occupe : on ajoute un co-equipier sur le siege le moins charge
        cand = min(
            ((t, r) for t in teams for r in R.ROLES),
            key=lambda k: (len(seats[k]), R.ROLE_PRIORITY.index(k[1])),
        )
        return cand

    def join(self, name=None, code=None, *, first_name=None, last_name=None):
        with self.lock:
            structured = first_name is not None or last_name is not None
            if structured:
                first_name, last_name = self._identity(first_name, last_name)
                name = first_name + " " + last_name
            else:
                name = (name or "").strip()[:24]
                if not name:
                    raise GameError("Indiquez votre prenom et votre nom.")
            # le code protege la partie quand l'adresse est publique (tunnel)
            if (code or "").strip().upper() != self.state["code"]:
                raise GameError("Code de partie incorrect.")
            if self.state["phase"] not in ("LOBBY", "R1_NEGO"):
                raise GameError("La partie a deja commence. Demandez a l'enseignant.")
            self._autoscale_teams(extra=1)
            team, role = self._pick_seat()
            token = secrets.token_urlsafe(12)
            self.state["players"][token] = {
                "id": token,
                "name": name,
                "team": team,
                "role": role,
                "first_name": first_name or "",
                "last_name": last_name or "",
                "identity_required": not structured,
                "joined": time.time(),
                "seen": time.time(),
            }
            self._rebalance()
            p = self.state["players"][token]
            self.touch("%s rejoint %s / %s" % (name, p["team"], p["role"]))
            return token

    @staticmethod
    def _identity(first_name, last_name):
        fields = []
        for value, label in ((first_name, "prenom"), (last_name, "nom")):
            if not isinstance(value, str) or not value.strip():
                raise GameError("Indiquez votre %s." % label)
            value = " ".join(value.split())
            if len(value) > 40:
                raise GameError("Le %s est limite a 40 caracteres." % label)
            fields.append(value)
        return fields

    def request_identity(self):
        with self.lock:
            for p in self.state["players"].values():
                p["identity_required"] = True
            self.touch("L'enseignant demande le prenom et le nom de chaque etudiant")

    def set_identity(self, token, first_name, last_name):
        with self.lock:
            p = self._player(token)
            first_name, last_name = self._identity(first_name, last_name)
            p.update(
                first_name=first_name,
                last_name=last_name,
                name=first_name + " " + last_name,
                identity_required=False,
            )
            self.touch("Identite renseignee : %s" % p["name"])

    def _autoscale_teams(self, extra=0):
        """Ouvre un ecosysteme de plus des que l'effectif permet de le remplir.

        On divise par defaut (et non par exces) : mieux vaut trois equipes
        completes et quelques binomes que quatre equipes trouees de sieges
        vacants, qu'aucun etudiant ne defendra pendant la negociation.
        """
        if not self.state["auto_teams"]:
            return
        n = len(self.state["players"]) + extra
        want = max(2, min(len(R.TEAMS), n // 5))
        if want > self.state["team_count"]:
            self.set_team_count(want, _internal=True)

    def set_team_count(self, n, _internal=False):
        n = max(2, min(len(R.TEAMS), int(n)))
        if n == self.state["team_count"]:
            return
        self.state["team_count"] = n
        if not _internal:
            self.state["auto_teams"] = False
        keep = R.TEAMS[:n]
        for t in keep:
            self.state["teams"].setdefault(t, _empty_team())
        for t in list(self.state["teams"]):
            if t not in keep:
                del self.state["teams"][t]
        # les joueurs des equipes supprimees, puis les binomes, sont replaces
        for p in self.state["players"].values():
            if p["team"] not in keep:
                p["team"], p["role"] = self._pick_seat()
        self._rebalance()
        if not _internal:
            self.touch("Nombre d'ecosystemes : %d" % n)

    def _rebalance(self):
        """Deplace les joueurs en binome vers les sieges restes vacants."""
        teams = self.active_teams()
        seats = {(t, r): [] for t in teams for r in R.ROLES}
        for p in self.state["players"].values():
            if (p["team"], p["role"]) in seats:
                seats[(p["team"], p["role"])].append(p)

        for _ in range(len(self.state["players"])):
            empty = [k for k, v in seats.items() if not v]
            crowded = [k for k, v in seats.items() if len(v) > 1]
            if not empty or not crowded:
                return
            counts = {t: sum(len(seats[(t, r)]) for r in R.ROLES) for t in teams}
            crowded.sort(key=lambda k: -len(seats[k]))
            empty.sort(key=lambda k: (counts[k[0]], R.ROLE_PRIORITY.index(k[1])))
            src, dst = crowded[0], empty[0]
            p = seats[src].pop()
            p["team"], p["role"] = dst
            seats[dst].append(p)

    def reassign(self, token, team, role):
        with self.lock:
            p = self.state["players"].get(token)
            if not p:
                raise GameError("Joueur inconnu.")
            if team not in self.active_teams() or role not in R.ROLES:
                raise GameError("Position invalide.")
            p["team"], p["role"] = team, role
            self.touch("%s -> %s / %s" % (p["name"], team, role))

    def remove_player(self, token):
        with self.lock:
            p = self.state["players"].pop(token, None)
            if p:
                if not self.seat_of(p["team"], p["role"]):
                    team = self.state["teams"][p["team"]]
                    team["claims"].pop(p["role"], None)
                    for rd in team["rounds"].values():
                        if not rd["locked"]:
                            rd["decisions"].pop(p["role"], None)
                            rd["signals"].pop(p["role"], None)
                self.touch("%s a ete retire" % p["name"])

    def shuffle(self):
        """Redistribue tous les joueurs (equipes equilibrees)."""
        with self.lock:
            players = list(self.state["players"].values())
            secrets.SystemRandom().shuffle(players)
            for p in players:
                p["team"] = None
                p["role"] = None
            self.state["players"] = {}
            for p in players:
                p["team"], p["role"] = self._pick_seat()
                self.state["players"][p["id"]] = p
            self.touch("Roles redistribues")

    # -- phases -------------------------------------------------------------

    def set_phase(self, phase):
        with self.lock:
            if phase not in R.PHASE_KEYS:
                raise GameError("Phase inconnue.")
            prev = self.state["phase"]
            # on ne verrouille qu'en avancant : revenir en arriere permet de rejouer
            forward = R.PHASE_KEYS.index(phase) > R.PHASE_KEYS.index(prev)
            if prev in R.DECISION_PHASES and forward:
                self._resolve(R.DECISION_PHASES[prev])
            if prev == "MARKET" and forward:
                self._resolve_market()
            if phase == "R3_SHOCK":
                self._draw_shock()
            self.state["phase"] = phase
            d = R.PHASE_DURATION[phase]
            self.state["timer"] = {
                "running": False,
                "ends_at": None,
                "remaining": d,
                "duration": d,
            }
            self.touch("Phase : %s" % R.PHASE_LABEL[phase])

    def step(self, delta):
        with self.lock:
            i = R.PHASE_KEYS.index(self.state["phase"]) + delta
            i = max(0, min(len(R.PHASE_KEYS) - 1, i))
            self.set_phase(R.PHASE_KEYS[i])

    def unlock_round(self, n):
        """Deverrouille un round pour le rejouer (efface les decisions)."""
        with self.lock:
            n = str(n)
            if n not in ("1", "2", "3"):
                raise GameError("Round inconnu.")
            for team in self.active_teams():
                rd = self.state["teams"][team]["rounds"][n]
                keep_arch = rd.get("architecture")
                keep_std = rd.get("standard")
                self.state["teams"][team]["rounds"][n] = _empty_round(int(n))
                if n == "3":
                    self.state["teams"][team]["rounds"][n]["architecture"] = keep_arch
                    self.state["teams"][team]["rounds"][n]["standard"] = keep_std or {}
                    # le choc reste celui deja tire : on rejoue la reponse, pas le sort
                    self.state["teams"][team]["rounds"][n]["shock"] = self.state.get("shock")
            self.touch("Round %s reouvert" % n)

    # -- chrono -------------------------------------------------------------

    def timer_start(self):
        with self.lock:
            t = self.state["timer"]
            if t["remaining"] is None:
                t["remaining"] = 300
                t["duration"] = 300
            t["ends_at"] = time.time() + t["remaining"]
            t["running"] = True
            self.touch()

    def timer_pause(self):
        with self.lock:
            t = self.state["timer"]
            if t["running"] and t["ends_at"]:
                t["remaining"] = max(0, int(round(t["ends_at"] - time.time())))
            t["running"] = False
            t["ends_at"] = None
            self.touch()

    def timer_reset(self):
        with self.lock:
            d = R.PHASE_DURATION[self.state["phase"]] or 300
            self.state["timer"] = {"running": False, "ends_at": None, "remaining": d, "duration": d}
            self.touch()

    def timer_add(self, seconds):
        with self.lock:
            t = self.state["timer"]
            if t["running"] and t["ends_at"]:
                t["ends_at"] += seconds
                t["remaining"] = max(0, int(round(t["ends_at"] - time.time())))
            else:
                t["remaining"] = max(0, (t["remaining"] or 0) + seconds)
            t["duration"] = max(t["duration"] or 0, t["remaining"] or 0)
            self.touch()

    # -- actions joueurs ----------------------------------------------------

    def _player(self, token):
        p = self.state["players"].get(token)
        if not p:
            raise GameError("Session expiree. Rejoignez la partie a nouveau.")
        p["seen"] = time.time()
        return p

    def _round_for_phase(self):
        ph = self.state["phase"]
        if ph.startswith("R1"):
            return 1
        if ph.startswith("R2"):
            return 2
        if ph.startswith("R3"):
            return 3
        return None

    def decide(self, token, choice):
        with self.lock:
            p = self._player(token)
            n = R.DECISION_PHASES.get(self.state["phase"])
            if not n:
                raise GameError("Ce n'est pas le moment de decider.")
            if choice not in ("JOIN", "OUT"):
                raise GameError("Choix invalide.")
            rd = self.state["teams"][p["team"]]["rounds"][str(n)]
            if rd["locked"]:
                raise GameError("Les decisions sont verrouillees.")
            if n == 3 and rd["resolution"] == "ABANDON":
                raise GameError("Votre ecosysteme a abandonne le projet.")
            if n == 3 and rd["resolution"] == "REPLACE":
                sp = shock_spec(rd.get("shock") or self.state.get("shock"))
                if p["role"] == sp["target"]:
                    raise GameError("Votre ecosysteme vous a remplace par %s." % sp["alt_label"])
            rd["decisions"][p["role"]] = choice
            self.touch()

    def set_claim(self, token, amount, text):
        with self.lock:
            p = self._player(token)
            if self.state["phase"] not in ("R1_NEGO", "R2_NEGO", "R3_NEGO"):
                raise GameError("Les demandes sont ouvertes pendant la negociation.")
            claims = self.state["teams"][p["team"]]["claims"]
            try:
                amount = None if amount in (None, "") else max(0, min(46, int(amount)))
            except (TypeError, ValueError):
                amount = None
            claims[p["role"]] = {
                "amount": amount,
                "text": (text or "").strip()[:80],
                "t": time.time(),
            }
            self.touch()

    def signal(self, token, stance, revision):
        """Intention non contraignante, visible uniquement dans son equipe."""
        with self.lock:
            p = self._player(token)
            if self.state["phase"] not in ("R1_NEGO", "R2_NEGO", "R3_NEGO"):
                raise GameError("Les intentions sont ouvertes pendant la negociation.")
            if stance not in ("READY", "DISCUSS", "CLEAR"):
                raise GameError("Intention invalide.")
            n = self._round_for_phase()
            rd = self.state["teams"][p["team"]]["rounds"][str(n)]
            if rd["locked"] or not rd.get("contract"):
                raise GameError("Attendez la publication d'un contrat.")
            if revision != rd["revision"]:
                raise GameError("Le contrat a change. Relisez la nouvelle version.")
            if n == 3 and rd["resolution"] == "REPLACE":
                if p["role"] == shock_spec(rd.get("shock"))["target"]:
                    raise GameError("Vous avez ete remplace dans ce contrat.")
            if stance == "CLEAR":
                rd["signals"].pop(p["role"], None)
            else:
                rd["signals"][p["role"]] = stance
            self.touch()

    def _record_contract(self, rd):
        rd["revision"] += 1
        rd["signals"] = {}
        rd["decisions"] = {}
        rd["history"].append(
            {
                "revision": rd["revision"],
                "contract": dict(rd.get("contract") or {}),
                "resolution": rd.get("resolution"),
                "integration": dict(rd.get("integration") or {}),
                "t": time.time(),
            }
        )
        rd["history"] = rd["history"][-20:]

    def _require_mobi(self, token):
        p = self._player(token)
        if p["role"] != "MOBI":
            raise GameError("Seul MOBI depose les accords de l'ecosysteme.")
        return p

    def submit_contract(self, token, revenues):
        """Round 2 : repartition libre des 40 points."""
        with self.lock:
            p = self._require_mobi(token)
            if self.state["phase"] not in ("R2_NEGO", "R2_DECIDE"):
                raise GameError("Le contrat se depose pendant le round 2.")
            rd = self.state["teams"][p["team"]]["rounds"]["2"]
            if rd["locked"]:
                raise GameError("Le contrat est verrouille.")
            if self.state["phase"] == "R2_DECIDE" and rd["contract"]:
                raise GameError("Le contrat ne peut plus etre modifie apres revelation.")
            vals = _ints(revenues, R.ROLES)
            total = sum(vals.values())
            if total != R.V_BASE:
                raise GameError(
                    "La somme doit faire exactement %d points (actuellement %d)."
                    % (R.V_BASE, total)
                )
            rd["contract"] = vals
            self._record_contract(rd)
            self.touch("Contrat R2 depose par %s" % p["team"])

    def submit_architecture(self, token, arch, contributions):
        with self.lock:
            p = self._require_mobi(token)
            if self.state["phase"] != "R3_ARCH":
                raise GameError("Le choix d'architecture n'est pas ouvert.")
            if arch not in ("PROPRIETARY", "MODULAR"):
                raise GameError("Architecture invalide.")
            if arch == "PROPRIETARY" and self.state["teams"][p["team"]]["veto"]:
                raise GameError("FLEET a pose son veto : PROPRIETARY est interdit.")
            rd = self.state["teams"][p["team"]]["rounds"]["3"]
            if arch == "MODULAR":
                vals = _ints(contributions, R.ROLES)
                total = sum(vals.values())
                if total != R.STANDARD_COST:
                    raise GameError(
                        "Les contributions doivent totaliser %d points "
                        "(actuellement %d)." % (R.STANDARD_COST, total)
                    )
            else:
                vals = {r: 0 for r in R.ROLES}
            rd["architecture"] = arch
            rd["standard"] = vals
            self.touch("%s choisit %s" % (p["team"], arch))

    def submit_resolution(self, token, resolution, revenues, integration):
        with self.lock:
            p = self._require_mobi(token)
            if self.state["phase"] not in ("R3_NEGO", "R3_DECIDE"):
                raise GameError("La renegociation n'est pas ouverte.")
            rd = self.state["teams"][p["team"]]["rounds"]["3"]
            if rd["locked"]:
                raise GameError("Les decisions sont verrouillees.")
            if self.state["phase"] == "R3_DECIDE" and rd["resolution"]:
                raise GameError("Le contrat ne peut plus etre modifie pendant le vote.")
            if not rd["architecture"]:
                raise GameError("Choisissez d'abord une architecture.")
            shock = rd.get("shock") or self.state.get("shock")
            sp = shock_spec(shock)
            if resolution not in sp["options"]:
                raise GameError("Solution impossible face a %s." % sp["label"])
            arch = rd["architecture"]
            team = self.state["teams"][p["team"]]
            # STANDARD READY : GRID a prepare l'infrastructure aux normes
            discount = R.POWERS["GRID"]["max"] if team["powers"].get("GRID", {}).get("used") else 0

            if resolution == "ABANDON":
                rd["resolution"] = "ABANDON"
                rd["contract"] = None
                rd["integration"] = {r: 0 for r in R.ROLES}
                rd["decisions"] = {}
                self._record_contract(rd)
                self.touch("%s abandonne le projet" % p["team"])
                return

            value = round3_value(arch, resolution, shock)
            need = adaptation_cost(arch, shock, resolution, discount)
            payers = [r for r in R.ROLES if r != sp["target"]]
            if resolution == "REPLACE":
                keys = payers + ["ALT_AI"]
            else:
                keys = list(R.ROLES)
            integ = _ints(integration, payers) if need else {r: 0 for r in payers}
            for r in R.ROLES:
                integ.setdefault(r, 0)
            if sum(integ.values()) != need:
                raise GameError(
                    "Le cout d'adaptation de %d points doit etre "
                    "reparti integralement (actuellement %d)." % (need, sum(integ.values()))
                )

            vals = _ints(revenues, keys)
            if sum(vals.values()) != value:
                raise GameError(
                    "La somme des revenus doit faire %d points "
                    "(actuellement %d)." % (value, sum(vals.values()))
                )
            if resolution == "REPLACE" and vals["ALT_AI"] < R.ALT_AI_MIN_REVENUE:
                raise GameError(
                    "ALT-AI refuse la position en dessous de %d points." % R.ALT_AI_MIN_REVENUE
                )

            rd["resolution"] = resolution
            rd["contract"] = vals
            rd["integration"] = integ
            rd["adapt_cost"] = need
            rd["shock"] = shock
            self._record_contract(rd)
            if resolution == "REPLACE":
                rd["decisions"].pop(sp["target"], None)
            self.touch("%s : %s" % (p["team"], resolution))

    # -- marche des ecosystemes --------------------------------------------

    def _require_brain(self, token):
        p = self._player(token)
        if p["role"] != "BRAIN":
            raise GameError("Seul BRAIN peut changer d'ecosysteme.")
        return p

    def make_offer(self, token, target_team, points):
        """MOBI propose des points au BRAIN d'un autre ecosysteme."""
        with self.lock:
            p = self._require_mobi(token)
            if self.state["phase"] != "MARKET":
                raise GameError("Le marche n'est pas ouvert.")
            if self.state["market"]["resolved"]:
                raise GameError("Le marche est clos.")
            if target_team == p["team"]:
                raise GameError("Vous ne pouvez pas recruter votre propre BRAIN.")
            if target_team not in self.active_teams():
                raise GameError("Ecosysteme inconnu.")
            try:
                points = int(points)
            except (TypeError, ValueError):
                raise GameError("Offre invalide.") from None
            if points < 0 or points > R.OFFER_MAX:
                raise GameError("Une offre va de 0 a %d points." % R.OFFER_MAX)
            offers = self.state["market"]["offers"].setdefault(p["team"], {})
            if points == 0:
                offers.pop(target_team, None)
            else:
                offers[target_team] = points
            self.touch("%s fait une offre au BRAIN de %s" % (p["team"], target_team))

    def market_decide(self, token, choice):
        """BRAIN choisit secretement : STAY ou le code d'un ecosysteme offrant."""
        with self.lock:
            p = self._require_brain(token)
            if self.state["phase"] != "MARKET":
                raise GameError("Le marche n'est pas ouvert.")
            mk = self.state["market"]
            if mk["resolved"]:
                raise GameError("Le marche est clos.")
            team = self.state["teams"][p["team"]]
            if choice != "STAY" and team["exclusive"]:
                raise GameError("Vous vous etes engage a l'exclusivite.")
            if choice != "STAY":
                if choice not in mk["offers"] or p["team"] not in mk["offers"][choice]:
                    raise GameError("Cet ecosysteme ne vous a pas fait d'offre.")
            mk["decisions"][p["team"]] = choice
            self.touch()

    def _resolve_market(self):
        """Applique les mouvements de BRAIN.

        Un ecosysteme ne peut heberger qu'un seul BRAIN : un depart n'est donc
        valide que si le siege vise est lui-meme libere. On ne conserve que les
        cycles de la permutation demandee ; les autres acceptations sont
        annulees et l'ecosysteme concerne garde son BRAIN. C'est ce qui evite
        qu'un seul joueur puisse detruire un ecosysteme entier en partant, sans
        rien enlever a la credibilite de sa menace pendant la negociation.
        """
        mk = self.state["market"]
        if mk["resolved"]:
            return
        teams = self.active_teams()
        dest = {t: mk["decisions"].get(t, "STAY") for t in teams}
        dest = {t: (d if d in teams and d != t else t) for t, d in dest.items()}
        asked = [t for t, d in dest.items() if d != t]

        # on retire iterativement les departs impossibles jusqu'a n'avoir que
        # des cycles (une permutation) :
        #  - deux BRAIN ne peuvent viser le meme siege : on garde celui que
        #    l'ecosysteme d'accueil a paye le plus cher, les autres restent ;
        #  - un depart n'est valide que si le siege vise est lui-meme libere.
        while True:
            incoming = {}
            for t, d in dest.items():
                if d != t:
                    incoming.setdefault(d, []).append(t)
            bad = []
            for d, srcs in incoming.items():
                if len(srcs) > 1:
                    best = max(
                        srcs, key=lambda t: (mk["offers"].get(d, {}).get(t, 0), -teams.index(t))
                    )
                    bad += [t for t in srcs if t != best]
            bad += [t for t, d in dest.items() if d != t and dest.get(d) == d]
            if not bad:
                break
            for t in bad:
                dest[t] = t

        mk["voided"] = sorted(t for t in asked if dest[t] == t)
        moves = []
        brains = {t: (self.seat_of(t, "BRAIN") or [None])[0] for t in teams}
        for src in sorted(dest):
            dst = dest[src]
            if dst == src:
                continue
            price = mk["offers"].get(dst, {}).get(src, 0)
            brain = brains[src]
            if brain is not None:
                brain.setdefault("origin_team", src)
                brain["team"] = dst
            self.state["teams"][src]["lost_brain"] = True
            # BRAIN encaisse l'offre et paie son changement ; le MOBI d'accueil
            # finance l'offre sur sa propre part
            adj = self.state["teams"][dst]["adjust"]
            adj["BRAIN"] = adj.get("BRAIN", 0) + price - R.SWITCH_COST
            adj["MOBI"] = adj.get("MOBI", 0) - price
            moves.append(
                {
                    "brain": brain["name"] if brain else "BRAIN (bot)",
                    "from": src,
                    "to": dst,
                    "price": price,
                }
            )
        mk["moves"] = moves
        mk["resolved"] = True
        if moves:
            self.touch(
                "Marche : "
                + ", ".join("%s -> %s (%d pts)" % (m["from"], m["to"], m["price"]) for m in moves)
            )
        else:
            self.touch("Marche : aucun transfert")

    # -- pouvoirs de role ---------------------------------------------------

    def power_available(self, team, role):
        """(possible, raison) : le pouvoir peut-il etre active maintenant ?"""
        spec = R.POWERS[role]
        t = self.state["teams"][team]
        if t["powers"].get(role, {}).get("used"):
            return False, "POUVOIR UTILISE"
        if self.state["phase"] not in spec["phases"]:
            return False, "Pas utilisable dans cette phase."
        if role == "BRAIN" and (t["exclusive"] or t["pending_exclusive"]):
            return False, "Proposition deja envoyee."
        if role == "GRID":
            if t["rounds"]["3"].get("architecture") != "MODULAR":
                return False, "Reserve aux ecosystemes MODULAR."
            if t["rounds"]["3"].get("resolution"):
                return False, "La solution est deja deposee."
        if role == "FLEET" and t["rounds"]["3"].get("architecture"):
            return False, "L'architecture est deja deposee."
        return True, ""

    def use_power(self, token, target=None, amount=None):
        with self.lock:
            p = self._player(token)
            role, team = p["role"], p["team"]
            ok, why = self.power_available(team, role)
            if not ok:
                raise GameError(
                    "Votre pouvoir a deja ete utilise." if why == "POUVOIR UTILISE" else why
                )
            t = self.state["teams"][team]
            spec = R.POWERS[role]

            if role == "MOBI":
                if target not in R.ROLES or target == "MOBI":
                    raise GameError("Choisissez un partenaire.")
                try:
                    amount = int(amount)
                except (TypeError, ValueError):
                    raise GameError("Montant invalide.") from None
                if not 1 <= amount <= spec["max"]:
                    raise GameError("De 1 a %d points." % spec["max"])
                t["adjust"]["MOBI"] -= amount
                t["adjust"][target] += amount
                detail = "%d pts vers %s" % (amount, target)

            elif role == "BRAIN":
                # simple proposition : MOBI doit l'accepter pour qu'elle compte
                t["pending_exclusive"] = True
                self.touch("%s : BRAIN propose l'exclusivite" % team)
                return

            elif role == "AUTO":
                t["adjust"]["AUTO"] += spec["max"]
                t["eco_adjust"] -= spec["max"]
                detail = "+%d pts, -%d de valeur collective" % (spec["max"], spec["max"])

            elif role == "GRID":
                detail = "cout d'adaptation reduit de %d" % spec["max"]

            else:  # FLEET
                t["veto"] = True
                detail = "PROPRIETARY interdit"

            t["powers"][role] = {"used": True, "detail": detail, "t": time.time()}
            self.touch("%s : pouvoir %s active (%s)" % (team, spec["name"], role))

    def respond_exclusivity(self, token, accept):
        """MOBI accepte ou refuse la proposition d'exclusivite de BRAIN."""
        with self.lock:
            p = self._require_mobi(token)
            t = self.state["teams"][p["team"]]
            if not t["pending_exclusive"]:
                raise GameError("Aucune proposition en attente.")
            t["pending_exclusive"] = False
            if not accept:
                # pouvoir non consomme : BRAIN pourra reproposer
                self.touch("%s : MOBI refuse l'exclusivite" % p["team"])
                return
            bonus = R.POWERS["BRAIN"]["max"]
            t["adjust"]["BRAIN"] += bonus
            t["adjust"]["MOBI"] -= bonus
            t["exclusive"] = True
            t["powers"]["BRAIN"] = {
                "used": True,
                "detail": "+%d pts contre exclusivite" % bonus,
                "t": time.time(),
            }
            self.state["market"]["decisions"][p["team"]] = "STAY"
            self.touch("%s : exclusivite accordee a BRAIN" % p["team"])

    # -- choc ---------------------------------------------------------------

    def _draw_shock(self):
        """Tirage unique pour toute la classe, apres le choix d'architecture."""
        if self.state.get("shock"):
            return
        self.state["shock"] = secrets.choice(R.SHOCK_KEYS)
        for team in self.active_teams():
            self.state["teams"][team]["rounds"]["3"]["shock"] = self.state["shock"]
        self.touch("Choc tire : %s" % R.SHOCKS[self.state["shock"]]["label"])

    def force_shock(self, key):
        """L'enseignant peut imposer un choc (repetition, demonstration)."""
        with self.lock:
            if key not in R.SHOCK_KEYS:
                raise GameError("Choc inconnu.")
            self.state["shock"] = key
            for team in self.active_teams():
                self.state["teams"][team]["rounds"]["3"]["shock"] = key
            self.touch("Choc impose : %s" % R.SHOCKS[key]["label"])

    # -- resolution des rounds ---------------------------------------------

    def _resolve(self, n):
        for team in self.active_teams():
            rd = self.state["teams"][team]["rounds"][str(n)]
            if rd["locked"]:
                continue
            if n == 2 and not rd.get("contract"):
                # aucun contrat depose = aucun accord : personne n'investit
                rd["decisions"] = {r: "OUT" for r in R.ROLES}
                rd["result"] = score_simple(rd["decisions"], {})
                rd["result"]["no_contract"] = True
                rd["locked"] = True
                continue
            self._fill_bots(team, n, rd)
            if n == 3:
                rd["result"] = score_round3(rd)
            else:
                contract = rd.get("contract") or dict(R.R1_REVENUE)
                rd["result"] = score_simple(rd["decisions"], contract)
            rd["locked"] = True

    def _fill_bots(self, team, n, rd):
        """Les sieges sans etudiant sont joues rationnellement."""
        if n == 3 and rd.get("resolution") == "ABANDON":
            return
        roles = list(R.ROLES)
        if n == 3 and rd.get("resolution") == "REPLACE":
            sp = shock_spec(rd.get("shock"))
            roles = [r for r in R.ROLES if r != sp["target"]]
        for role in roles:
            if role in rd["decisions"]:
                continue
            if not self.is_bot(team, role):
                rd["decisions"][role] = "OUT"  # absence de reponse = pas d'investissement
                continue
            rev = (rd.get("contract") or {}).get(role, 0)
            cost = R.COST[role]
            if (
                n == 3
                and rd.get("resolution") == "KEEP"
                and role == "BRAIN"
                and (rd.get("shock") or "AI_FAILURE") == "AI_FAILURE"
            ):
                cost += R.BRAIN_ADAPTATION
            extra = (rd.get("integration") or {}).get(role, 0)
            rd["decisions"][role] = "JOIN" if (rev - cost - extra) >= R.OUTSIDE[role] else "OUT"

    # -- vues ---------------------------------------------------------------

    def totals(self):
        """Cumuls individuels et collectifs sur les trois rounds."""
        per_player = []
        eco = {}
        for team in self.active_teams():
            t = self.state["teams"][team]
            eco[team] = {"rounds": {}, "total": 0}
            for n in ("1", "2", "3"):
                res = t["rounds"][n]["result"]
                v = res["ecosystem"] if res else None
                eco[team]["rounds"][n] = v
                eco[team]["total"] += v or 0
            eco[team]["architecture"] = t["rounds"]["3"].get("architecture")
            eco[team]["resolution"] = t["rounds"]["3"].get("resolution")
            eco[team]["shock"] = t["rounds"]["3"].get("shock")
            # multi-homing d'AUTO : valeur captee hors de l'ecosysteme
            eco[team]["adjust"] = t.get("eco_adjust", 0)
            eco[team]["total"] += eco[team]["adjust"]
            eco[team]["badges"] = self.team_badges(team)
        badges_by_role = {t: {} for t in self.active_teams()}
        for t in self.active_teams():
            for key, roles in self.role_badges(t).items():
                for r in roles:
                    badges_by_role[t].setdefault(r, []).append(key)
        for p in self.state["players"].values():
            # un BRAIN transfere au marche garde les points gagnes chez lui
            home = p.get("origin_team") or p["team"]
            row = {
                "name": p["name"],
                "team": p["team"],
                "role": p["role"],
                "origin_team": p.get("origin_team"),
                "rounds": {},
                "total": 0,
            }
            for n in ("1", "2", "3"):
                src = home if n in ("1", "2") else p["team"]
                res = self.state["teams"][src]["rounds"][n]["result"]
                sc = res["scores"].get(p["role"]) if res else None
                row["rounds"][n] = sc
                row["total"] += sc or 0
            adj = self.state["teams"][p["team"]]["adjust"].get(p["role"], 0)
            row["adjust"] = adj
            row["total"] += adj
            row["badges"] = badges_by_role.get(p["team"], {}).get(p["role"], [])
            per_player.append(row)
        per_player.sort(key=lambda r: -r["total"])
        return per_player, eco

    # -- badges pedagogiques (aucun effet sur les scores) -------------------

    def team_badges(self, team):
        """Liste de badges [{key, icon, label, text}] pour un ecosysteme."""
        t = self.state["teams"][team]
        keys = []
        r2 = t["rounds"]["2"]
        contract2 = r2.get("contract") or {}
        if contract2.get("BRAIN", 0) >= R.V_BASE * R.HOLD_UP_SHARE:
            keys.append("HOLD_UP")
        for n in ("1", "2"):
            res = t["rounds"][n].get("result")
            if res and not res["success"] and not res.get("no_contract"):
                keys.append("FAILED_BARGAIN")
                break
        if t.get("lost_brain"):
            keys.append("POACHED")
        r3 = t["rounds"]["3"]
        res3 = r3.get("result")
        arch = r3.get("architecture")
        if res3 and res3["success"]:
            if arch == "MODULAR":
                keys.append("RESILIENT")
            elif arch == "PROPRIETARY" and _lock_in(r3):
                keys.append("LOCK_IN")
        return [
            {"key": k, "icon": R.BADGES[k][0], "label": R.BADGES[k][1], "text": R.BADGES[k][2]}
            for k in keys
        ]

    def role_badges(self, team):
        """Badge -> roles concernes, pour l'affichage individuel."""
        out = {}
        for b in self.team_badges(team):
            if b["key"] == "HOLD_UP":
                out[b["key"]] = ["BRAIN"]
            elif b["key"] == "POACHED":
                out[b["key"]] = [r for r in R.ROLES if r != "BRAIN"]
            else:
                out[b["key"]] = list(R.ROLES)
        return out

    def team_public(self, team, reveal):
        """Ce que les membres d'une equipe voient de leur ecosysteme."""
        t = self.state["teams"][team]
        seats = {}
        for role in R.ROLES:
            people = self.seat_of(team, role)
            seats[role] = {
                "names": [x["name"] for x in people],
                "bot": not people,
            }
        out = {
            "team": team,
            "seats": seats,
            "claims": t["claims"],
            "rounds": {},
            "adjust": t["adjust"],
            "eco_adjust": t["eco_adjust"],
            "powers": t["powers"],
            "veto": t["veto"],
            "exclusive": t["exclusive"],
            "pending_exclusive": t["pending_exclusive"],
            "lost_brain": t["lost_brain"],
            "badges": self.team_badges(team),
        }
        for n in ("1", "2", "3"):
            rd = t["rounds"][n]
            answered = [r for r in R.ROLES if r in rd["decisions"]]
            item = {
                "answered": len(answered),
                "answered_roles": answered,
                "locked": rd["locked"],
                "contract": rd.get("contract"),
                "result": rd["result"],
                "revision": rd["revision"],
                "signals": dict(rd["signals"]),
                "history": list(rd["history"]),
            }
            if n == "3":
                item["architecture"] = rd["architecture"]
                item["standard"] = rd["standard"]
                item["resolution"] = rd["resolution"]
                item["integration"] = rd["integration"]
                item["shock"] = rd.get("shock")
                item["adapt_cost"] = rd.get("adapt_cost")
            if rd["locked"] or reveal:
                item["decisions"] = rd["decisions"]
            out["rounds"][n] = item
        return out

    def player_view(self, token):
        with self.lock:
            p = self._player(token)
            reveal = self.state["phase"] in ("FINAL", "DEBRIEF")
            team = self.team_public(p["team"], reveal)
            n = self._round_for_phase()
            rd = self.state["teams"][p["team"]]["rounds"][str(n)] if n else None
            power_ok, power_why = self.power_available(p["team"], p["role"])
            phase_index = R.PHASE_KEYS.index(self.state["phase"])
            # La vue participant ne contient que les informations deja revelees.
            visible_round = (
                3
                if reveal or self.state["phase"].startswith("R3")
                else 2
                if self.state["phase"] == "MARKET"
                else n or 0
            )
            team["rounds"] = {
                key: value for key, value in team["rounds"].items() if int(key) <= visible_round
            }
            if not reveal:
                team["badges"] = []
            if "3" in team["rounds"]:
                third = team["rounds"]["3"]
                if phase_index < R.PHASE_KEYS.index("R3_SHOCK"):
                    third["shock"] = None
                if phase_index < R.PHASE_KEYS.index("R3_NEGO"):
                    for key in ("resolution", "contract", "adapt_cost", "result"):
                        third[key] = None
                    third.update(
                        integration={}, signals={}, history=[], answered=0, answered_roles=[]
                    )
                    third.pop("decisions", None)
            spec = R.POWERS[p["role"]]
            power_seen = phase_index >= min(R.PHASE_KEYS.index(ph) for ph in spec["phases"])
            power = None
            if power_seen:
                used = self.state["teams"][p["team"]]["powers"].get(p["role"], {})
                power = {
                    "name": spec["name"],
                    "text": spec["text"],
                    "used": bool(used.get("used")),
                    "detail": used.get("detail"),
                    "available": power_ok,
                    "why": power_why,
                }
            view = {
                "version": self.state["version"],
                "server_time": time.time(),
                "phase": self.state["phase"],
                "phase_label": R.PHASE_LABEL[self.state["phase"]],
                "timer": self.state["timer"],
                "me": {
                    "name": p["name"],
                    "team": p["team"],
                    "role": p["role"],
                    "first_name": p.get("first_name", ""),
                    "last_name": p.get("last_name", ""),
                    "identity_required": p.get("identity_required", False),
                    "cost": R.COST[p["role"]],
                    "outside": R.OUTSIDE[p["role"]],
                    "card": R.ROLE_CARDS[p["role"]],
                    "decision": rd["decisions"].get(p["role"]) if rd else None,
                    "power": power,
                },
                "team": team,
                "round": n,
                "players_count": len(self.state["players"]),
                "teams_list": self.active_teams(),
                "shock": self.state.get("shock")
                if self.state["phase"] not in ("LOBBY",)
                and R.PHASE_KEYS.index(self.state["phase"]) >= R.PHASE_KEYS.index("R3_SHOCK")
                else None,
                "shock_warning": R.SHOCK_WARNING if visible_round == 3 else None,
                "market": self._market_view(p)
                if phase_index >= R.PHASE_KEYS.index("MARKET")
                else None,
            }
            if self.state["phase"] in ("FINAL", "DEBRIEF"):
                players, eco = self.totals()
                view["totals"] = {"players": players, "eco": eco}
                view["my_total"] = next(
                    (
                        x
                        for x in players
                        if x["name"] == p["name"]
                        and x["team"] == p["team"]
                        and x["role"] == p["role"]
                    ),
                    None,
                )
            return view

    def _market_view(self, p):
        """Ce qu'un joueur a le droit de voir du marche.

        MOBI voit ses propres offres ; BRAIN voit celles qu'il a recues ; les
        decisions des autres restent secretes jusqu'a la resolution.
        """
        mk = self.state["market"]
        out = {
            "open": self.state["phase"] == "MARKET",
            "resolved": mk["resolved"],
            "switch_cost": R.SWITCH_COST,
            "offer_max": R.OFFER_MAX,
            "moves": mk["moves"] if mk["resolved"] else [],
            "sent": {},
            "received": {},
            "decision": None,
        }
        if p["role"] == "MOBI":
            out["sent"] = dict(mk["offers"].get(p["team"], {}))
            out["targets"] = [t for t in self.active_teams() if t != p["team"]]
        if p["role"] == "BRAIN":
            out["received"] = {
                src: v[p["team"]]
                for src, v in mk["offers"].items()
                if p["team"] in v and src != p["team"]
            }
            out["decision"] = mk["decisions"].get(p["team"])
            out["locked"] = self.state["teams"][p["team"]]["exclusive"]
        return out

    def host_view(self):
        with self.lock:
            players, eco = self.totals()
            teams = {}
            for t in self.active_teams():
                teams[t] = self.team_public(t, reveal=self.state["phase"] in ("FINAL", "DEBRIEF"))
                # Le projecteur montre la progression, pas les intentions de chacun.
                for rd in teams[t]["rounds"].values():
                    rd["ready_count"] = sum(v == "READY" for v in rd["signals"].values())
                    rd["discuss_count"] = sum(v == "DISCUSS" for v in rd["signals"].values())
                    del rd["signals"]
            return {
                "version": self.state["version"],
                "server_time": time.time(),
                "code": self.state["code"],
                "phase": self.state["phase"],
                "phase_label": R.PHASE_LABEL[self.state["phase"]],
                "phase_index": R.PHASE_KEYS.index(self.state["phase"]),
                "phases": [{"key": k, "label": R.PHASE_LABEL[k]} for k in R.PHASE_KEYS],
                "timer": self.state["timer"],
                "team_count": self.state["team_count"],
                "auto_teams": self.state["auto_teams"],
                "teams": teams,
                "players": [
                    {
                        "id": p["id"],
                        "name": p["name"],
                        "team": p["team"],
                        "first_name": p.get("first_name", ""),
                        "last_name": p.get("last_name", ""),
                        "identity_required": p.get("identity_required", False),
                        "role": p["role"],
                        "seen": p["seen"],
                    }
                    for p in sorted(
                        self.state["players"].values(),
                        key=lambda x: (x["team"], R.ROLES.index(x["role"])),
                    )
                ],
                "totals": {"players": players, "eco": eco},
                "shock": self.state.get("shock"),
                "shocks": [{"key": k, "label": R.SHOCKS[k]["label"]} for k in R.SHOCK_KEYS],
                "market": {
                    "resolved": self.state["market"]["resolved"],
                    "moves": self.state["market"]["moves"],
                    "voided": self.state["market"]["voided"],
                    # nombre d'offres seulement : le detail reste prive
                    "offer_count": sum(len(v) for v in self.state["market"]["offers"].values()),
                    "answered": sorted(self.state["market"]["decisions"]),
                },
                "powers": {
                    t: {
                        r: {"used": True, "name": R.POWERS[r]["name"]}
                        for r, v in self.state["teams"][t]["powers"].items()
                        if v.get("used")
                    }
                    for t in self.active_teams()
                },
                "log": self.state["log"][-30:],
            }


# ---------------------------------------------------------------------------
# Scoring (pur, testable sans instance de jeu)
# ---------------------------------------------------------------------------


def _ints(d, keys):
    d = d or {}
    out = {}
    for k in keys:
        v = d.get(k, 0)
        try:
            v = int(v)
        except (TypeError, ValueError):
            raise GameError("Valeur invalide pour %s." % k) from None
        if v < 0:
            raise GameError("Les valeurs negatives ne sont pas autorisees (%s)." % k)
        out[k] = v
    return out


def score_simple(decisions, revenue):
    """Rounds 1 et 2 : cinq acteurs critiques, valeur 40."""
    joined = {r: decisions.get(r) == "JOIN" for r in R.ROLES}
    success = all(joined.values())
    scores = {}
    for r in R.ROLES:
        if joined[r]:
            scores[r] = R.RESOURCES - R.COST[r] + (revenue.get(r, 0) if success else 0)
        else:
            scores[r] = R.RESOURCES + R.OUTSIDE[r]
    if success:
        eco = R.V_BASE - R.TOTAL_COST
    else:
        eco = -sum(R.COST[r] for r in R.ROLES if joined[r])
    return {
        "success": success,
        "joined": joined,
        "scores": scores,
        "ecosystem": eco,
        "value": R.V_BASE if success else 0,
    }


def _lock_in(rd):
    """Le proprietaire a-t-il paye plus cher que ne l'aurait fait le modulaire ?"""
    shock = rd.get("shock")
    resolution = rd.get("resolution")
    if resolution not in ("KEEP", "REPLACE"):
        return False
    mine = adaptation_cost("PROPRIETARY", shock, resolution) + (
        R.DELAY_LOSS["PROPRIETARY"] if resolution in shock_spec(shock)["delay_on"] else 0
    )
    theirs = adaptation_cost("MODULAR", shock, resolution) + (
        R.DELAY_LOSS["MODULAR"] if resolution in shock_spec(shock)["delay_on"] else 0
    )
    return mine > theirs


def shock_spec(shock):
    """Description du choc, avec repli sur le choc historique du concept."""
    return R.SHOCKS.get(shock or "AI_FAILURE", R.SHOCKS["AI_FAILURE"])


def round3_value(arch, resolution, shock=None):
    """Valeur du service au round 3 selon architecture, solution et choc.

    Le retard (DELAY_LOSS) ne frappe que l'architecture proprietaire, et
    seulement quand la reponse au choc oblige a rouvrir le systeme : remplacer
    un partenaire (AI_FAILURE, INFRA_FAILURE) ou refaire certifier l'ensemble
    (REGULATION).
    """
    if resolution == "ABANDON":
        return 0
    base = R.V_PROPRIETARY if arch == "PROPRIETARY" else R.V_MODULAR
    if resolution in shock_spec(shock)["delay_on"]:
        return base - R.DELAY_LOSS[arch]
    return base


def adaptation_cost(arch, shock, resolution, discount=0):
    """Cout collectif a repartir pour encaisser le choc (0 si sans objet)."""
    sp = shock_spec(shock)
    if resolution == "REPLACE" and sp["replace_cost"]:
        need = sp["replace_cost"][arch]
    elif resolution == "KEEP" and sp["keep_cost"]:
        need = sp["keep_cost"][arch]
    else:
        return 0
    return max(0, need - discount)


def score_round3(rd):
    arch = rd.get("architecture") or "PROPRIETARY"
    resolution = rd.get("resolution") or "ABANDON"
    shock = rd.get("shock")
    sp = shock_spec(shock)
    contrib = rd.get("standard") or {r: 0 for r in R.ROLES}
    integ = rd.get("integration") or {r: 0 for r in R.ROLES}
    contract = rd.get("contract") or {}
    decisions = rd.get("decisions") or {}

    std_total = R.STANDARD_COST if arch == "MODULAR" else 0
    # le standard est paye avant le choc : il est irrecuperable dans tous les cas
    scores = {r: R.RESOURCES - contrib.get(r, 0) for r in R.ROLES}

    if resolution == "ABANDON":
        for r in R.ROLES:
            scores[r] += R.OUTSIDE[r]
        return {
            "success": False,
            "abandoned": True,
            "resolution": "ABANDON",
            "architecture": arch,
            "joined": {r: False for r in R.ROLES},
            "scores": scores,
            "ecosystem": -std_total,
            "value": 0,
            "shock": shock,
        }

    costs = dict(R.COST)
    if resolution == "KEEP":
        # AI_FAILURE : c'est BRAIN qui met son systeme en conformite, a ses frais.
        # REGULATION : la conformite est collective, elle passe par integration.
        if sp is R.SHOCKS["AI_FAILURE"]:
            costs["BRAIN"] += R.BRAIN_ADAPTATION
        participants = list(R.ROLES)
    else:
        participants = [r for r in R.ROLES if r != sp["target"]]

    joined = {r: (r in participants and decisions.get(r) == "JOIN") for r in R.ROLES}
    value = round3_value(arch, resolution, shock)
    need = rd.get("adapt_cost")
    if need is None:
        need = adaptation_cost(arch, shock, resolution)
    alt_ok = resolution != "REPLACE" or contract.get("ALT_AI", 0) >= R.ALT_AI_MIN_REVENUE
    success = all(joined[r] for r in participants) and alt_ok

    for r in R.ROLES:
        scores[r] -= integ.get(r, 0)
        if r not in participants:
            # role ecarte au profit du substitut : il repart sur son exterieur
            scores[r] += R.OUTSIDE[r]
            continue
        if joined[r]:
            scores[r] -= costs[r]
            if success:
                scores[r] += contract.get(r, 0)
        else:
            scores[r] += R.OUTSIDE[r]

    if success:
        realized = sum(costs[r] for r in participants) + need
        if resolution == "REPLACE":
            realized += R.ALT_AI_COST
        eco = value - realized - std_total
    else:
        sunk = sum(costs[r] for r in participants if joined[r])
        eco = -(sunk + std_total + sum(integ.values()))

    return {
        "success": success,
        "abandoned": False,
        "resolution": resolution,
        "architecture": arch,
        "joined": joined,
        "scores": scores,
        "ecosystem": eco,
        "value": value if success else 0,
        "alt_ai": contract.get("ALT_AI") if resolution == "REPLACE" else None,
        "shock": shock,
        "adapt_cost": need,
    }
