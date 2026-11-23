/* ECOSYSTEM — tableau de bord enseignant */
"use strict";

const ROLES = ["MOBI", "AUTO", "BRAIN", "GRID", "FLEET"];
const COLORS = {
  BLUE: "#8dbdd8", GREEN: "#a4cfb7", RED: "#e3a79c",
  YELLOW: "#dfc58c", PURPLE: "#bcafd6", ORANGE: "#ddba94"
};
const R1_REVENUE = { MOBI: 14, AUTO: 10, BRAIN: 6, GRID: 6, FLEET: 4 };

const KEY = new URLSearchParams(location.search).get("cle") || "";
const H = { st: null, version: 0, offset: 0, tab: "board" };

const $ = (id) => document.getElementById(id);
const esc = (s) => String(s == null ? "" : s).replace(/[&<>"']/g,
  (c) => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" }[c]));
const sleep = (ms) => new Promise((r) => setTimeout(r, ms));
const sum = (o) => Object.values(o || {}).reduce((a, b) => a + (Number(b) || 0), 0);
const signed = (n) => (n == null ? "—" : n > 0 ? "+" + n : String(n));

function toast(msg, ok) {
  const t = document.createElement("div");
  t.className = "toast" + (ok ? " ok" : "");
  t.textContent = msg;
  document.body.appendChild(t);
  setTimeout(() => t.remove(), 3500);
}

async function host(action, extra) {
  try {
    const r = await fetch("/api/host/action", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(Object.assign({ cle: KEY, action }, extra || {}))
    });
    const d = await r.json().catch(() => ({}));
    if (!r.ok) throw new Error(d.error || "Erreur");
    return true;
  } catch (e) { toast(e.message); return false; }
}

function manageStudents() {
  setTab("players");
  $("roster")?.scrollIntoView({ block: "start" });
}

async function requestIdentity() {
  if (!H.st?.players.length) return toast("Aucun étudiant connecté pour le moment.");
  if (await host("request_identity")) toast("Demande de nom et prénom envoyée à tous les étudiants", true);
}

async function removeStudent(id) {
  const p = H.st?.players.find((p) => p.id === id);
  if (!p || !confirm(`Retirer ${p.name} de la partie ? Son accès sera déconnecté.`)) return;
  if (await host("remove", { player: id })) toast(`${p.name} a été retiré de la partie`, true);
}

/* --- synchronisation ----------------------------------------------------- */

async function poll() {
  for (;;) {
    try {
      const r = await fetch("/api/host?cle=" + encodeURIComponent(KEY) +
                            "&since=" + H.version);
      if (r.status === 403) {
        document.body.innerHTML =
          '<div class="wrap" style="padding-top:3rem"><h1>Clé enseignant invalide</h1>' +
          "<p class=muted>Utilisez le lien affiché dans la console au démarrage " +
          "du serveur.</p></div>";
        return;
      }
      if (!r.ok) throw new Error("http " + r.status);
      const st = await r.json();
      $("offline").hidden = true;
      H.offset = st.server_time * 1000 - Date.now();
      H.st = st;
      H.version = st.version;
      render();
    } catch (e) {
      $("offline").hidden = false;
      await sleep(1500);
    }
  }
}

/* --- chrono -------------------------------------------------------------- */

function remaining() {
  const t = H.st && H.st.timer;
  if (!t || t.remaining == null) return null;
  if (!t.running || !t.ends_at) return t.remaining;
  return Math.round(t.ends_at - (Date.now() + H.offset) / 1000);
}

function tick() {
  const box = $("timer");
  const r = remaining();
  if (r == null) { box.textContent = "—"; box.className = "timer"; return; }
  const neg = r < 0, a = Math.abs(r);
  box.textContent = (neg ? "-" : "") +
    String(Math.floor(a / 60)).padStart(2, "0") + ":" +
    String(a % 60).padStart(2, "0");
  box.className = "timer" + (r <= 0 ? " over" : r <= 30 ? " low" : "");
}
setInterval(tick, 250);

function toggleTimer() {
  host(H.st && H.st.timer.running ? "timer_pause" : "timer_start");
}

/* --- rendu --------------------------------------------------------------- */

function setTab(t) {
  H.tab = t;
  ["board", "players", "final", "brief"].forEach((k) =>
    $("tab-" + k).setAttribute("aria-pressed", String(k === t)));
  render();
}

const SHOCK_LABEL = {
  AI_FAILURE: "AI FAILURE — BRAIN indisponible",
  INFRA_FAILURE: "INFRA FAILURE — GRID indisponible",
  REGULATION: "NEW REGULATION — mise en conformité"
};

const BADGES = {
  HOLD_UP:        ["\uD83C\uDFAF", "HOLD-UP"],
  FAILED_BARGAIN: ["\uD83D\uDCB8", "FAILED BARGAIN"],
  POACHED:        ["\uD83C\uDFF4", "POACHED"],
  LOCK_IN:        ["\uD83D\uDD12", "LOCK-IN"],
  RESILIENT:      ["\uD83D\uDEE1", "RESILIENT ECOSYSTEM"]
};

function badgePills(list) {
  return (list || []).map((b) => {
    const d = BADGES[b.key || b];
    if (!d) return "";
    return `<span class="pill" title="${esc(b.text || "")}">${d[1]}</span>`;
  }).join(" ");
}

function roundOf(phase) {
  if (phase.startsWith("R1")) return 1;
  if (phase.startsWith("R2")) return 2;
  if (phase.startsWith("R3")) return 3;
  return null;
}

function render() {
  const st = H.st;
  if (!st) return;

  $("code").textContent = st.code;
  $("nplayers").textContent = st.players.length;
  $("phase").textContent = st.phase_label;
  $("btnplay").textContent = st.timer.running ? "⏸" : "▶";
  tick();

  // l'adresse a projeter est celle du tunnel s'il y en a un, sinon celle-ci
  const base = (st.join_base || location.origin).replace(/\/+$/, "");
  const url = base + "/?c=" + st.code;
  if ($("joinurl").textContent !== base) {
    $("joinurl").textContent = base;
    $("qr").src = "/qr.svg?d=" + encodeURIComponent(url);
  }

  const sel = $("phasesel");
  if (sel.options.length !== st.phases.length) {
    sel.innerHTML = st.phases.map((p) =>
      `<option value="${p.key}">${esc(p.label)}</option>`).join("");
    sel.onchange = () => host("phase", { phase: sel.value });
  }
  sel.value = st.phase;

  const a = document.activeElement;
  const keep = a && a.id && $("view").contains(a) ? a.id : null;
  replacePanel($("view"),
    H.tab === "board" ? board() :
    H.tab === "players" ? players() :
    H.tab === "final" ? final() : brief());
  if (keep && $(keep)) $(keep).focus();
}

/* --- onglet ECOSYSTEMES -------------------------------------------------- */

function board() {
  const st = H.st;
  const n = roundOf(st.phase);
  const names = Object.keys(st.teams);
  return `
    ${sessionRail(st.phase)}
    ${sessionPulse()}
    ${notes()}
    ${marketPanel()}
    ${shockPanel()}
    <div class="teams-grid">
      ${names.map((t) => teamCard(t, n)).join("")}
    </div>`;
}

function sessionPulse() {
  const st = H.st, n = roundOf(st.phase), teams = Object.values(st.teams);
  const rds = n ? teams.map((t) => t.rounds[String(n)]) : [];
  const voting = st.phase.endsWith("_DECIDE");
  const plans = st.phase === "R3_ARCH" ? teams.filter((t) => t.rounds["3"].architecture).length
    : rds.filter((r) => r.contract || r.resolution === "ABANDON").length;
  const expected = n ? teams.reduce((v, t) => v + votingRoles(t, n, st.shock).length, 0) : 0;
  const received = n ? teams.reduce((v, t) => v + votingRoles(t, n, st.shock).filter((r) => t.rounds[String(n)].answered_roles.includes(r)).length, 0) : 0;
  return `<section class="session-pulse">
    <div><span class="edition">La table</span><b>${st.players.length}<small> joueurs</small></b></div>
    <div><span class="edition">${st.phase === "R3_ARCH" ? "Architectures" : "Accords publiés"}</span><b>${plans}<small> / ${teams.length} équipes</small></b></div>
    <div><span class="edition">${voting ? "Votes reçus" : "Intentions favorables"}</span><b>${voting ? received : rds.reduce((v, r) => v + (r.ready_count || 0), 0)}<small> ${voting ? "/ " + expected + " · choix secrets" : "· non contraignantes"}</small></b></div>
    <p>${voting ? "Attendez les réponses avant de révéler. Les sièges automatiques sont calculés à la clôture." : "Une proposition n’est pas un accord. Cherchez les points de blocage avant de passer au vote."}</p>
  </section>`;
}

/* --- marche des ecosystemes ---------------------------------------------- */

function marketPanel() {
  const st = H.st, mk = st.market || {};
  const idx = st.phases.findIndex((x) => x.key === st.phase);
  const mIdx = st.phases.findIndex((x) => x.key === "MARKET");
  if (idx < mIdx) return "";

  if (st.phase === "MARKET") {
    // en cours : ni les offres ni les decisions ne doivent transparaitre
    return `<div class="card" style="margin:0 1rem 1rem">
      <h2>Marché des écosystèmes — en cours</h2>
      <p style="margin:0">${mk.offer_count || 0} offre(s) déposée(s) ·
        ${(mk.answered || []).length} BRAIN ont répondu sur ${Object.keys(st.teams).length}.</p>
      <p class="muted" style="margin:.4rem 0 0">Les montants et les décisions
        restent privés jusqu'à la clôture. Passez à la phase suivante pour révéler.</p>
    </div>`;
  }
  if (!mk.resolved) return "";
  return `<div class="card" style="margin:0 1rem 1rem">
    <h2>Marché des écosystèmes — résultat</h2>
    ${mk.moves && mk.moves.length ? `<ul class="big-list" style="margin:.4rem 0 0;padding-left:1.2rem">
      ${mk.moves.map((m) => `<li><b style="color:${COLORS[m.from]}">BRAIN ${m.from}</b>
        → <b style="color:${COLORS[m.to]}">ÉCOSYSTÈME ${m.to}</b>
        <span class="muted">(${m.price} pts d'offre, ${2} pts de changement)</span></li>`).join("")}
    </ul>` : `<p style="margin:0">Aucun transfert : tous les BRAIN sont restés.</p>`}
    ${mk.voided && mk.voided.length ? `<p class="muted" style="margin:.5rem 0 0">
      Départ annulé faute de siège libre : ${mk.voided.join(", ")}.</p>` : ""}
  </div>`;
}

/* --- choc tire au sort ---------------------------------------------------- */

function shockPanel() {
  const st = H.st;
  if (st.phase === "R3_ARCH") {
    return `<div class="card" style="margin:0 1rem 1rem">
      <h2>Choc — pas encore tiré</h2>
      <p style="margin:0">Trois chocs sont possibles. Le serveur en tire un pour
        toute la classe au passage en <b>Ecosystem shock</b>.</p>
      <p class="muted" style="margin:.4rem 0 0">N'annoncez ni lequel, ni les probabilités.</p>
    </div>`;
  }
  const idx = st.phases.findIndex((x) => x.key === st.phase);
  if (idx < st.phases.findIndex((x) => x.key === "R3_SHOCK")) return "";
  return `<div class="card" style="margin:0 1rem 1rem">
    <h2>Choc de la classe</h2>
    <p style="margin:0;font-size:1.3rem;font-weight:800">
      ${st.shock ? esc(SHOCK_LABEL[st.shock] || st.shock) : "—"}</p>
    ${st.phase === "R3_SHOCK" ? `<div class="row" style="margin-top:.7rem">
      ${(st.shocks || []).map((sh) => `<button
        onclick="host('shock', { shock: '${sh.key}' })">Imposer ${esc(sh.label)}</button>`).join("")}
    </div>
    <p class="muted" style="margin:.4rem 0 0">Utile pour rejouer une séance à l'identique.</p>` : ""}
  </div>`;
}

function teamCard(name, n) {
  const st = H.st, t = st.teams[name];
  const rd = n ? t.rounds[String(n)] : null;
  const res = rd && rd.result;
  const decidePhase = st.phase.endsWith("_DECIDE");
  const showChoices = rd && (rd.locked || st.phase === "FINAL" || st.phase === "DEBRIEF");
  const replaced = n === 3 && rd && rd.resolution === "REPLACE";
  const target = { AI_FAILURE: "BRAIN", INFRA_FAILURE: "GRID" }[st.shock] || "BRAIN";
  const altName = st.shock === "INFRA_FAILURE" ? "ALT-INFRA" : "ALT-AI";
  const powers = st.powers ? (st.powers[name] || {}) : {};
  const expected = votingRoles(t, n, st.shock);
  const received = rd ? expected.filter((r) => rd.answered_roles.includes(r)).length : 0;

  let status = "";
  if (res) {
    status = `<div class="banner ${res.success ? "ok" : "fail"}" style="margin:.7rem 0 0">
      ${res.success ? "Service lancé"
        : res.abandoned ? "Projet abandonné" : "Value proposition not delivered"}
    </div>
    <div class="kpi" style="margin-top:.6rem">
      <div><b class="mono">${res.value}</b><span>Valeur</span></div>
      <div><b class="mono">${signed(res.ecosystem)}</b><span>Score collectif</span></div>
    </div>`;
  } else if (decidePhase && rd) {
    status = `<div class="banner ${received === expected.length ? "ok" : "fail"}"
      style="margin:.7rem 0 0;background:transparent;color:var(--muted);border-color:var(--line)">
      ${received} / ${expected.length} réponses humaines reçues</div>`;
  }

  return `<section class="team-card" style="--team:${COLORS[name]}">
    <header><span>${name}</span>
      <span class="mono" style="font-size:.85rem">${teamHeadInfo(t, n)}</span>
    </header>
    <div class="body">
      ${ROLES.map((r) => {
        const seat = t.seats[r];
        const d = showChoices ? (rd.decisions || {})[r] : null;
        const answered = rd && rd.answered_roles.includes(r);
        const ejected = replaced && r === target;
        const rev = n === 1 ? R1_REVENUE[r]
          : (rd && rd.contract ? rd.contract[r] : null);
        let pill = '<span class="pill wait">…</span>';
        if (ejected) pill = `<span class="pill">${altName}</span>`;
        else if (d) pill = `<span class="pill ${d === "JOIN" ? "join" : "out"}">${
          d === "JOIN" ? "JOIN" : "OUT"}</span>`;
        else if (answered) pill = '<span class="pill wait">répondu</span>';
        else if (!rd) pill = "";
        return `<div class="seat">
          <span class="rname">${r}${powers[r] ? ' <span title="pouvoir activé">*</span>' : ""}</span>
          <span class="pname">${seat.bot
            ? '<span class="pill bot">auto</span>'
            : esc(seat.names.join(", "))}</span>
          <span class="rev mono">${rev == null || ejected ? "" : rev}</span>
          ${pill}
        </div>`;
      }).join("")}
      ${replaced ? `<div class="seat"><span class="rname">${altName}</span>
        <span class="pname muted">fournisseur de remplacement</span>
        <span class="rev mono">${(rd.contract || {}).ALT_AI}</span>
        <span class="pill join">JOIN</span></div>` : ""}
      ${res ? `<table style="margin-top:.5rem"><tbody>
        ${ROLES.map((r) => `<tr><td>${r}</td>
          <td class="num mono">${res.scores[r]}</td></tr>`).join("")}
      </tbody></table>` : ""}
      ${rd && !res && st.phase.endsWith("_NEGO") ? `<div class="team-progress"><span>${n === 1 ? "Offre imposée" : "V" + (rd.revision || 0)} · ${rd.ready_count || 0} ${n === 1 ? "favorables" : "prêts"} · ${rd.discuss_count || 0} ${n === 1 ? "réservés" : "à renégocier"}</span><div class="agreement-track"><i style="width:${(rd.ready_count || 0) * 100 / (replaced ? 4 : 5)}%"></i></div></div>` : ""}
      ${Object.keys(powers).length ? `<p class="muted" style="margin:.5rem 0 0;font-size:.85rem">
        Pouvoirs : ${Object.entries(powers).map(([r, v]) =>
          `${r} · ${esc(v.name)}`).join(" — ")}</p>` : ""}
      ${t.lost_brain ? `<p class="muted" style="margin:.3rem 0 0;font-size:.85rem">
        BRAIN parti au marché</p>` : ""}
      ${t.badges && t.badges.length && (st.phase === "FINAL" || st.phase === "DEBRIEF")
        ? `<p style="margin:.5rem 0 0">${badgePills(t.badges)}</p>` : ""}
      ${status}
    </div>
  </section>`;
}

function teamHeadInfo(t, n) {
  const r3 = t.rounds["3"];
  const bits = [];
  if (n === 2 || n === 3) {
    const c = t.rounds[String(n === 3 ? 3 : 2)].contract;
    if (c) bits.push("Σ" + sum(c));
  }
  if (n === 3 && r3.architecture) {
    bits.push(r3.architecture === "MODULAR" ? "MODULAIRE" : "PROPRIÉTAIRE");
  }
  if (n === 3 && r3.resolution) {
    const sh = H.st.shock;
    bits.push({
      KEEP: sh === "REGULATION" ? "conformité" : "garde BRAIN",
      REPLACE: sh === "INFRA_FAILURE" ? "ALT-INFRA" : "ALT-AI",
      ABANDON: "abandon"
    }[r3.resolution]);
  }
  return esc(bits.join(" · "));
}

/* --- conduite de seance -------------------------------------------------- */

const NOTES = {
  LOBBY: ["Distribuez les rôles : chaque étudiant scanne le QR et reçoit sa fiche privée.",
    "Lisez la proposition de valeur à voix haute.",
    "Précisez : chaque acteur reçoit 10 points de ressources par round."],
  R1_NEGO: ["5 minutes. La répartition des 40 points est imposée et non négociable.",
    "Ils peuvent argumenter, promettre, bluffer, révéler ou cacher leur coût.",
    "MOBI peut utiliser son unique subvention ; le contrat de base reste imposé."],
  R1_DECIDE: ["Décisions simultanées et secrètes.",
    "Attendez que les 5 acteurs de chaque équipe aient répondu, puis passez aux résultats."],
  R1_RESULTS: ["Ne faites pas encore de cours.",
    "Demandez : « Vous aviez une technologie, des clients potentiels et 40 points de valeur à créer. Pourquoi cela n'a-t-il pas fonctionné ? »",
    "Prenez deux ou trois réponses.",
    "Puis : « Vous avez une deuxième tentative. Cette fois, vous pouvez modifier l'accord. »"],
  R2_NEGO: ["8 minutes. Les 40 points sont librement répartissables, Σ R = 40.",
    "MOBI dépose le contrat mais ne peut imposer aucune signature.",
    "Les seuils restent privés. Demandez une première proposition, puis un tour de table des intentions.",
    "Chaque nouvelle version remet les intentions à zéro. Demandez ce qui a changé avant de voter."],
  R2_DECIDE: ["Le contrat ne peut plus être modifié une fois les décisions ouvertes."],
  R2_RESULTS: ["Mini-débrief, deux minutes :",
    "« Qui avait réellement le pouvoir de négociation ? Était-ce nécessairement MOBI ? »",
    "« L'orchestrateur pouvait-il simplement décider ? »",
    "« Pourquoi certains acteurs ont-ils reçu davantage qu'au round 1 ? »",
    "Puis : « Votre écosystème fonctionne. Mais vous devez choisir son architecture technique. »"],
  MARKET: ["3 minutes. Seul BRAIN peut changer d'écosystème ; seul MOBI peut faire une offre.",
    "Une offre est un simple nombre de points, prélevé sur la part de l'orchestrateur.",
    "Un écosystème n'héberge qu'un seul BRAIN : un départ n'est validé que si le siège visé est lui-même libéré.",
    "Ne commentez pas les offres pendant la phase. Révélez les mouvements en passant à la suite.",
    "C'est ici que se joue la crédibilité de l'option extérieure de BRAIN."],
  R3_ARCH: ["3 minutes. N'annoncez surtout pas le choc.",
    "Dites seulement : « Le marché et l'environnement réglementaire sont incertains. Une architecture doit être choisie pour les trois prochaines années. »"],
  R3_SHOCK: ["Le choc est tiré au sort par le serveur, le même pour toute la classe.",
    "Une fois tous les choix verrouillés, lisez la carte lentement.",
    "Laissez le silence agir avant d'ouvrir la renégociation."],
  R3_NEGO: ["5 minutes. Ils peuvent redistribuer les revenus, remplacer le partenaire touché, se mettre en conformité, ou renoncer.",
    "Le partenaire touché est ici en position de renégocier fortement — laissez faire.",
    "GRID peut encore activer STANDARD READY si l'écosystème est modulaire."],
  R3_DECIDE: ["Décisions finales. Plus aucune modification du contrat."],
  R3_RESULTS: ["Comparez les architectures entre écosystèmes.",
    "La modularité n'est pas universellement supérieure : c'est une assurance.",
    "Demandez : « Auriez-vous choisi la même chose en connaissant le choc ? »"],
  FINAL: ["Affichez les deux classements, puis les badges.",
    "Insistez si un étudiant est meilleure entreprise sans être dans le meilleur écosystème.",
    "Les badges n'ont aucun effet sur les scores : ils nomment ce qui vient de se produire."],
  DEBRIEF: ["Passez à l'onglet Débrief.", "15 minutes."]
};

function notes() {
  const list = NOTES[H.st.phase] || [];
  if (!list.length) return "";
  return `<details class="card facilitator" style="margin:0 1rem 1rem">
    <summary>Conduite de la séance — ${esc(H.st.phase_label)}</summary>
    <ul class="big-list" style="margin:.6rem 0 0;padding-left:1.2rem">
      ${list.map((x) => `<li>${esc(x)}</li>`).join("")}
    </ul>
  </details>`;
}

/* --- onglet JOUEURS ------------------------------------------------------ */

function players() {
  const st = H.st;
  const teams = Object.keys(st.teams);
  return `<div class="wrap wide" style="padding:0 1rem">
    <div class="card">
      <h3>Réglages</h3>
      <div class="row wrapped">
        <div style="width:12rem">
          <label for="tc">Nombre d'écosystèmes</label>
          <select id="tc" onchange="host('teams',{count:this.value})">
            ${[2, 3, 4, 5, 6].map((k) => `<option value="${k}" ${
              k === st.team_count ? "selected" : ""}>${k}</option>`).join("")}
          </select>
        </div>
        <button onclick="if(confirm('Redistribuer tous les rôles ?'))host('shuffle')">
          Redistribuer les rôles</button>
        <button onclick="if(confirm('Rouvrir le round 1 ? Les décisions sont effacées.'))host('unlock',{round:1})">
          Rejouer R1</button>
        <button onclick="if(confirm('Rouvrir le round 2 ?'))host('unlock',{round:2})">
          Rejouer R2</button>
        <button onclick="if(confirm('Rouvrir le round 3 ?'))host('unlock',{round:3})">
          Rejouer R3</button>
        <button class="ghost" style="border-color:var(--bad);color:var(--bad)"
          onclick="if(confirm('Effacer toute la partie et les joueurs ?'))host('reset')">
          Nouvelle partie</button>
      </div>
      <p class="tiny muted" style="margin:.8rem 0 0">
        Un siège sans étudiant est joué automatiquement : il accepte si son revenu
        couvre son coût et son option extérieure. Les sièges se remplissent dans
        l'ordre MOBI, FLEET, BRAIN, AUTO, GRID pour que chaque équipe garde son
        orchestrateur.</p>
    </div>

    <div class="card" id="roster">
      <h3>${st.players.length} joueurs</h3>
      <p class="small muted">${st.players.filter((p) => p.identity_required).length} identité(s) à compléter.
        Le bouton « Retirer » déconnecte l’étudiant. Si son siège devient vacant, il sera joué automatiquement.</p>
      <div class="roster-table">
      <table>
        <thead><tr><th>Prénom et nom</th><th>Écosystème</th><th>Rôle</th><th>Action</th></tr></thead>
        <tbody>
          ${st.players.map((p) => `<tr>
            <td>${esc(p.name)}${p.identity_required ? '<br><span class="pill wait">Identité à compléter</span>' : ""}</td>
            <td><select onchange="host('reassign',{player:'${p.id}',team:this.value,role:'${p.role}'})">
              ${teams.map((t) => `<option ${t === p.team ? "selected" : ""}>${t}</option>`).join("")}
            </select></td>
            <td><select onchange="host('reassign',{player:'${p.id}',team:'${p.team}',role:this.value})">
              ${ROLES.map((r) => `<option ${r === p.role ? "selected" : ""}>${r}</option>`).join("")}
            </select></td>
            <td><button class="small remove-student" onclick="removeStudent('${p.id}')">Retirer</button></td>
          </tr>`).join("")}
        </tbody>
      </table>
      </div>
      ${st.players.length ? "" : '<p class="muted">Personne n\'a encore rejoint.</p>'}
    </div>

    <div class="card">
      <h3>Journal</h3>
      <ul class="small muted" style="margin:0;padding-left:1.1rem">
        ${st.log.slice().reverse().map((l) => `<li>${esc(l.m)}</li>`).join("")}
      </ul>
    </div>
  </div>`;
}

/* --- onglet CLASSEMENTS -------------------------------------------------- */

function final() {
  const st = H.st, t = st.totals;
  const ecos = Object.entries(t.eco).sort((a, b) => b[1].total - a[1].total);
  const arch = (a) => a === "MODULAR" ? "modulaire"
    : a === "PROPRIETARY" ? "propriétaire" : "—";

  return `<div class="wrap wide" style="padding:0 1rem">
    <div class="card">
      <h2>Tableau final des écosystèmes</h2>
      <table>
        <thead><tr><th>Écosystème</th><th class="num">R1</th><th class="num">R2</th>
          <th>Architecture</th><th class="num">R3</th>
          <th>Badges</th><th class="num">Valeur collective cumulée</th></tr></thead>
        <tbody>
          ${ecos.map(([name, e]) => `<tr>
            <td><b style="color:${COLORS[name]};font-size:1.1rem">${name}</b></td>
            <td class="num mono">${signed(e.rounds["1"])}</td>
            <td class="num mono">${signed(e.rounds["2"])}</td>
            <td>${arch(e.architecture)}${
              e.resolution === "REPLACE" ? " · ALT-AI"
              : e.resolution === "ABANDON" ? " · abandon" : ""}</td>
            <td class="num mono">${signed(e.rounds["3"])}</td>
            <td>${badgePills(e.badges)}</td>
            <td class="num mono" style="font-size:1.2rem;font-weight:800">${signed(e.total)}</td>
          </tr>`).join("")}
        </tbody>
      </table>
    </div>

    <div class="card">
      <h2>Meilleures entreprises</h2>
      <table>
        <thead><tr><th></th><th>Nom</th><th>Rôle</th><th>Écosystème</th>
          <th class="num">R1</th><th class="num">R2</th><th class="num">R3</th>
          <th>Badges</th><th class="num">Total</th></tr></thead>
        <tbody>
          ${t.players.map((p, i) => `<tr class="${i < 3 ? "me" : ""}">
            <td class="muted">${i + 1}</td>
            <td>${esc(p.name)}</td>
            <td><b>${p.role}</b></td>
            <td style="color:${COLORS[p.team]}">${p.team}</td>
            <td class="num mono">${p.rounds["1"] == null ? "—" : p.rounds["1"]}</td>
            <td class="num mono">${p.rounds["2"] == null ? "—" : p.rounds["2"]}</td>
            <td class="num mono">${p.rounds["3"] == null ? "—" : p.rounds["3"]}</td>
            <td>${badgePills(p.badges)}</td>
            <td class="num mono" style="font-size:1.1rem;font-weight:800">${p.total}</td>
          </tr>`).join("")}
        </tbody>
      </table>
      <p class="muted small" style="margin:.8rem 0 0">
        Il est important qu'un étudiant puisse être <b>meilleure entreprise</b>
        sans appartenir au <b>meilleur écosystème</b>.</p>
    </div>
  </div>`;
}

/* --- onglet DEBRIEF ------------------------------------------------------ */

const SLIDES = [
  { h: "1 — Repartir de la proposition de valeur",
    boxed: "Navette autonome à la demande",
    p: "« Quelles activités étaient nécessaires pour produire effectivement cette proposition ? »",
    li: ["relation client", "réservation", "paiement", "production des véhicules",
         "conduite autonome", "cartographie", "recharge", "maintenance",
         "opérations", "supervision"],
    tag: "ACTIVITIES" },
  { h: "2 — Ajouter les acteurs",
    p: "« Qui contrôlait ces activités ? »",
    li: ["MOBI", "AUTO", "BRAIN", "GRID", "FLEET"], tag: "ACTORS" },
  { h: "3 — Positions",
    p: "« Les cinq entreprises occupaient-elles la même position ? »",
    li: ["certaines sont proches du client", "certaines contrôlent un complément critique",
         "certaines possèdent l'infrastructure", "certaines orchestrent"],
    tag: "POSITIONS" },
  { h: "4 — Links",
    p: "« Le système ressemblait-il vraiment à une chaîne fournisseur → entreprise → client ? »",
    li: ["AUTO ↔ BRAIN", "AUTO ↔ GRID", "BRAIN ↔ MOBI", "FLEET ↔ AUTO", "FLEET ↔ MOBI"],
    tag: "LINKS", boxed2: "Activities + Actors + Positions + Links" },
  { h: "5 — La question centrale du round 1",
    p: "« Pourquoi le premier écosystème échouait-il alors qu'il était collectivement rentable ? »",
    boxed: "Collective Value ≠ Individual Incentives",
    boxed2: "Participation ≠ Alignment",
    li: ["V = 40", "coûts totaux = 21", "options extérieures = 13",
         "40 − 21 − 13 = 6 points de surplus disponibles",
         "le problème n'était pas l'absence de valeur, mais sa distribution"] },
  { h: "6 — Orchestration",
    p: "« Quel était réellement le travail de MOBI ? »",
    li: ["identifier les acteurs nécessaires", "comprendre leurs dépendances",
         "négocier leur participation", "redistribuer suffisamment de valeur",
         "coordonner les investissements", "concevoir des règles acceptables"],
    boxed: "Orchestration ≠ Hierarchy" },
  { h: "7 — Création et capture de valeur",
    p: "« Un acteur important techniquement reçoit-il nécessairement beaucoup de valeur ? » Non. « Un acteur peut-il capturer tellement de valeur qu'il détruit l'écosystème dont il dépend ? » Oui.",
    boxed: "Value Creation ≠ Value Capture" },
  { h: "8 — Jacobides : complémentarités",
    p: "« Pourquoi ne pouviez-vous pas simplement acheter chaque élément indépendamment ? »",
    li: ["le véhicule doit être compatible avec l'IA, les stations, l'opérateur, les systèmes de MOBI",
         "la valeur d'un élément dépend de la présence et de la configuration des autres"] },
  { h: "9 — Jacobides : modularité",
    p: "« Qu'avez-vous réellement acheté avec les 6 points du standard ? »",
    li: ["de la substituabilité", "de la flexibilité",
         "une réduction des coûts de coordination futurs", "des interfaces",
         "la capacité à modifier la composition de l'écosystème"],
    boxed: "Modularity → Reduced Specificity → Greater Substitutability" },
  { h: "10 — Le standard redistribue le pouvoir",
    p: "« Que devient le pouvoir de BRAIN si BRAIN peut être remplacé facilement ? »",
    li: ["il diminue", "la modularité modifie le bargaining power, la dépendance, la capture de valeur"] },
  { h: "11 — Ce n'est pas une supply chain",
    li: ["supply chain : A → B → C → client",
         "écosystème : activités interdépendantes autour d'une même proposition de valeur",
         "les dépendances sont multilatérales",
         "aucune entreprise n'a d'autorité complète sur les autres"] },
  { h: "12 — Ce n'est pas nécessairement une plateforme",
    p: "« Avions-nous besoin d'un marché à deux faces pour avoir un écosystème ? » Non.",
    li: ["l'écosystème existe parce qu'une proposition de valeur dépend de l'alignement d'acteurs indépendants et complémentaires",
         "une plateforme n'est qu'une architecture possible parmi d'autres"] },
  { h: "13 — Conclusion",
    p: "« La stratégie d'écosystème commence là où la performance de ma propre organisation ne suffit plus à déterminer si ma proposition de valeur sera effectivement produite. »",
    boxed: "Success = Strategy + Partners + Alignment + Architecture" }
];

function brief() {
  return `<div class="wrap wide" style="padding:0 1rem">
    ${SLIDES.map((s) => `<section class="card slide">
      <h2>${esc(s.h)}</h2>
      ${s.boxed ? `<div class="boxed">${esc(s.boxed)}</div>` : ""}
      ${s.p ? `<p class="quote" style="font-size:1.2rem">${esc(s.p)}</p>` : ""}
      ${s.li ? `<ul class="big-list">${s.li.map((x) =>
        `<li>${esc(x)}</li>`).join("")}</ul>` : ""}
      ${s.tag ? `<div class="boxed" style="border-color:var(--accent);color:var(--accent)">${
        esc(s.tag)}</div>` : ""}
      ${s.boxed2 ? `<div class="boxed">${esc(s.boxed2)}</div>` : ""}
    </section>`).join("")}
  </div>`;
}

/* --- demarrage ----------------------------------------------------------- */

window.host = host;
window.setTab = setTab;
window.toggleTimer = toggleTimer;

document.addEventListener("keydown", (e) => {
  const t = e.target.tagName;
  if (t === "INPUT" || t === "SELECT" || t === "TEXTAREA" || t === "BUTTON") return;
  if (e.key === "ArrowRight") host("next");
  if (e.key === "ArrowLeft") host("prev");
  if (e.key === " ") { e.preventDefault(); toggleTimer(); }
});

poll();
