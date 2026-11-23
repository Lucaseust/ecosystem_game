/* ECOSYSTEM — application joueur (telephone) */
"use strict";

const ROLES = ["MOBI", "AUTO", "BRAIN", "GRID", "FLEET"];
const ROLE_ASSETS = { MOBI: "L’application et les clients", AUTO: "Les véhicules", BRAIN: "La conduite autonome", GRID: "L’énergie et les dépôts", FLEET: "Les opérations sur le terrain" };
const COLORS = {
  BLUE: "#7abfff", GREEN: "#85e0b2", RED: "#ff9c92",
  YELLOW: "#efcf79", PURPLE: "#c2a8ff", ORANGE: "#ffb47e"
};
const R1_REVENUE = { MOBI: 14, AUTO: 10, BRAIN: 6, GRID: 6, FLEET: 4 };

/* les trois chocs possibles : miroir exact de eco/rules.py */
const SHOCKS = {
  AI_FAILURE: {
    label: "AI FAILURE",
    title: "Alerte · certification de l’IA refusée",
    target: "BRAIN", alt: "ALT-AI",
    options: ["KEEP", "REPLACE", "ABANDON"],
    keepLabel: "Garder BRAIN", replaceLabel: "Passer à ALT-AI",
    replace: { PROPRIETARY: 8, MODULAR: 2 }, keep: null,
    delay: ["REPLACE"],
    lines: [
      "Le régulateur annonce que le système autonome de <b>BRAIN</b> ne sera pas certifié dans les délais.",
      "BRAIN peut adapter son système : <b>6 points</b> à sa charge.",
      "Ou vous le remplacez par <b>ALT-AI</b>, qui exige <b>au moins 8 points</b> de revenu.",
      "Ou vous abandonnez le projet."
    ]
  },
  INFRA_FAILURE: {
    label: "INFRA FAILURE",
    title: "Alerte · défaillance de l’infrastructure",
    target: "GRID", alt: "ALT-INFRA",
    options: ["REPLACE", "ABANDON"],
    keepLabel: "", replaceLabel: "Passer à ALT-INFRA",
    replace: { PROPRIETARY: 10, MODULAR: 4 }, keep: null,
    delay: ["REPLACE"],
    lines: [
      "Votre fournisseur d'infrastructure — <b>GRID</b> — n'est plus en mesure d'assurer stations, dépôts et maintenance.",
      "Vous le remplacez par <b>ALT-INFRA</b>, qui exige <b>au moins 8 points</b> de revenu.",
      "Ou vous abandonnez le projet."
    ]
  },
  REGULATION: {
    label: "NEW REGULATION",
    title: "Alerte · nouvelle réglementation",
    target: null, alt: null,
    options: ["KEEP", "ABANDON"],
    keepLabel: "Se mettre en conformité", replaceLabel: "",
    replace: null, keep: { PROPRIETARY: 8, MODULAR: 3 },
    delay: ["KEEP"],
    lines: [
      "Une nouvelle réglementation impose une adaptation technique et une mise en conformité de tout le service.",
      "Personne ne disparaît : c'est l'ensemble de l'écosystème qui doit se mettre à niveau, à ses frais.",
      "Ou vous abandonnez le projet."
    ]
  }
};

function shockOf() { return SHOCKS[S.st.shock] || SHOCKS.AI_FAILURE; }

function adaptNeed(arch, res) {
  const sh = shockOf();
  let need = 0;
  if (res === "REPLACE" && sh.replace) need = sh.replace[arch];
  else if (res === "KEEP" && sh.keep) need = sh.keep[arch];
  if (need && (S.st.team.powers || {}).GRID) need -= 2;
  return Math.max(0, need);
}

function payers() {
  const t = shockOf().target;
  return ROLES.filter((r) => r !== t);
}
const VALUE_PROP = "Permettre à un utilisateur de réserver à la demande une " +
  "navette autonome, avec moins de dix minutes d'attente, un trajet fiable et " +
  "un prix inférieur à celui d'un taxi.";

const S = { token: null, st: null, version: 0, offset: 0, draft: {}, seeded: {}, tab: "situation", scene: null };

/* Des faits et un enjeu, sans annoncer les mecanismes a venir. */
const SCENES = {
  LOBBY: ["Le projet", "La ville attend sa première navette.", "Métropole, 2032. Les habitants veulent un trajet fiable, moins cher qu’un taxi, avec moins de dix minutes d’attente. Cinq entreprises ont les moyens de créer ce service. Aucune ne peut le faire seule."],
  R1_NEGO: ["Première proposition", "Le projet a un prix. Votre accord aussi.", "Un premier partage des 40 points de revenu est sur la table. Les parts sont imposées. Chaque entreprise reste libre de participer ou de poursuivre ses propres affaires."],
  R2_NEGO: ["Nouvelle proposition", "La feuille est à vous.", "Vous pouvez maintenant répartir librement les 40 points de revenu du service. MOBI publie les propositions ; chaque partenaire décide s’il s’engage."],
  MARKET: ["Le marché s’ouvre", "Les partenaires peuvent aussi se quitter.", "D’autres écosystèmes recherchent une technologie de conduite autonome. MOBI peut adresser une offre à un BRAIN concurrent. BRAIN peut rester ou accepter une offre, sous réserve d’une place disponible."],
  R3_ARCH: ["Un engagement durable", "Comment allez-vous construire le service ?", "Votre alliance doit choisir une architecture pour les trois prochaines années. Une intégration sur mesure promet davantage de revenu. Des interfaces communes rendent les partenaires plus faciles à remplacer. L’environnement reste incertain."],
  R3_SHOCK: ["Édition spéciale", "Une nouvelle vient de tomber.", "Les conditions du projet viennent de changer. L’annonce ci-dessous est désormais connue de toute la table."],
  R3_NEGO: ["Le projet sous pression", "L’accord tient-il encore ?", "Votre architecture est en place, mais les conditions ont changé. La table peut publier un nouvel accord ou renoncer au service."],
  FINAL: ["Fin de partie", "Qu’avez-vous gagné ensemble ?", "Les comptes sont arrêtés. Voici les résultats des entreprises et des écosystèmes."],
  DEBRIEF: ["Retour à la table", "Vos choix ont laissé des traces.", "Revenez sur les accords, les refus et leurs conséquences avec l’enseignant."]
};

function scene() {
  if (S.st.phase.endsWith("_DECIDE")) return ["Décision privée", "Alors, vous embarquez ?", "Le contrat publié est celui sur lequel vous vous engagez. Votre choix reste secret jusqu’aux résultats. Une intention annoncée à la table ne vous oblige pas à signer."];
  if (S.st.phase.endsWith("_RESULTS")) return ["Les comptes", "Voici ce que vos décisions ont produit.", "Les votes sont révélés. Le résultat dépend de l’engagement de chaque partenaire nécessaire au service."];
  return SCENES[S.st.phase] || ["En cours", "La partie continue.", ""];
}

function sceneStatus() {
  if (S.st.phase.endsWith("_NEGO")) return "Discussion ouverte";
  if (S.st.phase.endsWith("_DECIDE")) return "Vote secret ouvert";
  if (S.st.phase.endsWith("_RESULTS")) return "Votes révélés";
  return { LOBBY: "La table se réunit", MARKET: "Offres ouvertes", R3_ARCH: "Choix d’architecture ouvert", R3_SHOCK: "Annonce publique", FINAL: "Partie terminée", DEBRIEF: "Discussion avec la salle" }[S.st.phase] || "Partie en cours";
}

function chooseTab(tab) {
  if (!["situation", "entreprise", "table"].includes(tab)) return;
  S.tab = tab;
  render();
  window.scrollTo(0, 0);
}

function workspace() {
  if (S.st.me.identity_required) return identityPanel();
  if (S.tab === "entreprise") return `<header class="page-heading"><span class="edition">Dossier confidentiel</span><h1>Mon entreprise</h1><p>Vos chiffres vous appartiennent. Vous choisissez ce que vous révélez.</p></header>${S.st.me.power?.available || S.st.team.pending_exclusive ? powerCard() : ""}${myCard()}${S.st.round && !S.st.phase.endsWith("_RESULTS") ? calculator(S.st.round) : ""}${!S.st.me.power?.available && !S.st.team.pending_exclusive ? powerCard() : ""}`;
  if (S.tab === "table") return `<header class="page-heading"><span class="edition">Écosystème ${esc(S.st.me.team)}</span><h1>La table</h1><p>Des partenaires, des intérêts et une conversation à construire.</p></header>${teamSeats()}${S.st.phase === "LOBBY" ? '<p class="table-note">Retrouvez ces partenaires dans la salle. Chaque entreprise apporte une pièce du service.</p>' : claims()}`;
  const [label, title, text] = scene();
  return `<header class="page-heading"><span class="edition">${esc(label)}</span><h1>${esc(title)}</h1><p>${esc(text)}</p></header>${panel()}`;
}

/* --- utilitaires --------------------------------------------------------- */

const $ = (id) => document.getElementById(id);
const esc = (s) => String(s == null ? "" : s).replace(/[&<>"']/g,
  (c) => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" }[c]));
const sleep = (ms) => new Promise((r) => setTimeout(r, ms));
const sum = (o) => Object.values(o || {}).reduce((a, b) => a + (Number(b) || 0), 0);
const signed = (n) => (n > 0 ? "+" + n : String(n));

function toast(msg, ok) {
  const t = document.createElement("div");
  t.className = "toast" + (ok ? " ok" : "");
  t.setAttribute("role", "status");
  t.textContent = msg;
  document.body.appendChild(t);
  setTimeout(() => t.remove(), 3800);
}

async function api(path, body) {
  const r = await fetch(path, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(body)
  });
  const data = await r.json().catch(() => ({}));
  if (!r.ok) throw new Error(data.error || "Erreur réseau");
  return data;
}

async function act(action, extra) {
  try {
    await api("/api/action", Object.assign({ token: S.token, action }, extra || {}));
    return true;
  } catch (e) {
    toast(e.message);
    return false;
  }
}

/* --- connexion ----------------------------------------------------------- */

async function doJoin() {
  const first_name = $("pname").value.trim();
  const last_name = $("plastname").value.trim();
  const code = $("pcode").value.trim().toUpperCase();
  const err = $("gateerr");
  err.hidden = true;
  if (!first_name) { err.textContent = "Indiquez votre prénom."; err.hidden = false; $("pname").focus(); return; }
  if (!last_name) { err.textContent = "Indiquez votre nom de famille."; err.hidden = false; $("plastname").focus(); return; }
  if (!code) { err.textContent = "Indiquez le code affiché par l'enseignant.";
               err.hidden = false; return; }
  $("gojoin").disabled = true;
  try {
    const res = await api("/api/join", { first_name, last_name, code });
    S.token = res.token;
    localStorage.setItem("eco_token", res.token);
    localStorage.setItem("eco_code", code);
    start();
  } catch (e) {
    err.textContent = e.message;
    err.hidden = false;
  } finally {
    $("gojoin").disabled = false;
  }
}

function logout(message) {
  window.EcoIntro?.reset();
  localStorage.removeItem("eco_token");
  S.token = null;
  S.draft = {};
  S.seeded = {};
  S.identityDraft = null;
  S.scene = null;
  S.version = 0;
  $("game").hidden = true;
  $("gate").hidden = false;
  if (message) { $("gateerr").textContent = message; $("gateerr").hidden = false; }
}

function start() {
  $("gate").hidden = true;
  $("game").hidden = false;
  poll();
}

/* --- boucle de synchronisation (long polling) ---------------------------- */

async function poll() {
  for (;;) {
    try {
      const r = await fetch("/api/state?token=" + encodeURIComponent(S.token) +
                            "&since=" + S.version);
      if (r.status === 401) {
        return logout("Votre session a expiré. Rejoignez la partie.");
      }
      if (!r.ok) throw new Error("http " + r.status);
      const st = await r.json();
      $("offline").hidden = true;
      S.offset = st.server_time * 1000 - Date.now();
      S.st = st;
      S.version = st.version;
      render();
    } catch (e) {
      $("offline").hidden = false;
      await sleep(1500);
    }
  }
}

/* --- chrono -------------------------------------------------------------- */

function remaining() {
  const t = S.st && S.st.timer;
  if (!t || t.remaining == null) return null;
  if (!t.running || !t.ends_at) return t.remaining;
  return Math.round(t.ends_at - (Date.now() + S.offset) / 1000);
}

function tick() {
  const box = $("tTimer");
  if (!box) return;
  const r = remaining();
  if (r == null) { box.textContent = "—"; box.className = "timer"; return; }
  const neg = r < 0, a = Math.abs(r);
  box.textContent = (neg ? "-" : "") +
    String(Math.floor(a / 60)).padStart(2, "0") + ":" +
    String(a % 60).padStart(2, "0");
  box.className = "timer" + (r <= 0 ? " over" : r <= 30 ? " low" : "");
}
setInterval(tick, 250);

/* --- rendu --------------------------------------------------------------- */

function render() {
  const st = S.st;
  if (!st) return;
  document.documentElement.style.setProperty("--team", COLORS[st.me.team] || "#6ea8fe");

  $("tRole").textContent = st.me.role;
  $("tName").textContent = st.me.name;
  $("tTeam").textContent = "Écosystème " + st.me.team + " · " + st.me.card.title;
  const sceneKey = [st.phase, st.me.team, st.me.role].join(":");
  const seatKey = [st.me.team, st.me.role].join(":");
  if (S.seat && S.seat !== seatKey) { S.draft = {}; S.seeded = {}; }
  S.seat = seatKey;
  const newScene = S.scene !== sceneKey;
  if (newScene) { S.tab = "situation"; S.scene = sceneKey; }
  $("tPhase").textContent = sceneStatus();
  tick();

  seedDrafts();

  // preserve le focus et le curseur pendant le re-rendu
  const a = document.activeElement;
  const keep = a && a.id && $("app").contains(a)
    ? { id: a.id, s: a.selectionStart, e: a.selectionEnd } : null;

  replacePanel($("app"), workspace());
  const nav = $("playerNav");
  nav.hidden = !!st.me.identity_required;
  const activeNav = document.activeElement;
  const navFocus = activeNav && nav.contains(activeNav) ? activeNav.id : null;
  nav.innerHTML = [["situation", "01", "La situation"], ["entreprise", "02", "Mon entreprise"], ["table", "03", "La table"]].map(([key, number, label]) =>
    `<button id="nav-${key}" aria-current="${S.tab === key ? "page" : "false"}" onclick="chooseTab('${key}')"><span>${number}</span>${label}${key === "entreprise" && st.me.power?.available ? '<i class="power-dot" aria-label="Action spéciale disponible"></i>' : ""}</button>`).join("");
  if (navFocus) $(navFocus)?.focus({ preventScroll: true });
  if (newScene) window.scrollTo(0, 0);

  if (keep) {
    const back = $(keep.id);
    if (back) {
      back.focus();
      try { back.setSelectionRange(keep.s, keep.e); } catch (_) {}
    }
  }
  window.EcoIntro?.sync(st.me, S.token);
}

function panel() {
  if (S.st.me.identity_required) return identityPanel();
  S.identityDraft = null;
  const p = S.st.phase;
  switch (p) {
    case "LOBBY":      return lobby();
    case "R1_NEGO":    return round1Nego();
    case "R1_DECIDE":  return decide(1);
    case "R1_RESULTS": return results(1);
    case "R2_NEGO":    return round2Nego();
    case "R2_DECIDE":  return decide(2);
    case "R2_RESULTS": return results(2);
    case "MARKET":     return market();
    case "R3_ARCH":    return round3Arch();
    case "R3_SHOCK":   return shockCard(false);
    case "R3_NEGO":    return round3Nego();
    case "R3_DECIDE":  return decide(3);
    case "R3_RESULTS": return results(3);
    case "FINAL":      return final();
    case "DEBRIEF":    return debrief();
    default:           return "";
  }
}

function identityPanel() {
  if (!S.identityDraft) S.identityDraft = {
    first_name: S.st.me.first_name || "", last_name: S.st.me.last_name || ""
  };
  return `<form class="card accent" onsubmit="event.preventDefault(); sendIdentity()">
    <h2>Votre nom et votre prénom</h2>
    <p class="small muted">L’enseignant souhaite identifier chaque étudiant dans le tableau de bord.</p>
    <label for="identityFirst">Prénom</label>
    <input id="identityFirst" type="text" autocomplete="given-name" maxlength="40" required
      value="${esc(S.identityDraft.first_name)}">
    <div style="height:.8rem"></div>
    <label for="identityLast">Nom de famille</label>
    <input id="identityLast" type="text" autocomplete="family-name" maxlength="40" required
      value="${esc(S.identityDraft.last_name)}">
    <button id="saveIdentity" class="primary block" type="submit" style="margin-top:1rem">Enregistrer et continuer</button>
  </form>`;
}

async function sendIdentity() {
  const first_name = $("identityFirst").value.trim();
  const last_name = $("identityLast").value.trim();
  if (!first_name || !last_name) return toast("Renseignez votre prénom et votre nom de famille.");
  $("saveIdentity").disabled = true;
  const ok = await act("identity", { first_name, last_name });
  if (ok) toast("Nom et prénom enregistrés", true);
  else if ($("saveIdentity")) $("saveIdentity").disabled = false;
}

/* --- fragments communs --------------------------------------------------- */

function myCard() {
  const me = S.st.me, c = me.card;
  return `
  <section class="company-file">
    <div class="company-name"><span>${esc(me.role)}</span><h2>${esc(c.title)}</h2></div>
    <p class="quote">${esc(c.tagline)}</p>
    <p class="small">${esc(c.brief)}</p>
    <div class="private-ledger">
      <div><span>Ressources au début de chaque manche</span><b>10 <small>pts</small></b></div>
      <div><span>Votre investissement si vous participez</span><b>${me.cost} <small>pts</small></b></div>
      <div><span>Votre revenu hors de ce projet</span><b>${me.outside} <small>pts</small></b></div>
    </div>
    <p class="small muted">Votre objectif : obtenir le meilleur score pour votre entreprise.</p>
    <details><summary>Ce que votre entreprise apporte</summary><ul class="small">${c.controls.map((x) => `<li>${esc(x)}</li>`).join("")}</ul></details>
    ${gameRules()}
  </section>`;
}

function gameRules() {
  return `<details class="game-rules"><summary>Comment les points fonctionnent</summary><p class="small">Chaque manche commence avec 10 points. Si vous participez, votre investissement est déduit. Votre part de revenu n’est versée que si tous les partenaires nécessaires participent. Si le service échoue, l’investissement est perdu.</p><p class="small">Si vous vous retirez, vous conservez vos ressources et gagnez votre revenu hors du projet. Les contributions déjà engagées restent à votre charge. Sans réponse à la clôture, vous êtes retiré du projet.</p><p class="small">Les annonces à la table sont publiques. Le vote est secret et peut être changé tant qu’il est ouvert. Un binôme partage une décision et un score.</p></details>`;
}

/* --- pouvoir de role (un seul usage par partie) --------------------------- */

function powerCard() {
  const pw = S.st.me.power;
  if (!pw) return "";
  const used = pw.used;
  return `
  <div class="card ${used ? "" : pw.available ? "accent" : "tight"}">
    <span class="edition">Action spéciale · Un seul usage</span>
    <h3 style="display:flex;justify-content:space-between;align-items:baseline;gap:.6rem">
      <span>${esc(pw.name)}</span>
      ${used ? `<span class="small" style="color:var(--good)">POUVOIR UTILISÉ</span>` : ""}
    </h3>
    <p class="small" style="margin:0 0 .6rem">${esc(pw.text)}</p>
    ${used
      ? `<p class="tiny muted" style="margin:0">${esc(pw.detail || "")}</p>`
      : pw.available ? powerForm() :
        `<p class="tiny muted" style="margin:0">${esc(pw.why)}</p>`}
  </div>
  ${exclusivityInbox()}`;
}

function powerForm() {
  if (S.st.me.role === "MOBI") {
    return `
    <div class="row">
      <select id="pw_target" aria-label="Partenaire bénéficiaire" data-k="powerTarget">
        ${ROLES.filter((r) => r !== "MOBI").map((r) =>
          `<option value="${r}" ${S.draft.powerTarget === r ? "selected" : ""}>${r}</option>`).join("")}
      </select>
      <input id="pw_amount" type="number" min="1" max="3" aria-label="Points transférés" data-k="powerAmount" value="${esc(S.draft.powerAmount ?? 3)}" style="width:5rem">
    </div>
    <div style="height:.6rem"></div>
    <button class="primary block" onclick="usePower()">UTILISER MON POUVOIR</button>`;
  }
  return `<button class="primary block" onclick="usePower()">UTILISER MON POUVOIR</button>`;
}

async function usePower() {
  const pw = S.st.me.power;
  const extra = {};
  let ask = `Utiliser ${pw.name} ? Ce pouvoir ne sert qu'une fois dans la partie.`;
  if (S.st.me.role === "MOBI") {
    extra.target = $("pw_target").value;
    extra.amount = Number($("pw_amount").value) || 0;
    ask = `Transférer ${extra.amount} point(s) de votre part vers ${extra.target} ?`
        + " Ce pouvoir ne sert qu'une fois.";
  }
  if (!confirm(ask)) return;
  if (await act("power", extra)) toast("Pouvoir activé", true);
}

/* MOBI recoit la proposition d'exclusivite de BRAIN */
function exclusivityInbox() {
  if (S.st.me.role !== "MOBI" || !S.st.team.pending_exclusive) return "";
  return `<div class="card warn">
    <h3>BRAIN propose l'exclusivité</h3>
    <p class="small" style="margin:0 0 .7rem">BRAIN demande <b>+3 points</b>, pris sur
    votre part, et s'engage en échange à rester dans votre écosystème jusqu’à la fin de la partie.</p>
    <div class="row">
      <button class="primary" onclick="answerExclusivity(true)">Accepter</button>
      <button onclick="answerExclusivity(false)">Refuser</button>
    </div>
  </div>`;
}

async function answerExclusivity(accept) {
  if (accept && !confirm("Accorder l'exclusivité à BRAIN pour 3 points de votre part ?")) return;
  if (await act("exclusivity", { accept })) toast(accept ? "Exclusivité accordée" : "Refusé", true);
}

/* --- marche des ecosystemes ---------------------------------------------- */

function market() {
  const mk = S.st.market || {};
  const role = S.st.me.role;
  const intro = `
  <div class="card accent">
    <h3>Marché des écosystèmes</h3>
    <p style="margin:0 0 .5rem">Trois minutes. Seul <b>BRAIN</b> peut changer
    d'écosystème. Les orchestrateurs peuvent lui faire une offre en points,
    prise sur leur propre part.</p>
    <p class="small muted" style="margin:0">Un écosystème n'héberge qu'un seul BRAIN :
    un départ n'est validé que si le siège visé est lui-même libéré. Changer coûte
    <b>${mk.switch_cost} points</b> à BRAIN, et ne se fait qu'une fois.</p>
  </div>`;

  let body = "";
  if (role === "MOBI") body = marketOffers(mk);
  else if (role === "BRAIN") body = marketChoice(mk);
  else body = `<div class="card tight"><p class="small muted" style="margin:0">
    Votre entreprise reste dans cet écosystème. Les offres et les départs de BRAIN concernent les partenaires autour de votre table.</p></div>`;

  return `${intro}${body}`;
}

function marketOffers(mk) {
  const sent = mk.sent || {};
  return `<div class="card">
    <h3>Vos offres aux BRAIN des autres écosystèmes</h3>
    <p class="small muted" style="margin:0 0 .6rem">
      De 0 à ${mk.offer_max} points. Une offre acceptée est prélevée sur votre part.
      0 retire l'offre.</p>
    <table><tbody>
      ${(mk.targets || []).map((t) => `<tr>
        <td><b style="color:${COLORS[t]}">${t}</b></td>
        <td style="width:6rem"><input id="of_${t}" type="number" min="0"
          max="${mk.offer_max}" aria-label="Offre au BRAIN de ${t}" data-k="offer${t}" value="${esc(S.draft['offer' + t] ?? sent[t] ?? 0)}"></td>
        <td style="width:6rem"><button onclick="sendOffer('${t}')">Envoyer</button></td>
      </tr>`).join("")}
    </tbody></table>
    ${Object.keys(sent).length ? `<p class="tiny muted" style="margin:.7rem 0 0">
      Offres en cours : ${Object.entries(sent).map(([t, v]) =>
        `${t} ${v} pts`).join(" · ")}. Les BRAIN décident en secret.</p>` : ""}
  </div>`;
}

async function sendOffer(team) {
  const points = Number($("of_" + team).value) || 0;
  if (await act("offer", { target: team, points })) toast("Offre transmise", true);
}

function marketChoice(mk) {
  const got = mk.received || {};
  const keys = Object.keys(got).sort();
  const chosen = mk.decision;
  if (mk.locked) {
    return `<div class="card good"><h3>Vous êtes engagé</h3>
      <p style="margin:0">Vous avez accordé l'exclusivité à votre écosystème :
      vous ne pouvez plus accepter d'offre.</p></div>`;
  }
  return `<div class="card">
    <h3>Votre décision — elle reste secrète</h3>
    <p class="small muted" style="margin:0 0 .7rem">
      Écosystème actuel : <b style="color:${COLORS[S.st.me.team]}">${S.st.me.team}</b>.</p>
    <div class="seg" style="flex-wrap:wrap">
      <button aria-pressed="${chosen === "STAY"}"
        onclick="sendMarket('STAY')">RESTER</button>
      ${keys.map((t) => `<button aria-pressed="${chosen === t}"
        onclick="sendMarket('${t}')">${t} · +${got[t]} pts</button>`).join("")}
    </div>
    ${keys.length ? "" : `<p class="small muted" style="margin:.8rem 0 0">
      Aucune offre reçue pour l'instant.</p>`}
    ${chosen ? `<p class="tiny muted" style="margin:.8rem 0 0">
      Enregistré : <b>${chosen === "STAY" ? "rester" : "rejoindre " + chosen}</b>.
      ${chosen === "STAY" ? "" : `Coût du changement : ${mk.switch_cost} points.`}</p>` : ""}
  </div>`;
}

async function sendMarket(choice) {
  const mk = S.st.market || {};
  if (choice !== "STAY") {
    const price = (mk.received || {})[choice] || 0;
    if (!confirm(`Rejoindre ${choice} pour +${price} points, moins `
      + `${mk.switch_cost} points de changement ? Vous quittez ${S.st.me.team}.`)) return;
  }
  if (await act("market", { choice })) toast("Décision enregistrée", true);
}

function valueProp() {
  return `<div class="card accent">
    <h3>Proposition de valeur</h3>
    <p class="quote" style="margin:0">${esc(VALUE_PROP)}</p>
  </div>`;
}

function teamSeats() {
  const t = S.st.team;
  return `<div class="card tight">
    <h3>Écosystème ${esc(t.team)}</h3>
    <table><tbody>
      ${ROLES.map((r) => `
        <tr class="${r === S.st.me.role ? "me" : ""}">
          <td style="width:45%"><b>${r}</b><span class="seat-asset">${ROLE_ASSETS[r]}</span></td>
          <td class="muted">${t.seats[r].bot
            ? '<span class="pill bot">siège vacant</span>'
            : esc(t.seats[r].names.join(", "))}</td>
        </tr>`).join("")}
    </tbody></table>
  </div>`;
}

/* Revenu actuellement propose a mon role pour le round en cours. */
function myRevenue(n) {
  const rd = S.st.team.rounds[String(n)];
  if (n === 1) return R1_REVENUE[S.st.me.role];
  if (!rd.contract) return null;
  if (n === 3 && rd.resolution === "REPLACE" && S.st.me.role === shockOf().target) return null;
  return rd.contract[S.st.me.role];
}

/* Cout total que je supporte ce round (investissement + contributions). */
function myCosts(n) {
  const me = S.st.me, rd = S.st.team.rounds[String(n)];
  let invest = me.cost, extras = 0, notes = [];
  if (n === 3) {
    const std = (rd.standard || {})[me.role] || 0;
    const integ = (rd.integration || {})[me.role] || 0;
    if (std) { extras += std; notes.push(`standard ${std}`); }
    if (integ) { extras += integ; notes.push(`intégration ${integ}`); }
    if (rd.resolution === "KEEP" && me.role === "BRAIN" && S.st.shock === "AI_FAILURE") {
      invest += 6; notes.push("mise en conformité 6");
    }
  }
  return { invest, extras, notes };
}

function calculator(n) {
  const me = S.st.me, rev = myRevenue(n), c = myCosts(n);
  const rd = S.st.team.rounds[String(n)];
  const ejected = n === 3 && rd.resolution === "REPLACE" && me.role === shockOf().target;
  return `<details class="decision-ledger"><summary>Mes chiffres pour cet accord · privé</summary>
    <div class="private-ledger">
      <div><span>Ressources de départ</span><b>10</b></div>
      <div><span>Investissement si je participe</span><b>${ejected ? "—" : c.invest}</b></div>
      <div><span>Revenu proposé si le service fonctionne</span><b>${rev == null ? "—" : rev}</b></div>
      <div><span>Revenu hors du projet</span><b>${me.outside}</b></div>
      ${c.extras ? `<div><span>Contributions engagées · ${esc(c.notes.filter((x) => !x.startsWith("mise en conformité")).join(", "))}</span><b>${c.extras}</b></div>` : ""}
    </div><p class="tiny muted">Vos contributions restent dues, même en cas de retrait. L’investissement n’est dépensé que si vous participez ; le revenu du projet dépend du lancement du service.</p>
  </details>`;
}

/* --- tableau des exigences publiques ------------------------------------- */

function claims() {
  const t = S.st.team, me = S.st.me;
  const mine = t.claims[me.role] || {};
  const fixed = S.st.phase.startsWith("R1_");
  const editable = ["R1_NEGO", "R2_NEGO", "R3_NEGO"].includes(S.st.phase);
  return `<div class="card">
    <h3>Paroles de la table</h3>
    <table><tbody>
      ${ROLES.map((r) => {
        const c = t.claims[r];
        return `<tr class="${r === me.role ? "me" : ""}">
          <td style="width:4.6rem"><b>${r}</b></td>
          ${fixed ? "" : `<td class="num mono" style="width:3rem">${
            c && c.amount != null ? "≥ " + c.amount : "—"}</td>`}
          <td class="small muted">${c ? esc(c.text) : ""}</td>
        </tr>`;
      }).join("")}
    </tbody></table>
    ${editable ? `<p class="small muted">Une annonce engage la discussion, pas votre vote. Vous pouvez garder vos chiffres privés.</p><div class="row" style="margin-top:.8rem">
      ${fixed ? "" : `<div style="width:6.5rem">
        <label for="claimAmt">Je demande ≥</label>
        <input id="claimAmt" type="number" min="0" max="46" data-k="claimAmount"
               value="${esc(S.draft.claimAmount ?? mine.amount ?? "")}">
      </div>`}
      <div class="grow">
        <label for="claimTxt">${fixed ? "Votre réaction à l’offre" : "Message (facultatif)"}</label>
        <input id="claimTxt" type="text" maxlength="80" data-k="claimText"
               value="${esc(S.draft.claimText ?? mine.text ?? "")}" placeholder="${fixed ? "Ce que vous souhaitez dire à la table" : "Votre condition pour rejoindre"}">
      </div>
    </div>
    <div style="height:.6rem"></div>
    <button class="block" onclick="sendClaim()">Prendre la parole →</button>` : '<p class="tiny muted">Les annonces sont fermées à cette étape.</p>'}
  </div>`;
}

async function sendClaim() {
  const ok = await act("claim", {
    amount: $("claimAmt")?.value || null,
    text: $("claimTxt").value
  });
  if (ok) toast("Annonce publiée", true);
}

/* --- LOBBY --------------------------------------------------------------- */

function lobby() {
  const me = S.st.me;
  return `
  <section class="seat-ticket"><span class="edition">Votre place à la table ${esc(me.team)}</span><strong>${esc(me.role)}</strong><p>${esc(me.card.title)}</p><p class="small muted">${esc(me.card.tagline)}</p><button class="primary block" onclick="chooseTab('entreprise')">Ouvrir mon dossier confidentiel →</button></section>
  <p class="table-note">Vous cherchez à gagner le plus de points pour votre entreprise. Les autres poursuivent leur propre objectif. À vous de trouver votre place dans cet accord.</p>
  <p class="waiting"><span></span>La table se réunit. La partie démarrera avec l’enseignant.</p>`;
}

/* --- ROUND 1 ------------------------------------------------------------- */

function round1Nego() {
  return `
  ${contractView(S.st.team.rounds["1"], true)}
  ${negotiation(1)}
  ${gameRules()}`;
}

/* --- ROUND 2 ------------------------------------------------------------- */

function round2Nego() {
  const isMobi = S.st.me.role === "MOBI";
  const rd = S.st.team.rounds["2"];
  return `
  ${isMobi ? contractEditor() : contractView(rd)}
  ${negotiation(2)}
  ${gameRules()}`;
}

function contractView(rd, imposed = false) {
  if (!rd.contract) {
    return `<div class="card warn">
      <h3>Contrat</h3>
      <p style="margin:0">MOBI n'a pas encore publié de contrat.</p>
    </div>`;
  }
  return `<div class="card">
    <div class="spread"><h3>${imposed ? "Répartition imposée" : "Contrat publié"}</h3><span class="edition">${sum(rd.contract)} points</span></div>
    <dl class="allocation" aria-label="Répartition des revenus">${ROLES.map((r) => `<div class="${r === S.st.me.role ? "my-allocation" : ""}"><dt>${r}</dt><dd>${rd.contract[r]}</dd></div>`).join("")}</dl>
    ${imposed ? '<p class="tiny muted" style="margin:0">Les parts sont fixes pour cette manche.</p>' : ""}
  </div>`;
}

function contractEditor() {
  const d = S.draft.contract, total = sum(d);
  const ok = total === 40;
  return `<div class="card accent">
    <h3>Contrat d'écosystème — vous êtes MOBI</h3>
    <table><tbody>
      ${ROLES.map((r) => `<tr>
        <td><b>${r}</b></td>
        <td style="width:6.5rem">
          <input id="c_${r}" type="number" min="0" max="40" aria-label="Revenu ${r}" data-k="contract.${r}"
                 value="${d[r]}"></td>
      </tr>`).join("")}
      <tr class="total"><td>TOTAL</td>
        <td class="num mono" style="color:${ok ? "var(--good)" : "var(--bad)"}">
          ${total} / 40</td></tr>
    </tbody></table>
    <div style="height:.7rem"></div>
    <button class="primary block" ${ok ? "" : "disabled"} onclick="sendContract()">
      ${ok ? "Publier le contrat à mon équipe" : "La somme doit faire 40"}
    </button>
    <p class="tiny muted" style="margin:.6rem 0 0">
      La dernière version publiée fait foi.</p>
  </div>`;
}

async function sendContract() {
  if (await act("contract", { revenues: nums(S.draft.contract, ROLES) })) {
    toast("Contrat publié", true);
  }
}

/* Les intentions sont un outil de négociation, jamais une signature. */
function negotiation(n) {
  const rd = S.st.team.rounds[String(n)], me = S.st.me;
  const signals = rd.signals || {}, history = rd.history || [];
  const replaced = n === 3 && rd.resolution === "REPLACE";
  const excluded = replaced ? shockOf().target : null;
  const active = ROLES.filter((r) => r !== excluded);
  const ready = active.filter((r) => signals[r] === "READY").length;
  const canSignal = rd.contract && rd.resolution !== "ABANDON" && me.role !== excluded;
  const mine = signals[me.role];
  const readyLabel = n === 1 ? "Favorable" : "Prêt à signer";
  const discussLabel = n === 1 ? "Réservé" : "À renégocier";
  return `<section class="card negotiation">
    <div class="spread"><h3>Votre position publique</h3><span class="edition">${n === 1 ? "Accord imposé" : "Version " + rd.revision}</span></div>
    <p class="small muted">${n === 1 ? "Les parts sont imposées. Vous pouvez réagir à l’offre ; votre décision sera prise au vote secret." : rd.contract ? "Une intention, sans obligation. Une nouvelle version efface les intentions." : "Aucune proposition publiée pour le moment."}</p>
    <div class="readiness"><b>${ready}<small> / ${active.length}</small></b><span>${n === 1 ? "partenaires favorables" : "partenaires prêts à signer"}${replaced ? " · fournisseur de remplacement automatique" : ""}</span></div>
    ${canSignal ? `<div class="seg" style="margin-top:1rem">
      <button aria-pressed="${mine === "READY"}" onclick="sendSignal('READY')">${readyLabel}</button>
      <button aria-pressed="${mine === "DISCUSS"}" onclick="sendSignal('DISCUSS')">${discussLabel}</button>
      ${mine ? `<button class="ghost small" onclick="sendSignal('CLEAR')">Retirer</button>` : ""}
    </div>` : ""}
    <details class="signal-details"><summary>Les intentions autour de la table</summary><div class="signal-list">${ROLES.map((r) => `<div><b>${r}</b><span class="${signals[r] === "READY" ? "signal-ready" : signals[r] === "DISCUSS" ? "signal-discuss" : "muted"}">${r === excluded ? "Remplacé" : S.st.team.seats[r].bot ? "Siège automatique" : signals[r] === "READY" ? readyLabel : signals[r] === "DISCUSS" ? discussLabel : "Pas d’intention"}</span></div>`).join("")}</div></details>
    ${history.length ? `<details class="contract-history"><summary>Historique des propositions (${history.length})</summary>${history.slice().reverse().map((h) => `<div><b>V${h.revision}</b> ${Object.entries(h.contract).map(([r, v]) => esc(r) + " " + v).join(" · ")}${h.resolution ? `<span class="muted"> / ${esc(h.resolution)} · frais ${Object.entries(h.integration || {}).map(([r, v]) => esc(r) + " " + v).join(" · ")}</span>` : ""}</div>`).join("")}</details>` : ""}
  </section>`;
}

async function sendSignal(stance) {
  const rd = S.st.team.rounds[String(S.st.round)];
  if (await act("signal", { stance, revision: rd.revision })) toast("Intention mise à jour", true);
}

/* --- ROUND 3 : architecture ---------------------------------------------- */

function archTable() {
  return `<table>
    <thead><tr><th></th><th class="num">Intégrée</th><th class="num">Modulaire</th></tr></thead>
    <tbody>
      <tr><td>Valeur du service</td><td class="num mono">46</td><td class="num mono">40</td></tr>
      <tr><td>Coût collectif initial</td><td class="num mono">0</td><td class="num mono">6</td></tr>
      <tr><td>Interfaces</td><td class="num">Sur mesure</td><td class="num">Communes</td></tr>
      <tr><td>Remplacer un partenaire</td><td class="num">Difficile</td><td class="num">Plus simple</td></tr>
    </tbody></table>`;
}

function round3Arch() {
  const isMobi = S.st.me.role === "MOBI";
  const rd = S.st.team.rounds["3"];
  return `
  ${S.st.team.veto ? `<div class="card warn"><p style="margin:0">
    <b>FLEET a posé son veto.</b> L’architecture intégrée est écartée. Seule l’architecture modulaire reste disponible.</p></div>` : ""}
  <div class="card">
    <h3>Option A — intégrée / propriétaire</h3>
    <p class="small" style="margin:0 0 .6rem">Chaque partenaire développe une
    intégration optimisée pour les autres membres. Performance élevée, interfaces
    spécifiques, partenaire difficile à remplacer.</p>
    <h3>Option B — modulaire / standardisée</h3>
    <p class="small" style="margin:0 0 .8rem">API communes, formats standardisés,
    interfaces documentées. Pas de bonus de performance, mais un partenaire se
    remplace facilement.</p>
    ${archTable()}
  </div>
  ${isMobi ? archEditor(rd) : archView(rd)}
  <p class="table-note">Les conséquences d’un changement de l’environnement ne sont pas connues à ce stade.</p>`;
}

function archView(rd) {
  if (!rd.architecture) {
    return `<div class="card warn"><p style="margin:0">
      MOBI n'a pas encore verrouillé l'architecture.</p></div>`;
  }
  const std = rd.standard || {};
  return `<div class="card good">
    <h3>Architecture choisie</h3>
    <p style="font-size:1.3rem;font-weight:800;margin:0 0 .4rem">
      ${rd.architecture === "MODULAR" ? "MODULAIRE" : "INTÉGRÉE"}</p>
    ${rd.architecture === "MODULAR" ? `<table><tbody>
      ${ROLES.map((r) => `<tr class="${r === S.st.me.role ? "me" : ""}">
        <td><b>${r}</b></td><td class="num mono">−${std[r] || 0}</td></tr>`).join("")}
      <tr class="total"><td>Coût du standard</td><td class="num mono">6</td></tr>
    </tbody></table>` : ""}
  </div>`;
}

function archEditor(rd) {
  const a = S.draft.arch;
  const std = S.draft.std, total = sum(std);
  const ok = a === "PROPRIETARY" ? !S.st.team.veto : a === "MODULAR" && total === 6;
  return `<div class="card accent">
    <h3>Décision — vous êtes MOBI</h3>
    <div class="seg">
      <button aria-pressed="${a === "PROPRIETARY"}" ${S.st.team.veto ? "disabled" : ""} onclick="pickArch('PROPRIETARY')">
        INTÉGRÉE</button>
      <button aria-pressed="${a === "MODULAR"}" onclick="pickArch('MODULAR')">
        MODULAIRE</button>
    </div>
    ${a === "MODULAR" ? `
      <p class="small muted" style="margin:.8rem 0 .3rem">
        Coût du standard&nbsp;: 6 points, retirés quoi qu'il arrive ensuite.</p>
      <table><tbody>
        ${ROLES.map((r) => `<tr>
          <td><b>${r}</b></td>
          <td style="width:6.5rem"><input id="s_${r}" type="number" min="0" max="10"
            data-k="std.${r}" value="${std[r]}"></td></tr>`).join("")}
        <tr class="total"><td>TOTAL</td>
          <td class="num mono" style="color:${total === 6 ? "var(--good)" : "var(--bad)"}">
            ${total} / 6</td></tr>
      </tbody></table>` : ""}
    <div style="height:.7rem"></div>
    <button class="primary block" ${a && ok ? "" : "disabled"} onclick="sendArch()">
      ${!a ? "Choisissez une architecture"
           : ok ? "Publier l’architecture" : a === "PROPRIETARY" ? "FLEET a posé son veto" : "Les contributions doivent faire 6"}
    </button>
    ${rd.architecture ? `<p class="tiny muted" style="margin:.6rem 0 0">
      Actuellement enregistré : <b>${rd.architecture === "MODULAR" ? "modulaire" : "intégrée"}</b>.</p>` : ""}
  </div>`;
}

function pickArch(a) { S.draft.arch = a; render(); }

async function sendArch() {
  if (await act("architecture", {
    architecture: S.draft.arch, contributions: nums(S.draft.std, ROLES)
  })) toast("Architecture enregistrée", true);
}

/* --- ROUND 3 : choc ------------------------------------------------------ */

function shockCard(compact) {
  if (!S.st.shock) {
    return `<div class="card warn"><p style="margin:0">
      Le tirage est en cours. Regardez l'écran.</p></div>`;
  }
  const sh = shockOf();
  return `<div class="card bad">
    <h3 style="color:var(--bad)">${sh.title}</h3>
    <p ${compact ? 'class="small"' : ""} style="margin:0 0 .6rem">${sh.lines[0]}</p>
    ${compact ? `<details><summary>Les conditions connues</summary><ul class="small">${sh.lines.slice(1).map((x) => `<li>${x}</li>`).join("")}</ul></details>` : '<p class="small muted">L’annonce concerne tous les écosystèmes. Prenez connaissance de la situation autour de votre table.</p>'}
  </div>`;
}

/* --- ROUND 3 : renegociation --------------------------------------------- */

function r3Value(arch, res) {
  if (res === "ABANDON") return 0;
  const base = arch === "PROPRIETARY" ? 46 : 40;
  if (shockOf().delay.indexOf(res) >= 0) {
    return base - (arch === "PROPRIETARY" ? 12 : 0);
  }
  return base;
}

function round3Nego() {
  const rd = S.st.team.rounds["3"];
  const isMobi = S.st.me.role === "MOBI";
  const arch = rd.architecture || "PROPRIETARY";
  const sh = shockOf();
  const rows = sh.options.map((o) => {
    if (o === "ABANDON") {
      return `<tr><td>Abandonner</td><td class="num mono">valeur 0</td>
        <td class="num mono muted">option extérieure</td></tr>`;
    }
    const label = o === "KEEP" ? sh.keepLabel : sh.replaceLabel;
    const need = adaptNeed(arch, o);
    const note = (o === "KEEP" && S.st.shock === "AI_FAILURE")
      ? "BRAIN paie 6" : "adaptation " + need;
    return `<tr><td>${label}</td>
      <td class="num mono">valeur ${r3Value(arch, o)}</td>
      <td class="num mono muted">${note}</td></tr>`;
  }).join("");
  return `
  ${shockCard(true)}
  <details class="option-rules">
    <summary>Conditions de révision · architecture ${arch === "MODULAR" ? "modulaire" : "intégrée"}</summary>
    <table><tbody>${rows}</tbody></table>
    ${(S.st.team.powers || {}).GRID ? `<p class="tiny" style="margin:.6rem 0 0;color:var(--good)">
      GRID a activé STANDARD READY : le coût d'adaptation est réduit de 2 points.</p>` : ""}
  </details>
  ${isMobi ? resolutionEditor(rd, arch) : resolutionView(rd)}
  ${negotiation(3)}
  ${gameRules()}`;
}

function resolutionView(rd) {
  if (!rd.resolution) {
    return `<div class="card warn"><p style="margin:0">
      MOBI n'a pas encore déposé de solution.</p></div>`;
  }
  if (rd.resolution === "ABANDON") {
    return `<div class="card bad"><h3>Solution retenue</h3>
      <p style="margin:0"><b>ABANDON.</b> L'écosystème renonce au projet.</p></div>`;
  }
  const sh = shockOf();
  const keys = rd.resolution === "KEEP" ? ROLES : payers().concat("ALT_AI");
  const title = rd.resolution === "KEEP" ? sh.keepLabel : sh.replaceLabel;
  return `<div class="card">
    <h3>Solution retenue — ${title.toLowerCase()}</h3>
    <table><tbody>
      ${keys.map((r) => `<tr class="${r === S.st.me.role ? "me" : ""}">
        <td><b>${r === "ALT_AI" ? sh.alt : r}</b></td>
        <td class="num mono">${(rd.contract || {})[r]}</td>
        <td class="num mono muted">${(rd.integration || {})[r]
          ? "−" + rd.integration[r] : ""}</td></tr>`).join("")}
      <tr class="total"><td>TOTAL</td>
        <td class="num mono">${sum(rd.contract)}</td><td></td></tr>
    </tbody></table>
  </div>`;
}

function resolutionEditor(rd, arch) {
  const res = S.draft.res;
  const sh = shockOf();
  const pay = payers();
  const keys = res === "REPLACE" ? pay.concat("ALT_AI") : ROLES;
  const need = r3Value(arch, res || sh.options[0]);
  const rev = S.draft.r3rev, total = keys.reduce((a, k) => a + (Number(rev[k]) || 0), 0);
  const integ = S.draft.integ;
  const integNeed = adaptNeed(arch, res || sh.options[0]);
  const integTotal = pay.reduce((a, k) => a + (Number(integ[k]) || 0), 0);

  let ok = false;
  if (res === "ABANDON") ok = true;
  else if (res) {
    ok = total === need && integTotal === integNeed &&
      (res !== "REPLACE" || (Number(rev.ALT_AI) || 0) >= 8);
  }

  const label = { KEEP: sh.keepLabel, REPLACE: sh.replaceLabel, ABANDON: "Abandonner" };
  return `<div class="card accent">
    <h3>Solution — vous êtes MOBI</h3>
    <div class="seg">
      ${sh.options.map((o) => `<button aria-pressed="${res === o}"
        onclick="pickRes('${o}')">${label[o]}</button>`).join("")}
    </div>
    ${!res ? "" : res === "ABANDON" ? `
      <p class="small" style="margin:.9rem 0 0">Chacun repart sur son option
      extérieure. Les contributions déjà versées au standard restent perdues.</p>`
      : `
      <p class="small muted" style="margin:.9rem 0 .3rem">
        Répartissez les <b>${need}</b> points de revenu.
        ${res === "REPLACE" ? sh.alt + " refuse en dessous de 8."
          : S.st.shock === "AI_FAILURE" ? "BRAIN paiera 6 points de mise en conformité." : ""}</p>
      <table><tbody>
        ${keys.map((r) => `<tr>
          <td><b>${r === "ALT_AI" ? shockOf().alt : r}</b></td>
          <td style="width:6.5rem"><input id="r_${r}" type="number" min="0" max="46"
            data-k="r3rev.${r}" value="${rev[r]}"></td></tr>`).join("")}
        <tr class="total"><td>TOTAL</td>
          <td class="num mono" style="color:${total === need ? "var(--good)" : "var(--bad)"}">
            ${total} / ${need}</td></tr>
      </tbody></table>
      ${integNeed ? `
        <p class="small muted" style="margin:.9rem 0 .3rem">
          Répartissez le coût d'adaptation (${integNeed} points)
          ${res === "REPLACE" ? "— intégration de " + sh.alt : "— mise en conformité"}.</p>
        <table><tbody>
          ${pay.map((r) => `<tr>
            <td><b>${r}</b></td>
            <td style="width:6.5rem"><input id="i_${r}" type="number" min="0" max="10"
              data-k="integ.${r}" value="${integ[r]}"></td></tr>`).join("")}
          <tr class="total"><td>TOTAL</td>
            <td class="num mono" style="color:${integTotal === integNeed ? "var(--good)" : "var(--bad)"}">
              ${integTotal} / ${integNeed}</td></tr>
        </tbody></table>` : ""}`}
    <div style="height:.7rem"></div>
    <button class="primary block" ${ok ? "" : "disabled"} onclick="sendResolution()">
      Publier la solution</button>
    ${rd.resolution ? `<p class="tiny muted" style="margin:.6rem 0 0">
      Actuellement enregistré : <b>${esc(label[rd.resolution] || rd.resolution)}</b>.</p>` : ""}
  </div>`;
}

function pickRes(r) { S.draft.res = r; render(); }

async function sendResolution() {
  if (await act("resolution", {
    resolution: S.draft.res,
    revenues: nums(S.draft.r3rev, ROLES.concat("ALT_AI")),
    integration: nums(S.draft.integ, ROLES)   // le serveur ne retient que les payeurs
  })) toast("Solution publiée", true);
}

/* --- decisions ----------------------------------------------------------- */

function decide(n) {
  const rd = S.st.team.rounds[String(n)];
  const me = S.st.me;
  const mine = me.decision;
  const expected = votingRoles(S.st.team, n, S.st.shock);
  const received = expected.filter((r) => rd.answered_roles.includes(r)).length;

  if (n === 3 && rd.resolution === "ABANDON") {
    return `<div class="card bad center"><h2>Projet abandonné</h2>
      <p style="margin:0">Votre écosystème a renoncé. Aucune décision à prendre.</p></div>`;
  }
  if (n === 3 && rd.resolution === "REPLACE" && me.role === shockOf().target) {
    return `${calculator(3)}
      <div class="card warn center"><h2>Vous êtes hors de l'écosystème</h2>
      <p style="margin:0">${shockOf().alt} occupe votre position. Vous n'avez pas de décision
      à prendre ce round.</p></div>`;
  }

  // filet de securite : MOBI n'a rien publie avant l'ouverture des votes
  const late = me.role === "MOBI" && ((n === 2 && !rd.contract) ||
                                      (n === 3 && !rd.resolution));
  return `
  ${late ? `<div class="card warn"><p style="margin:0">Vous n'avez encore rien
    déposé.</p></div>` : ""}
  ${n === 1 ? contractView(rd, true) : ""}
  ${n === 2 ? (late ? contractEditor() : contractView(rd)) : ""}
  ${n === 3 ? (late ? resolutionEditor(rd, rd.architecture || "PROPRIETARY")
                    : resolutionView(rd)) : ""}
  <div class="card accent">
    <h3>Votre décision</h3>
    <p class="small muted" style="margin:-.2rem 0 .8rem">
      Les partenaires nécessaires doivent tous participer pour que le service existe. Sans réponse à la clôture : retrait.</p>
    <div class="choice-pair">
      <button class="join" aria-pressed="${mine === "JOIN"}" ${mine === "JOIN" || !rd.contract ? "disabled" : ""}
        onclick="sendDecision('JOIN')">Je participe<span>JOIN</span></button>
      <button class="out" aria-pressed="${mine === "OUT"}" ${mine === "OUT" || !rd.contract ? "disabled" : ""}
        onclick="sendDecision('OUT')">Je me retire<span>OUT</span></button>
    </div>
    <p class="center" style="margin:.9rem 0 0">${
      mine ? `Votre choix : <b style="color:${mine === "JOIN" ? "var(--good)" : "var(--bad)"}">${mine}</b>`
           : '<span class="muted">Aucun choix enregistré</span>'}</p>
  </div>
  ${calculator(n)}
  ${gameRules()}
  <div class="card tight">
    <h3>Où en est l'équipe</h3>
    <div class="row wrapped">
      ${ROLES.map((r) => `<span class="pill ${
        rd.answered_roles.includes(r) ? "join" : "wait"}">${r} ${
        !expected.includes(r) ? "auto / sans vote" : rd.answered_roles.includes(r) ? "✓" : "…"}</span>`).join("")}
    </div>
    <p class="tiny muted" style="margin:.6rem 0 0">
      ${received} / ${expected.length} réponses humaines reçues. Les automates sont calculés à la clôture.</p>
  </div>`;
}

async function sendDecision(choice) {
  if (await act("decide", { choice })) toast("Décision enregistrée : " + choice, true);
}

/* --- resultats ----------------------------------------------------------- */

function results(n) {
  const rd = S.st.team.rounds[String(n)];
  const res = rd.result;
  const me = S.st.me;
  if (!res) {
    return `<div class="card center"><p style="margin:0" class="muted">
      Résultats en cours de calcul…</p></div>`;
  }
  const myScore = res.scores[me.role];
  const abandoned = res.abandoned;

  return `
  <div class="banner ${res.success ? "ok" : "fail"}">
    ${res.success ? "Service lancé — proposition de valeur produite"
      : abandoned ? "Projet abandonné"
      : "Le service n’a pas été lancé"}
  </div>
  <div class="card center" style="margin-top:1rem">
    <p class="muted small" style="margin:0">Votre score au round ${n}</p>
    <b class="mono" style="font-size:3rem;line-height:1.1">${myScore}</b>
  </div>
  <div class="card">
    <h3>Écosystème ${esc(S.st.team.team)}</h3>
    <table>
      <thead><tr><th>Acteur</th><th>Choix</th><th class="num">Revenu</th>
        <th class="num">Score</th></tr></thead>
      <tbody>
        ${ROLES.map((r) => {
          const d = (rd.decisions || {})[r];
          const rev = n === 1 ? R1_REVENUE[r] : (rd.contract || {})[r];
          const ejected = n === 3 && rd.resolution === "REPLACE" && r === shockOf().target;
          return `<tr class="${r === me.role ? "me" : ""}">
            <td><b>${r}</b></td>
            <td>${ejected ? '<span class="pill">remplacé</span>'
              : d ? `<span class="pill ${d === "JOIN" ? "join" : "out"}">${d}</span>`
              : '<span class="pill wait">—</span>'}</td>
            <td class="num mono">${res.success && !ejected && rev != null ? rev : "—"}</td>
            <td class="num mono">${res.scores[r]}</td></tr>`;
        }).join("")}
        ${n === 3 && rd.resolution === "REPLACE" ? `<tr>
          <td><b>${shockOf().alt}</b></td><td><span class="pill join">JOIN</span></td>
          <td class="num mono">${(rd.contract || {}).ALT_AI}</td>
          <td class="num mono muted">—</td></tr>` : ""}
      </tbody>
    </table>
  </div>
  <div class="kpi">
    <div><b class="mono">${res.value}</b><span>Valeur créée</span></div>
    <div><b class="mono">${signed(res.ecosystem)}</b><span>Score collectif</span></div>
  </div>
  ${!res.success && !abandoned ? `<div class="card tight small muted"
    style="margin-top:1rem">Le service n'existe pas sans les cinq acteurs.</div>` : ""}`;
}

/* --- fin de partie ------------------------------------------------------- */

const BADGES = {
  HOLD_UP:        ["\uD83C\uDFAF", "HOLD-UP",
                   "BRAIN a capté au moins 30 % des 40 points du round 2."],
  FAILED_BARGAIN: ["\uD83D\uDCB8", "FAILED BARGAIN",
                   "L'écosystème était collectivement rentable, mais un acteur est sorti."],
  POACHED:        ["\uD83C\uDFF4", "POACHED",
                   "Votre BRAIN est parti pour un autre écosystème."],
  LOCK_IN:        ["\uD83D\uDD12", "LOCK-IN",
                   "Votre architecture a rendu l'adaptation plus coûteuse qu'en modulaire."],
  RESILIENT:      ["\uD83D\uDEE1", "RESILIENT ECOSYSTEM",
                   "Architecture modulaire : vous avez encaissé le choc."]
};

function badgeList(keys, compact) {
  if (!keys || !keys.length) return "";
  return keys.map((k) => {
    const b = BADGES[k];
    if (!b) return "";
    if (compact) return `<span class="pill" title="${esc(b[2])}">${b[1]}</span>`;
    return `<div class="card tight" style="margin:.5rem 0 0">
      <b>${b[1]}</b>
      <p class="small muted" style="margin:.2rem 0 0">${esc(b[2])}</p></div>`;
  }).join("");
}

function final() {
  const t = S.st.totals, mine = S.st.my_total;
  const myBadges = (mine && mine.badges) || [];
  const rank = t.players.findIndex((p) =>
    p.name === S.st.me.name && p.team === S.st.me.team && p.role === S.st.me.role) + 1;
  const ecos = Object.entries(t.eco).sort((a, b) => b[1].total - a[1].total);

  return `
  <div class="card accent center">
    <p class="muted small" style="margin:0">Votre score total</p>
    <b class="mono" style="font-size:3.2rem;line-height:1.1">${mine ? mine.total : "—"}</b>
    <p class="muted small" style="margin:.2rem 0 0">${rank}<sup>e</sup> sur ${t.players.length}</p>
  </div>
  ${mine ? `<div class="card tight"><table>
    <thead><tr><th>Round</th><th class="num">Score</th></tr></thead>
    <tbody>${["1", "2", "3"].map((n) => `<tr><td>Round ${n}</td>
      <td class="num mono">${mine.rounds[n] == null ? "—" : mine.rounds[n]}</td></tr>`).join("")}
      ${mine.adjust ? `<tr><td>Pouvoirs et marché</td>
        <td class="num mono">${signed(mine.adjust)}</td></tr>` : ""}
      <tr class="total"><td>TOTAL</td><td class="num mono">${mine.total}</td></tr>
    </tbody></table></div>` : ""}

  ${myBadges.length ? `<div class="card">
    <h3>Vos badges</h3>
    <p class="tiny muted" style="margin:0">Purement pédagogiques : aucun effet sur les scores.</p>
    ${badgeList(myBadges, false)}
  </div>` : ""}

  <div class="card">
    <h3>Meilleures entreprises</h3>
    <table><tbody>
      ${t.players.slice(0, 8).map((p, i) => `<tr class="${
        p.name === S.st.me.name && p.team === S.st.me.team ? "me" : ""}">
        <td style="width:1.6rem" class="muted">${i + 1}</td>
        <td>${esc(p.name)}</td>
        <td class="small muted">${p.role} · ${p.team}</td>
        <td class="small">${badgeList(p.badges, true)}</td>
        <td class="num mono">${p.total}</td></tr>`).join("")}
    </tbody></table>
  </div>

  <div class="card">
    <h3>Meilleurs écosystèmes</h3>
    <table><tbody>
      ${ecos.map(([name, e], i) => `<tr class="${name === S.st.me.team ? "me" : ""}">
        <td style="width:1.6rem" class="muted">${i + 1}</td>
        <td><b style="color:${COLORS[name]}">${name}</b></td>
        <td class="small muted">${e.architecture === "MODULAR" ? "modulaire"
          : e.architecture === "PROPRIETARY" ? "propriétaire" : "—"}</td>
        <td class="small">${badgeList((e.badges || []).map((b) => b.key), true)}</td>
        <td class="num mono">${signed(e.total)}</td></tr>`).join("")}
    </tbody></table>
    <p class="tiny muted" style="margin:.6rem 0 0">
      Valeur collective créée = valeur du service − coûts engagés.</p>
  </div>`;
}

function debrief() {
  return `<div class="card accent center">
    <h2>Débrief</h2>
    <p style="margin:0">Regardez l'écran.</p>
  </div>${final()}`;
}

/* --- brouillons ---------------------------------------------------------- */

function seedDrafts() {
  const d = S.draft, st = S.st;
  const r2 = st.team.rounds["2"] || {}, r3 = st.team.rounds["3"] || {};

  if (!d.contract) d.contract = Object.fromEntries(ROLES.map((r) => [r, 0]));
  if (!d.std) d.std = Object.fromEntries(ROLES.map((r) => [r, 0]));
  if (!d.r3rev) d.r3rev = Object.fromEntries(
    ROLES.concat("ALT_AI").map((r) => [r, 0]));
  if (!d.integ) d.integ = Object.fromEntries(ROLES.map((r) => [r, 0]));

  // recopie une fois ce qui a deja ete publie par le serveur
  if (r2.contract && !S.seeded.contract) {
    d.contract = Object.assign({}, r2.contract);
    S.seeded.contract = true;
  }
  if (r3.architecture && !S.seeded.arch) {
    d.arch = r3.architecture;
    d.std = Object.assign(d.std, r3.standard || {});
    S.seeded.arch = true;
  }
  if (r3.resolution && !S.seeded.res) {
    d.res = r3.resolution;
    d.r3rev = Object.assign(d.r3rev, r3.contract || {});
    d.integ = Object.assign(d.integ, r3.integration || {});
    S.seeded.res = true;
  }
}

/* Les champs numeriques gardent la chaine saisie telle quelle (un champ vide
   doit rester vide) ; la conversion en entiers n'a lieu qu'a l'envoi. */
function nums(obj, keys) {
  const out = {};
  keys.forEach((k) => { out[k] = Math.max(0, parseInt(obj[k], 10) || 0); });
  return out;
}

document.addEventListener("input", (ev) => {
  if (S.identityDraft && ev.target.id === "identityFirst") S.identityDraft.first_name = ev.target.value;
  if (S.identityDraft && ev.target.id === "identityLast") S.identityDraft.last_name = ev.target.value;
  const k = ev.target.getAttribute && ev.target.getAttribute("data-k");
  if (!k) return;
  const parts = k.split(".");
  if (parts.length === 2) {
    S.draft[parts[0]][parts[1]] = ev.target.value.replace(/[^0-9]/g, "");
    render();                       // met a jour les totaux, focus preserve
  } else {
    S.draft[k] = ev.target.value;
  }
});

/* --- demarrage ----------------------------------------------------------- */

$("gojoin").addEventListener("click", doJoin);
$("pname").addEventListener("keydown", (e) => {
  if (e.key === "Enter") $("plastname").focus();
});
$("plastname").addEventListener("keydown", (e) => {
  if (e.key === "Enter") $("pcode").focus();
});
$("pcode").addEventListener("keydown", (e) => { if (e.key === "Enter") doJoin(); });

// le code arrive par le QR (?c=ABCD) ; sinon il est saisi a la main
const urlCode = new URLSearchParams(location.search).get("c");
$("pcode").value = (urlCode || localStorage.getItem("eco_code") || "").toUpperCase();

S.token = localStorage.getItem("eco_token");
if (S.token) start(); else $("pname").focus();

window.sendClaim = sendClaim;
window.sendContract = sendContract;
window.sendDecision = sendDecision;
window.pickArch = pickArch;
window.sendArch = sendArch;
window.pickRes = pickRes;
window.sendResolution = sendResolution;
window.usePower = usePower;
window.answerExclusivity = answerExclusivity;
window.sendOffer = sendOffer;
window.sendMarket = sendMarket;
window.chooseTab = chooseTab;
