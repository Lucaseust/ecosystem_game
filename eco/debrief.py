"""Données du débrief : faits comptables et chronologie, sans interprétation causale."""

import copy
import html
import json
from pathlib import Path

from . import i18n
from .campaign import allocations

DATES = ["JANUARY", "APRIL", "JULY", "OCTOBER"]
EXPENSES = {"INSTALLATION", "PROFILE", "ADAPTATION", "OPERATION"}
EVENTS = {
    "event_drawn": ("circumstance", "Événement local"),
    "risk_drawn": ("circumstance", "Résultat d'un essai"),
    "contract_committed": ("decision", "Accord signé"),
    "partner_left": ("decision", "Départ de BRAIN"),
    "renegotiation_requested": ("decision", "Renégociation demandée"),
    "capacity_withdrawn": ("decision", "Activité retirée"),
    "return_requested": ("decision", "Retour demandé"),
    "proposal_expired": ("outcome", "Proposition expirée"),
    "commissioning_interrupted": ("outcome", "Essais interrompus"),
    "funding_shortfall": ("outcome", "Financement insuffisant"),
    "replacement_delay": ("outcome", "Délai d'intégration"),
    "intervention_delay": ("outcome", "Activité réduite"),
    "expansion_overload": ("outcome", "Surcharge de l'extension"),
}


def build(game):
    """Appelé par la vue enseignant uniquement après la clôture de l'année."""
    from .campaign import INITIAL
    from .rules import ROLES

    result = dict(amount_unit="centicredit", initial_cash=INITIAL, dates=DATES[:], teams=[])
    for name in game.active_teams():
        c = game.c(name)
        ledger = [r for r in game.state["ledger"] if r["ecosystem_id"] == name]
        journal = [e for e in game.state["journal"] if e["ecosystem_id"] == name]
        actors = []
        for role in ROLES:
            rows = [r for r in ledger if r["role"] == role]
            revenue = sum(r["amount"] for r in rows if r["kind"] == "REVENUE")
            outside = sum(r["amount"] for r in rows if r["kind"] == "OUTSIDE")
            costs = -sum(r["amount"] for r in rows if r["kind"] in EXPENSES)
            actors.append(
                dict(
                    role=role,
                    revenue=revenue,
                    outside=outside,
                    costs=costs,
                    project_result=revenue - costs,
                    net=c["cash"][role] - INITIAL,
                )
            )
        finances = dict(
            revenue=c["revenue"],
            created=c["created"],
            installation=-sum(
                r["amount"] for r in ledger if r["kind"] in ("INSTALLATION", "PROFILE")
            ),
            adaptation=-sum(r["amount"] for r in ledger if r["kind"] == "ADAPTATION"),
            operation=-sum(r["amount"] for r in ledger if r["kind"] == "OPERATION"),
            supplier=sum(r["amount"] for r in ledger if r["kind"] == "EXTERNAL_SUPPLIER"),
            outside=sum(a["outside"] for a in actors),
            company_result=sum(a["net"] for a in actors),
        )
        finances["accounting_gap"] = (
            finances["revenue"]
            - sum(finances[k] for k in ("installation", "adaptation", "operation", "supplier"))
            - finances["created"]
        )
        finances["distribution_gap"] = (
            finances["created"] + finances["outside"] - finances["company_result"]
        )
        periods = [
            dict(
                date=s["date"],
                revenue=s["revenue"],
                created=s["created"],
                company_result=sum(s["cash"].values()) - len(ROLES) * INITIAL,
                operating=s["operating"],
                message=s.get("message", ""),
            )
            for s in c["settlements"]
        ]
        contracts, events = [], []
        for event in journal:
            kind, data = event["event_type"], event["data"]
            if kind == "contract_committed":
                p = data["proposal"]
                contracts.append(
                    dict(
                        revision=p["revision"],
                        date=event["economic_date"],
                        sequence=event["sequence"],
                        kind=p["kind"],
                        architecture=p["architecture"],
                        allocations=copy.deepcopy(allocations(p)),
                        funding=copy.deepcopy(p["funding"]),
                    )
                )
            if kind not in EVENTS:
                continue
            category, title = EVENTS[kind]
            detail = event.get("public_message") or ""
            if kind == "event_drawn":
                title = data.get("selected", title)
                detail = event.get("public_message") or "Tirage local enregistré."
                if title == "ORDINARY":
                    category = "context"
                if not data.get("eligible", True):
                    category, title = "context", "EXISTING_SITUATION"
                    detail += " La situation existante ne permettait pas un nouvel événement d'exploitation."
                shock = data.get("intensity")
                if isinstance(shock, dict):
                    if shock.get("increase"):
                        detail += (
                            " %s : frais augmentés de %.2f crédits par trimestre engagé jusqu'en décembre."
                            % (shock["role"], shock["increase"] / 100)
                        )
                    elif shock.get("adjustment"):
                        detail += (
                            " Recettes à pleine capacité : %.2f crédits par trimestre par rapport au niveau précédent."
                            % (shock["adjustment"] / 100)
                        )
            elif kind == "risk_drawn":
                title = (
                    "Essais de lancement"
                    if data.get("channel") == "commissioning"
                    else "Essais d'extension"
                )
                outcome = {
                    "READY": "Essais validés",
                    "INTERRUPTION": "Mise en service interrompue",
                    "OVERLOAD": "Capacité surchargée",
                }.get(data.get("selected"), "Résultat enregistré")
                detail = (
                    "%s. Risque d'interruption ou de surcharge pour ces essais : %.0f %% (selon la préparation et le mode de lancement)."
                    % (outcome, data.get("probability", 0) * 100)
                )
            events.append(
                dict(
                    sequence=event["sequence"],
                    date=event["economic_date"],
                    category=category,
                    kind=kind,
                    title=title,
                    detail=detail,
                    rules_version=event["rules_version"],
                )
            )
        result["teams"].append(
            dict(
                team=name,
                architecture=c["architecture"],
                installed=c["installed"],
                finances=finances,
                actors=actors,
                periods=periods,
                contracts=contracts,
                events=events,
                proposal_count=sum(e["event_type"] == "proposal_published" for e in journal),
                refusal_count=sum(
                    e["event_type"] == "consent_submitted" and e["data"].get("choice") == "REFUSE"
                    for e in journal
                ),
            )
        )
    return result


def html_report(data, css, script, code, language="fr"):
    """Rapport autonome : ni nom de participant, ni jeton, ni appel au serveur."""
    # Une marque d'encodage au milieu du HTML invaliderait le premier sélecteur CSS.
    css = css.replace("\ufeff", "")
    script = script.lstrip("\ufeff")
    encoded = (
        json.dumps(i18n.view(data, language), ensure_ascii=False)
        .replace("<", "\\u003c")
        .replace(">", "\\u003e")
        .replace("&", "\\u0026")
    )
    runtime = (Path(__file__).resolve().parent.parent / "web" / "i18n.js").read_text(
        encoding="utf-8"
    )
    catalogue = json.dumps(i18n.catalog() if language == "en" else {}, ensure_ascii=False).replace(
        "<", "\\u003c"
    )
    title = i18n.translate("Compte rendu de la séance", language)
    offline = i18n.translate("consultation hors connexion", language)
    report_label = i18n.translate("débrief", language)
    return f'''<!doctype html>
<html lang="{language}"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>ECOSYSTEM · {report_label} {html.escape(str(code))}</title><style>{css}</style></head>
<body><div class="host-masthead"><b>ecosystem.</b><span>{title} {html.escape(str(code))} · {offline}</span></div>
<main id="view" class="wide"></main><script>{runtime}\nEcoI18n.configure({catalogue});\n{script}</script>
<script>const reportData={encoded};function render(){{document.getElementById("view").innerHTML=Debrief.render(reportData);}}render();</script>
</body></html>'''
