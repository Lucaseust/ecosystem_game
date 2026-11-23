"use strict";
const suppliedKey = new URLSearchParams(location.hash.slice(1)).get("cle") || new URLSearchParams(
  location.search).get("cle");
const KEY = suppliedKey || sessionStorage.getItem("eco_host_key") || "";
if (suppliedKey) {
  sessionStorage.setItem("eco_host_key", KEY);
  history.replaceState(null, "", location.pathname);
}
const ROLES = ["MOBI", "AUTO", "BRAIN", "GRID", "FLEET"];
const COLORS = {
  BLUE: "#7abfff",
  GREEN: "#85e0b2",
  RED: "#ff9c92",
  YELLOW: "#efcf79",
  PURPLE: "#c2a8ff",
  ORANGE: "#ffb47e"
};
const $ = id => document.getElementById(id);
const esc = v => String(v ?? "").replace(/[&<>"']/g, c => ({
  "&": "&amp;",
  "<": "&lt;",
  ">": "&gt;",
  '"': "&quot;",
  "'": "&#39;"
} [c]));
const money = n => new Intl.NumberFormat(EcoI18n.locale, {
  maximumFractionDigits: 2
}).format((n || 0) / 100);
const H = {
  st: null,
  version: 0,
  tab: "board",
  offset: 0
};
window.H = H;

function toast(msg) {
  const n = document.createElement("div");
  n.className = "toast";
  n.setAttribute("role", "status");
  n.textContent = msg;
  document.body.append(n);
  setTimeout(() => n.remove(), 3500);
}
async function host(action, extra = {}) {
  if (H.pending) return false;
  H.pending = true;
  if (action === "next") extra = {
    expected_phase: H.st.phase,
    ...extra
  };
  try {
    const response = await fetch("/api/host/action", {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        "Authorization": "Bearer " + encodeURIComponent(KEY)
      },
      body: JSON.stringify({
        action,
        ...extra
      })
    });
    const data = await response.json();
    if (!response.ok) throw new Error(data.error);
    return true;
  } catch (e) {
    toast(e.message);
    return false;
  } finally {
    H.pending = false;
  }
}
async function poll() {
  for (;;) {
    try {
      const response = await fetch("/api/host?since=" + H.version, {
        headers: {
          "Authorization": "Bearer " + encodeURIComponent(KEY)
        }
      });
      if (response.status === 403) {
        $("view").innerHTML = EcoI18n.t(
          '<div class="card"><h1>Clé enseignant invalide</h1><p>Ouvrez le lien fourni par l’application de bureau.</p></div>'
        );
        return;
      }
      if (!response.ok) throw new Error();
      H.st = await response.json();
      H.version = H.st.version;
      H.offset = H.st.server_time * 1000 - Date.now();
      $("offline").hidden = true;
      render();
    } catch (_) {
      $("offline").hidden = false;
      await new Promise(r => setTimeout(r, 1500));
    }
  }
}

function tick() {
  const t = H.st?.timer;
  if (!t || t.remaining == null) {
    $("timer").textContent = "—";
    return;
  }
  const n = t.running ? Math.max(0, Math.round(t.ends_at - (Date.now() + H.offset) / 1000)) : t
    .remaining;
  $("timer").textContent = String(Math.floor(n / 60)).padStart(2, "0") + ":" + String(n % 60)
    .padStart(2, "0");
  $("btnplay").textContent = t.running ? "Ⅱ" : "▶";
}
setInterval(tick, 250);

function toggleTimer() {
  if (!H.st) return;
  host(H.st.timer.running ? "timer_pause" : "timer_start");
}

function advanceDate() {
  if (!H.st || H.st.phase === "DEBRIEF") return;
  const count = Object.values(H.st.teams).filter(t => t.proposal?.status === "OPEN").length;
  if (H.st.phase !== "LOBBY" && H.st.phase !== "FINAL" && !confirm(
      `${EcoI18n.t("Clore ")}${H.st.phase_label}${EcoI18n.t(" et régler les comptes ? ")}${count}${EcoI18n.t(" proposition(s) non acceptée(s) expireront. Un groupe sans accord ne bloque pas les autres. Les contrats signés et les investissements seront conservés.")}`
    )) return;
  host("next");
}

function setTab(tab) {
  H.tab = tab;
  ["board", "players", "final", "brief"].forEach(k => $("tab-" + k).setAttribute("aria-pressed",
    String(k === tab)));
  render();
}

function manageStudents() {
  setTab("players");
}

function requestIdentity() {
  host("request_identity");
}

function removeStudent(id) {
  const p = H.st.players.find(p => p.id === id);
  if (p && confirm(EcoI18n.t("Retirer ") + p.name + EcoI18n.t(
      " ? Son entreprise conserve ses engagements ; un binôme restant ou un automate assure la suite."
    ))) host("remove", {
    player: id
  });
}

function render() {
  const st = H.st;
  if (!st) return;
  $("code").textContent = st.code;
  $("nplayers").textContent = st.players.length;
  $("phase").textContent = st.phase_label;
  const base = st.join_base || location.origin;
  const url = base + "/?c=" + st.code;
  $("joinurl").textContent = url;
  const qr = "/qr.svg?d=" + encodeURIComponent(url);
  if ($("qr").getAttribute("src") !== qr) $("qr").src = qr;
  if ($("joinQr").getAttribute("src") !== qr) $("joinQr").src = qr;
  $("joinCode").textContent = st.code;
  $("joinLink").textContent = url;
  $("joinLink").href = url;
  $("enlargeQr").disabled = false;
  $("advanceDate").textContent = st.phase === "LOBBY" ? EcoI18n.t("Ouvrir janvier →") : st.phase ===
    "FINAL" ? EcoI18n.t("Ouvrir le débrief →") : EcoI18n.t("Clore cette date et avancer →");
  $("advanceDate").disabled = st.phase === "DEBRIEF";
  $("advanceHint").textContent = st.rules_version !== "campaign-3.0" ? EcoI18n.t(
    "Redémarrez le serveur pour activer les nouveaux événements. L’histoire déjà jouée sera conservée."
  ) : ["JANUARY", "APRIL", "JULY", "OCTOBER"].includes(st.phase) ? EcoI18n.t(
    "Vous pouvez avancer sans accord dans tous les groupes. Le chronomètre ne clôt pas la date."
  ) : EcoI18n.t("Vous pilotez le calendrier commun.");
  tick();
  document.body.classList.toggle("debrief-projecting", H.tab === "brief" && Debrief.isProjecting());
  replacePanel($("view"), H.tab === "board" ? board() : H.tab === "players" ? roster() : H.tab ===
    "final" ? annual() : analysis());
}
const NODES = {
  MANDATE: EcoI18n.t("Installation des entreprises"),
  FOUNDING: EcoI18n.t("Premier accord à constituer"),
  INCIDENT: EcoI18n.t("Intervention à financer"),
  MISSING_PARTNER: EcoI18n.t("Partenaire manquant"),
  DEMAND: EcoI18n.t("Demande supplémentaire"),
  PARTNER: EcoI18n.t("Offre extérieure"),
  OPERATING: EcoI18n.t("Exploitation engagée"),
  RENEGOTIATION: EcoI18n.t("Renégociation demandée"),
  REVENUE_PRESSURE: EcoI18n.t("Recettes du territoire en baisse"),
  PAUSED: EcoI18n.t("Exploitation suspendue"),
  CLOSED: EcoI18n.t("Année clôturée")
};

function dateOverview() {
  if (!["JANUARY", "APRIL", "JULY", "OCTOBER"].includes(H.st.phase)) return "";
  const teams = Object.values(H.st.teams),
    unformed = teams.filter(t => !t.installed).length,
    running = teams.filter(t => t.installed && t.operating && !t.incident && !t.missing).length;
  return `${EcoI18n.t("<section class=\"date-overview\"><div><span class=\"edition\">Calendrier commun · situations indépendantes</span><h2>La date peut avancer pour tous.</h2><p>Aucun accord collectif entre les groupes n’est requis. À la clôture, chaque territoire règle ses propres comptes et poursuit sa propre histoire.</p></div><dl><div><dt>Exploitation engagée</dt><dd>")}${running}${EcoI18n.t("</dd></div><div><dt>Premier accord en attente</dt><dd>")}${unformed}${EcoI18n.t("</dd></div><div><dt>Service suspendu ou interrompu</dt><dd>")}${teams.length-running-unformed}</dd></div></dl></section>`;
}

function board() {
  return dateOverview() +
    `${EcoI18n.t("<p class=\"campaign-status\"><strong>Une année, des trajectoires.</strong> Clore une date règle les comptes du trimestre et ouvre la suivante, y compris pour les groupes sans accord. Un territoire sans flotte peut encore négocier ; il ne rattrape pas les trimestres écoulés. Le chronomètre ne clôt pas la date.</p><div class=\"teams-grid\">")}${Object.values(H.st.teams).map(t=>{const last=t.settlements.at(-1);return `<article class="team-card" style="--team:${COLORS[t.team]}"><header><span>${t.team}</span><span>${NODES[t.node]}</span></header><div class="body">${t.news?GameVisuals.note(t.incident?"alert":"message",t.news.title,t.news.text,t.incident?"alert":"message"):""}<p>${t.installed?`Interfaces ${t.architecture==="MODULAR"?EcoI18n.t("communes"):EcoI18n.t("spécifiques")} · ${t.growth?EcoI18n.t("extension financée"):EcoI18n.t("périmètre pilote")}`:EcoI18n.t("La flotte attend les engagements des cinq entreprises. Ce groupe ne bloque pas les autres.")}</p>${Object.keys(t.renegotiation_requests||{}).length?GameVisuals.note("message",EcoI18n.t("Renégociation demandée"),Object.keys(t.renegotiation_requests).join(", ")+EcoI18n.t(" demande à revoir le contrat. Les motifs et chiffres privés restent à la discrétion des partenaires."),"message"):""}${last?`${EcoI18n.t("<p class=\"team-settlement\"><b>Trimestre précédent : ")}${money(last.revenue)}${EcoI18n.t(" crédits de transport</b><span>")}${esc(last.message||EcoI18n.t("Les comptes de ce territoire ont été réglés."))}</span></p>`:""}${ROLES.map(r=>`<div class="seat"><b class="rname">${r}</b><span class="pname">${t.seats[r].bot?EcoI18n.t("Automatique"):esc(t.seats[r].names.join(", "))}<small class="edition">${esc(t.profiles[r]||EcoI18n.t("Engagement à préciser"))}</small></span><span>${[t.missing,t.replaced].includes(r)?EcoI18n.t("Hors exploitation"):t.contract?.allocations[r]!=null?money(t.contract.allocations[r])+" "+EcoI18n.t("crédits"):"—"}</span></div>`).join("")}${t.proposal?.status==="OPEN"?`${EcoI18n.t("<p class=\"team-progress\">Proposition V")}${t.proposal.revision} · ${t.proposal.answered} / ${t.proposal.required.length}${EcoI18n.t(" réponses. Les joueurs peuvent publier leurs demandes et expliquer leurs décisions.</p>")}`:t.contract?`<p class="team-progress">${t.agreement_current?EcoI18n.t("Accord"):EcoI18n.t("Dernier accord signé")} V${t.contract.revision}${!t.agreement_current?EcoI18n.t(" · nouvel accord requis pour ce tour"):t.revenue_adjustment?EcoI18n.t(" · recettes révisées"):Object.keys(t.renegotiation_requests||{}).length?EcoI18n.t(" · renégociation demandée"):EcoI18n.t(" en vigueur")}.</p>`:""}${t.history.length?`${EcoI18n.t("<details><summary>Histoire du territoire</summary>")}${t.history.map(h=>`<p>${esc(h.text)}</p>`).join("")}</details>`:""}</div></article>`;}).join("")}</div>`;
}

function roster() {
  const lobby = H.st.phase === "LOBBY";
  return `${EcoI18n.t("<div class=\"campaign-actions\"><h2>Les participants et leurs entreprises</h2><p class=\"small muted\">Les réaffectations et le nombre de territoires sont fixés avant le début de l’année. Un binôme partage les décisions d’une entreprise.</p>")}${lobby?`${EcoI18n.t("<div class=\"row wrapped\"><label>Territoires<select id=\"teamCount\" onchange=\"host('teams',{count:Number(this.value)})\">")}${[2,3,4,5,6].map(n=>`<option ${n===H.st.team_count?"selected":""}>${n}</option>`).join("")}${EcoI18n.t("</select></label><button onclick=\"host('shuffle')\">Redistribuer les rôles</button></div>")}`:""}${EcoI18n.t("<div class=\"roster-table\"><table id=\"roster\"><thead><tr><th>Étudiant</th><th>Territoire</th><th>Entreprise</th><th>Identité</th><th></th></tr></thead><tbody>")}${H.st.players.map(p=>`<tr><td>${esc(p.name)}</td><td>${lobby?`${EcoI18n.t("<select aria-label=\"Territoire de ")}${esc(p.name)}" onchange="host('reassign',{player:'${p.id}',team:this.value,role:'${p.role}'})">${Object.keys(H.st.teams).map(t=>`<option ${t===p.team?"selected":""}>${t}</option>`).join("")}</select>`:p.team}</td><td>${lobby?`${EcoI18n.t("<select aria-label=\"Entreprise de ")}${esc(p.name)}" onchange="host('reassign',{player:'${p.id}',team:'${p.team}',role:this.value})">${ROLES.map(r=>`<option ${r===p.role?"selected":""}>${r}</option>`).join("")}</select>`:p.role}</td><td>${p.identity_required?EcoI18n.t("À compléter"):EcoI18n.t("Complète")}</td><td><button class="small remove-student" onclick="removeStudent('${p.id}${EcoI18n.t("')\">Retirer</button></td></tr>")}`).join("")}</tbody></table></div></div>`;
}

function annual() {
  if (!H.st.can_export) return EcoI18n.t(
    '<div class="campaign-actions"><h2>Le bilan se construit pendant l’année.</h2><p>Les résultats individuels seront révélés à la clôture de décembre. Les contrats et les dépenses restent enregistrés entre les dates.</p></div>'
  );
  const teams = Object.values(H.st.teams).sort((a, b) => b.created - a.created);
  const companies = teams.flatMap(t => ROLES.map(r => ({
    team: t.team,
    role: r,
    cash: t.cash[r],
    names: t.seats[r].names.join(", ") || EcoI18n.t("Automatique")
  }))).sort((a, b) => b.cash - a.cash);
  return `${EcoI18n.t("<div class=\"campaign-actions\"><h2>Résultats de l’année 2032</h2><div class=\"analysis-grid\"><section class=\"card\"><h3>Valeur collective du transport</h3><table>")}${teams.map(t=>`<tr><td style="color:${COLORS[t.team]}">${t.team}</td><td>${money(t.revenue)}${EcoI18n.t(" de recettes</td><td>")}${money(t.expenses)}${EcoI18n.t(" de coûts</td><td class=\"num\">")}${money(t.created)}</td></tr>`).join("")}${EcoI18n.t("</table></section><section class=\"card\"><h3>Résultat des entreprises · hors dotation initiale</h3><table>")}${companies.map(c=>`<tr><td>${esc(c.names)}</td><td>${c.role} · ${c.team}</td><td class="num">${money(c.cash-2000)}</td></tr>`).join("")}${EcoI18n.t("</table></section></div><p class=\"small muted\">Les revenus extérieurs participent au résultat des entreprises, pas à la valeur créée par le transport. Les événements propres à chaque territoire éclairent les écarts.</p></div>")}`;
}

function analysis() {
  if (!H.st.can_export) return EcoI18n.t(
    '<div class="campaign-actions"><h2>Le journal enregistre déjà les trajectoires.</h2><p>Les graphiques, décisions et chiffres privés seront disponibles au bilan, après la clôture de l’année.</p></div>'
  );
  return `${EcoI18n.t("<div class=\"campaign-actions db-actions\"><h2>Les données de la séance</h2><a class=\"download-link\" id=\"exportData\" download=\"ecosystem-2032.zip\" href=\"/api/export?cle=")}${encodeURIComponent(KEY)}${EcoI18n.t("\">Télécharger le journal complet · ZIP</a><a class=\"download-link\" id=\"exportReport\" download=\"ecosystem-debrief.html\" href=\"/api/debrief?cle=")}${encodeURIComponent(KEY)}${EcoI18n.t("\">Rapport interactif hors connexion · HTML</a></div>")}${Debrief.render(H.st.debrief)}`;
}

const joinDialog = $("joinDialog");
$("enlargeQr").addEventListener("click", () => {
  if (H.st && !joinDialog.open) joinDialog.showModal();
});
$("closeJoinDialog").addEventListener("click", () => joinDialog.close());
joinDialog.addEventListener("click", event => {
  if (event.target !== joinDialog) return;
  const box = joinDialog.getBoundingClientRect();
  if (event.clientX < box.left || event.clientX > box.right ||
      event.clientY < box.top || event.clientY > box.bottom) joinDialog.close();
});
joinDialog.addEventListener("close", () => $("enlargeQr").focus({preventScroll: true}));

document.addEventListener("keydown", e => {
  if (joinDialog.open) return;
  if (["INPUT", "SELECT", "TEXTAREA", "BUTTON"].includes(document.activeElement.tagName))
    return;
  if (e.code === "Space") {
    e.preventDefault();
    toggleTimer();
  }
});
poll();

async function downloadSession(path, filename) {
  try {
    const response = await fetch(path, {
      headers: {
        Authorization: "Bearer " + encodeURIComponent(KEY)
      }
    });
    if (!response.ok) {
      const data = await response.json();
      throw new Error(data.error);
    }
    const url = URL.createObjectURL(await response.blob());
    const link = document.createElement("a");
    link.href = url;
    link.download = filename;
    document.body.append(link);
    link.click();
    link.remove();
    setTimeout(() => URL.revokeObjectURL(url), 5000);
  } catch (error) {
    toast(error.message);
  }
}
