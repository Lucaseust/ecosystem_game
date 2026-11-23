/* Campagne 2032 : seul le present et le passe du territoire sont affiches. */
"use strict";
const $ = (id) => document.getElementById(id);
const esc = (v) => String(v ?? "").replace(/[&<>"']/g, c => ({
  "&": "&amp;",
  "<": "&lt;",
  ">": "&gt;",
  '"': "&quot;",
  "'": "&#39;"
} [c]));
const ROLES = ["MOBI", "AUTO", "BRAIN", "GRID", "FLEET"];
const ASSETS = {
  MOBI: EcoI18n.t("Application et voyageurs"),
  AUTO: EcoI18n.t("Véhicules"),
  BRAIN: EcoI18n.t("IA de conduite"),
  GRID: EcoI18n.t("Recharge et dépôts"),
  FLEET: EcoI18n.t("Exploitation de la flotte")
};
const COLORS = {
  BLUE: "#7abfff",
  GREEN: "#85e0b2",
  RED: "#ff9c92",
  YELLOW: "#efcf79",
  PURPLE: "#c2a8ff",
  ORANGE: "#ffb47e"
};
const money = (n) => new Intl.NumberFormat(EcoI18n.locale, {
  maximumFractionDigits: 2
}).format((n || 0) / 100);
const C = {
  st: null,
  token: localStorage.getItem("eco_token"),
  version: 0,
  tab: "situation",
  draft: {},
  pending: false,
  offset: 0,
  scene: null,
  retry: null
};
window.C = C;
const done = () => C.st && ["FINAL", "DEBRIEF"].includes(C.st.phase);
const live = () => C.st && !["LOBBY", "FINAL", "DEBRIEF"].includes(C.st.phase);

function toast(message, ok = false) {
  const node = document.createElement("div");
  node.className = "toast" + (ok ? " ok" : "");
  node.setAttribute("role", "status");
  node.textContent = message;
  document.body.append(node);
  setTimeout(() => node.remove(), 3500);
}
async function post(path, body) {
  const response = await fetch(path, {
    method: "POST",
    headers: {
      "Content-Type": "application/json"
    },
    body: JSON.stringify(body)
  });
  const data = await response.json();
  if (!response.ok) throw new Error(data.error || EcoI18n.t("La demande n’a pas abouti."));
  return data;
}
async function send(action, extra = {}) {
  if (C.pending) return;
  C.pending = true;
  const payload = JSON.stringify({
    action,
    ...extra
  });
  if (C.retry?.payload !== payload) C.retry = {
    payload,
    id: globalThis.crypto?.randomUUID?.() || Date.now().toString(36) + Math.random().toString(
      36).slice(2)
  };
  try {
    await post("/api/action", {
      token: C.token,
      action,
      request_id: C.retry.id,
      ...extra
    });
    C.retry = null;
    toast(EcoI18n.t("Décision enregistrée"), true);
  } catch (error) {
    toast(error.message);
  } finally {
    C.pending = false;
  }
}
async function join() {
  $("gateerr").hidden = true;
  $("gojoin").disabled = true;
  try {
    const data = await post("/api/join", {
      first_name: $("pname").value.trim(),
      last_name: $("plastname").value.trim(),
      code: $("pcode").value.trim().toUpperCase()
    });
    C.token = data.token;
    C.version = 0;
    localStorage.setItem("eco_token", C.token);
    localStorage.setItem("eco_code", $("pcode").value.trim().toUpperCase());
    start();
  } catch (error) {
    $("gateerr").textContent = error.message;
    $("gateerr").hidden = false;
  } finally {
    $("gojoin").disabled = false;
  }
}

function logout(message) {
  EcoIntro.reset();
  localStorage.removeItem("eco_token");
  C.token = null;
  C.version = 0;
  C.st = null;
  C.draft = {};
  C.scene = null;
  $("game").hidden = true;
  $("gate").hidden = false;
  $("gateerr").textContent = message;
  $("gateerr").hidden = false;
}

function start() {
  $("gate").hidden = true;
  $("game").hidden = false;
  poll();
}
async function poll() {
  while (C.token) {
    try {
      const response = await fetch("/api/state?since=" + C.version, {
        headers: {
          "Authorization": "Bearer " + C.token
        }
      });
      if (response.status === 401) return logout(EcoI18n.t(
        "Rejoignez la campagne avec le code de la salle."));
      if (!response.ok) throw new Error();
      C.st = await response.json();
      C.version = C.st.version;
      C.offset = C.st.server_time * 1000 - Date.now();
      $("offline").hidden = true;
      render();
    } catch (_) {
      $("offline").hidden = false;
      await new Promise(resolve => setTimeout(resolve, 1500));
    }
  }
}

function tick() {
  const t = C.st?.timer;
  if (!t || t.remaining == null) {
    $("tTimer").textContent = "—";
    return;
  }
  const remaining = t.running ? Math.max(0, Math.round(t.ends_at - (Date.now() + C.offset) /
    1000)) : t.remaining;
  $("tTimer").textContent = String(Math.floor(remaining / 60)).padStart(2, "0") + ":" + String(
    remaining % 60).padStart(2, "0");
  $("tTimer").className = "timer" + (remaining <= 30 ? " low" : "");
}
setInterval(tick, 250);

function chooseTab(tab) {
  if (!["situation", "entreprise", "table"].includes(tab)) return;
  C.tab = tab;
  render();
  window.scrollTo(0, 0);
}

function render() {
  const st = C.st,
    me = st.me,
    t = st.team;
  document.documentElement.style.setProperty("--team", COLORS[me.team]);
  $("tRole").innerHTML = GameVisuals.icon(me.role) + "<span>" + me.role + "</span>";
  $("tName").textContent = me.name;
  $("tTeam").textContent = ASSETS[me.role];
  if ($("tTeamName").textContent !== me.team) $("tTeamName").textContent = me.team;
  $("tPhase").textContent = st.phase_label;
  tick();
  const scene = [st.phase, me.org_id, t.node].join(":");
  if (C.seat !== me.org_id) {
    C.draft = {};
    C.seat = me.org_id;
    C.inspectRole = me.role;
  }
  C.entering = C.scene !== scene;
  if (C.entering) {
    C.tab = "situation";
    C.scene = scene;
    window.scrollTo(0, 0);
  }
  const active = document.activeElement;
  const focus = active?.id && $("app").contains(active) ? {
    id: active.id,
    s: active.selectionStart,
    e: active.selectionEnd
  } : null;
  replacePanel($("app"), me.identity_required ? identity() : C.tab === "situation" ? situation() : C
    .tab === "entreprise" ? company() : table());
  const nav = $("playerNav");
  nav.hidden = !!me.identity_required;
  nav.innerHTML = [
    ["situation", "01", EcoI18n.t("La situation")],
    ["entreprise", "02", EcoI18n.t("Mon entreprise")],
    ["table", "03", EcoI18n.t("La table")]
  ].map(([key, number, label]) =>
    `<button id="nav-${key}" aria-current="${C.tab===key?"page":"false"}" onclick="chooseTab('${key}')"><span>${number}</span>${label}</button>`
  ).join("");
  if (focus && $(focus.id)) {
    $(focus.id).focus({
      preventScroll: true
    });
    try {
      $(focus.id).setSelectionRange(focus.s, focus.e);
    } catch (_) {}
  }
  EcoIntro.sync(me, C.token);
}

function heading(label, title, text, role = null) {
  return `<header class="page-heading ${role?"has-emblem":""}">${role?`<span class="company-emblem" style="--role-color:${GameVisuals.colors[role]}">${GameVisuals.icon(role)}</span>`:""}<span class="edition">${esc(label)}</span><h1>${esc(title)}</h1><p class="${role?"company-copy":"scene-copy"}">${esc(text)}</p></header>`;
}

function identity() {
  return `${EcoI18n.t("<form class=\"card\" onsubmit=\"event.preventDefault();saveIdentity()\"><h1>Votre identité</h1><p>L’enseignant vous demande de compléter votre nom.</p><label for=\"identityFirst\">Prénom</label><input id=\"identityFirst\" type=\"text\" autocomplete=\"given-name\" data-k=\"first\" required value=\"")}${esc(C.draft.first??C.st.me.first_name)}${EcoI18n.t("\"><label for=\"identityLast\">Nom</label><input id=\"identityLast\" type=\"text\" autocomplete=\"family-name\" data-k=\"last\" required value=\"")}${esc(C.draft.last??C.st.me.last_name)}${EcoI18n.t("\"><button class=\"primary block\">Enregistrer</button></form>")}`;
}

function quarterReceipt() {
  const previous = C.st.team.settlements.at(-1);
  if (!previous) return "";
  // Read settled ledger amounts, including rounding and the contract used then.
  // Current shares or capacity may already have changed at the new date.
  const rows = C.st.me.transactions.filter(row => row.economic_date === previous.date);
  const total = kind => rows.filter(row => row.kind === kind).reduce((sum, row) => sum + row.amount, 0);
  const revenue = total("REVENUE"), outside = total("OUTSIDE");
  const costs = -rows.filter(row => row.amount < 0).reduce((sum, row) => sum + row.amount, 0);
  const net = rows.reduce((sum, row) => sum + row.amount, 0);
  return `<details class="quarter-receipt"><summary>${esc(dateName(previous.date))} · ${net > 0 ? "+" : ""}${money(net)} ${EcoI18n.t("crédits pour votre entreprise")}</summary><dl class="allocation">${[
    [EcoI18n.t("Recettes du transport reçues"), revenue],
    [EcoI18n.t("Activité extérieure"), outside],
    [EcoI18n.t("Dépenses du trimestre"), -costs],
    [EcoI18n.t("Variation de trésorerie"), net]
  ].map(([label, amount]) => `<div><dt>${esc(label)}</dt><dd>${money(amount)} <small>${EcoI18n.t("crédits")}</small></dd></div>`).join("")}</dl><p>${esc(previous.message || EcoI18n.t("Les comptes ont été réglés. Retrouvez vos mouvements dans Mon entreprise."))}</p></details>`;
}

function calendarStatus() {
  const dates = ["JANUARY", "APRIL", "JULY", "OCTOBER"],
    current = dates.indexOf(C.st.phase),
    t = C.st.team;
  if (current < 0) return "";
  return `<section class="quarter-status ${C.entering?"quarter-arrives":""}${EcoI18n.t("\" aria-label=\"Calendrier et dernier trimestre\"><div class=\"quarter-heading\"><span class=\"edition\">Trimestre ")}${current+1} / 4</span><span class="quarter-track" aria-hidden="true">${dates.map((_,i)=>`<i class="${i<current?"past":i===current?"now":""}"></i>`).join("")}</span></div>${quarterReceipt()}<p>${!t.installed?`${EcoI18n.t("Sans accord, votre groupe peut encore lancer sa flotte. Il reste ")}${4-current}${EcoI18n.t(" trimestre")}${current<3?"s":""}${EcoI18n.t(", celui-ci compris. Les autres groupes poursuivent leur histoire.")}`:EcoI18n.t("Les engagements déjà pris sont conservés. Les comptes sont réglés à la clôture par l’enseignant.")}</p></section>`;
}
async function saveIdentity() {
  try {
    await post("/api/action", {
      token: C.token,
      action: "identity",
      first_name: $("identityFirst").value,
      last_name: $("identityLast").value
    });
  } catch (e) {
    toast(e.message);
  }
}

function situation() {
  const {
    me,
    team: t
  } = C.st;
  if (done()) return final();
  if (!live()) return heading(EcoI18n.t("Métropole · Janvier 2032"), EcoI18n.t(
      "Une flotte à construire."), EcoI18n.t(
      "La ville veut des navettes sans chauffeur : véhicules, IA, recharge, exploitation quotidienne et application voyageurs. Aucun partenaire ne possède l’ensemble."
    )) + GameVisuals.fleet(t) +
    `${EcoI18n.t("<section class=\"seat-ticket\"><span class=\"edition\">Votre entreprise · ")}${esc(me.team)}</span><strong>${me.role}</strong><p>${esc(ASSETS[me.role])}${EcoI18n.t("</p><button class=\"primary block\" onclick=\"chooseTab('entreprise')\">Ouvrir mon dossier →</button></section><p class=\"table-note\">Une année pour créer le service et maximiser votre résultat. Chaque entreprise défend ses intérêts.</p><p class=\"waiting\">L’enseignant ouvre la campagne lorsque la salle est prête.</p>")}`;
  const scenes = {
    FOUNDING: [EcoI18n.t("Assembler le consortium"), EcoI18n.t("La ville attend un accord."),
      EcoI18n.t(
        "Négociez apports, financement et partage des recettes. Les cinq activités sont nécessaires pour circuler."
      )
    ],
    INCIDENT: [EcoI18n.t("La flotte est à l’arrêt"), EcoI18n.t(
      "Une activité doit être rétablie."), EcoI18n.t(
      "Investissements et contrats sont conservés. Financez l’intervention et obtenez les engagements nécessaires."
    )],
    MISSING_PARTNER: [EcoI18n.t("Une position est vacante"), EcoI18n.t(
      "Votre partenaire est parti."), EcoI18n.t(
      "Les actifs restent installés. Un nouvel accord permet un substitut ou le retour du partenaire."
    )],
    DEMAND: [EcoI18n.t("Une demande supplémentaire"), EcoI18n.t(
      "Le territoire veut plus de trajets."), EcoI18n.t(
      "Financez une extension ou conservez le périmètre actuel. L’extension engage dépenses et montée en charge."
    )],
    PARTNER: [EcoI18n.t("Les intérêts évoluent"), EcoI18n.t("Une offre extérieure est arrivée."),
      EcoI18n.t(
        "BRAIN dispose d’une proposition privée. Le contrat actif et les restrictions de mobilité déjà consenties restent applicables."
      )
    ],
    OPERATING: [EcoI18n.t("La flotte est constituée"), EcoI18n.t("Faites vivre votre service."),
      EcoI18n.t(
        "Obtenez un accord en crédits pour ce tour. Vous pouvez reprendre les montants précédents dans une nouvelle proposition, puis recueillir les consentements."
      )
    ],
    PAUSED: [EcoI18n.t("Exploitation suspendue"), EcoI18n.t("Les actifs sont toujours là."),
      EcoI18n.t(
        "Les recettes du transport sont interrompues. Un accord peut organiser la reprise ; aucune dépense passée n’est effacée."
      )
    ]
  };
  scenes.RENEGOTIATION = [EcoI18n.t("Un partenaire rouvre la discussion"), EcoI18n.t(
    "Le contrat est contesté."), EcoI18n.t(
    "Une entreprise demande une révision. Négociez un accord en crédits pour ce tour. Sans unanimité, le gain est nul."
  )];
  scenes.REVENUE_PRESSURE = [EcoI18n.t("Les conditions économiques ont changé"), EcoI18n.t(
    "Moins de crédits à répartir."), EcoI18n.t(
    "La contribution de la ville diminue. MOBI doit proposer une nouvelle répartition en crédits, acceptée par les partenaires."
  )];
  const privatePressure = !!me.private_shock && !me.outside_position;
  const s = t.node === "OPERATING" && privatePressure ? [EcoI18n.t(
      "Un changement pour votre entreprise"), EcoI18n.t("Votre activité coûte plus cher."),
    EcoI18n.t(
      "Vos frais augmentent ; négociez les crédits nécessaires pour ce tour. Cette information est privée. Décidez de maintenir votre engagement ou de rouvrir la discussion."
    )
  ] : scenes[t.node] || scenes.OPERATING;
  const visual = t.installed && t.node === "OPERATING" && !privatePressure && t.proposal?.status !==
    "OPEN" ? GameVisuals.fleet(t) : "";
  const news = t.news && !(privatePressure && t.news.kind === "PRIVATE_COST") ? GameVisuals.note(t
    .incident ? "alert" : "message", t.news.title, t.news.text, t.incident ? "alert" : "message"
  ) : "";
  return heading(...s) + calendarStatus() + news + visual +
    (!t.installed && t.proposal?.status !== "OPEN" ? profileChoice() : "") + privateCost() +
    outsideChoice() + renegotiations() + negotiation() + proposal() +
    (me.role === "MOBI" ? editor() : "") +
    (t.contract ? contract(t.contract, !t.agreement_current ? EcoI18n.t("Accord précédent · à renégocier pour ce tour") : t.operating ? (t.revenue_adjustment ? EcoI18n.t(
      "Accord maintenu · recettes révisées") : me.private_shock ? EcoI18n.t(
      "Accord maintenu · vos frais ont changé") : EcoI18n.t("Accord en vigueur")) : EcoI18n.t(
      "Dernier accord signé · exploitation suspendue")) : "") +
    (!visual ?
      `${EcoI18n.t("<details class=\"fleet-disclosure\"><summary>Vue de la flotte et du territoire</summary>")}${GameVisuals.fleet(t)}</details>` :
      "") + history() + rules();
}
const PROFILE_GUIDES = {
  MOBI: {
    question: EcoI18n.t(
      "Quelle relation voyageurs financer ?"),
    options: {
      LOCAL: {
        purpose: EcoI18n.t(
          "Vous assurez la réservation et la relation client nécessaires au pilote."),
        effect: EcoI18n.t("Le service utilise son niveau de recettes de base."),
        condition: EcoI18n.t(
          "Ce choix suffit pour constituer la flotte ; le partage des recettes reste à négocier."
        )
      },
      SUPPORT: {
        purpose: EcoI18n.t(
          "Vous financez une assistance aux voyageurs plus développée pour soutenir les réservations."
        ),
        effect: EcoI18n.t(
          "Jusqu’à 2 crédits s’ajoutent aux recettes trimestrielles à pleine capacité, partagés selon le contrat."
        ),
        condition: EcoI18n.t(
          "MOBI paie le supplément d’installation et reçoit sa part des recettes ajoutées. Les périodes réduites rapportent moins ; aucun supplément sans recettes."
        )
      }
    }
  },
  AUTO: {
    question: EcoI18n.t(
      "Comment adapter les véhicules en préservant leur réutilisation ?"
    ),
    options: {
      DEDICATED: {
        purpose: EcoI18n.t("Vous adaptez les véhicules aux trajets prévus pour ce territoire."),
        effect: EcoI18n.t("Les véhicules assurent la capacité prévue pour le pilote."),
        condition: EcoI18n.t(
          "Votre installation de base reste à financer à l’entrée en vigueur de l’accord.")
      },
      FLEXIBLE: {
        purpose: EcoI18n.t("Vous financez des véhicules plus faciles à reconfigurer."),
        effect: EcoI18n.t(
          "Le devis collectif d’une adaptation ou d’un remplacement ultérieur peut baisser de 1 crédit. Après installation, une activité extérieure disponible rapporte aussi 1 crédit supplémentaire par trimestre."
        ),
        condition: EcoI18n.t(
          "La dépense est certaine à la signature ; les avantages dépendent des interventions et activités réalisées. L’économie dépend aussi des moyens apportés par les partenaires."
        )
      }
    }
  },
  BRAIN: {
    question: EcoI18n.t(
      "Quels droits sur votre IA engager jusqu’en décembre ?"),
    options: {
      MOBILE: {
        purpose: EcoI18n.t(
          "Vous accordez l’usage de votre IA sans exclusivité jusqu’en décembre."
        ),
        effect: EcoI18n.t(
          "Votre licence reste compatible avec une éventuelle offre d’activité extérieure."),
        condition: EcoI18n.t(
          "Une offre extérieure n’est pas garantie. Le service ne reçoit pas le supplément lié à l’exclusivité."
        )
      },
      COMMITTED: {
        purpose: EcoI18n.t("Vous vous engagez à rester dans ce service jusqu’en décembre."),
        effect: EcoI18n.t(
          "L’engagement ajoute 2 crédits aux recettes totales par trimestre à pleine capacité, partagés selon le contrat."
        ),
        condition: EcoI18n.t(
          "Sans supplément d’installation, vous renoncez à toute activité concurrente avant décembre. Les recettes supplémentaires dépendent des trajets facturés."
        )
      }
    }
  },
  GRID: {
    question: EcoI18n.t(
      "Quelle capacité de recharge installer ?"),
    options: {
      BASE: {
        purpose: EcoI18n.t(
          "Vous préparez les stations de recharge nécessaires au périmètre pilote."),
        effect: EcoI18n.t("La flotte dispose de sa capacité initiale de recharge."),
        condition: EcoI18n.t(
          "Une capacité supplémentaire demandera un investissement si elle devient nécessaire.")
      },
      RESERVE: {
        purpose: EcoI18n.t("Vous financez dès maintenant une réserve de capacité."),
        effect: EcoI18n.t(
          "Une extension ou intervention sur l’infrastructure peut coûter 2 crédits de moins au collectif. La réserve réduit aussi le risque de surcharge à l’extension."
        ),
        condition: EcoI18n.t(
          "Le supplément est payé même sans utilisation. Ses avantages dépendent des besoins locaux, des moyens des partenaires et de votre place dans l’exploitation."
        )
      }
    }
  },
  FLEET: {
    question: EcoI18n.t(
      "Quelle préparation financer pour l’exploitation quotidienne ?"
    ),
    options: {
      LEAN: {
        purpose: EcoI18n.t(
          "Vous organisez l’exploitation et les essais de base nécessaires au lancement."),
        effect: EcoI18n.t(
          "La flotte peut être mise en service après les validations obligatoires."),
        condition: EcoI18n.t(
          "Une interruption reste possible pendant les essais ; les frais d’exploitation engagée restent dus."
        )
      },
      PREPARED: {
        purpose: EcoI18n.t(
          "Vous financez davantage d’essais et de moyens de continuité avant l’ouverture."),
        effect: EcoI18n.t(
          "La préparation réduit les risques d’interruption au lancement et de surcharge à l’extension. Une intervention peut coûter 2 crédits de moins au collectif."
        ),
        condition: EcoI18n.t(
          "Des incidents restent possibles. La dépense est engagée même sans problème ; son effet dépend aussi des autres moyens de préparation du groupe."
        )
      }
    }
  }
};

function profileChoice() {
  const me = C.st.me;
  const guide = PROFILE_GUIDES[me.role];
  const body =
    `<p class="profile-question">${esc(guide.question)}</p><p class="small muted">${me.role}${EcoI18n.t(" paie le supplément choisi une seule fois, lorsque le premier accord prend effet, en plus de son installation de base de ")}${money(me.cost)}${EcoI18n.t(" crédits.</p>")}${me.profile_options.map(([key,title,cost,text])=>{const detail=guide.options[key];return `<article class="profile-option decision-option"><button id="profile-${key}" aria-pressed="${me.profile===key}" onclick="send('profile',{choice:'${key}'})"><span>${esc(title)}</span><span>${money(cost)}${EcoI18n.t(" crédit")}${cost>100?"s":""}${EcoI18n.t(" supplémentaires</span></button><p class=\"option-purpose\">")}${esc(detail.purpose)}${EcoI18n.t("</p><dl class=\"option-effects\"><div><dt>Effet dans le jeu</dt><dd>")}${esc(detail.effect)}${EcoI18n.t("</dd></div><div><dt>À prendre en compte</dt><dd>")}${esc(detail.condition)}</dd></div></dl></article>`;}).join("")}${EcoI18n.t("<p class=\"tiny muted\">Choix révisable avant installation ; tout changement exige une nouvelle proposition collective.</p>")}`;
  return me.profile ?
    `${EcoI18n.t("<details><summary>Votre engagement : ")}${esc(C.st.team.profiles[me.role])}</summary>${body}</details>` :
    `${EcoI18n.t("<section class=\"card\"><h2>Votre engagement · ")}${me.role}</h2>${body}</section>`;
}

function outsideChoice() {
  const me = C.st.me,
    t = C.st.team;
  if (me.outside_position)
    return `${EcoI18n.t("<section class=\"card warn\"><h2>Votre entreprise poursuit une autre activité</h2><p>Gains et investissements sont conservés. Hors exploitation, vous ne touchez aucune recette du transport.</p><button id=\"requestReturn\" ")}${t.return_request?"disabled":""} onclick="send('return_request')">${t.return_request?EcoI18n.t("Votre demande de retour est publiée"):EcoI18n.t("Proposer mon retour à la table")}${EcoI18n.t("</button><p class=\"tiny muted\">Retour soumis à un nouvel accord ; activité extérieure toujours possible.</p></section>")}`;
  if (me.offer?.date !== C.st.phase) return "";
  return `<section class="card private-offer"><h2>${GameVisuals.icon("lock")}${EcoI18n.t(" Une offre pour votre IA · privé</h2><p>Une activité extérieure propose ")}${money(me.outside+me.offer.bonus)}${EcoI18n.t(" crédits par trimestre si vous quittez l’exploitation, jusqu’en décembre.</p>")}${me.can_leave?EcoI18n.t('<button id="leaveCompany" onclick="leaveCompany()">Quitter l’exploitation pour cette activité</button>'):EcoI18n.t('<p class="small muted">Votre engagement actuel ne permet pas ce départ. Vous pouvez discuter des conditions de votre contrat à la table.</p>')}</section>`;
}

function privateCost() {
  const me = C.st.me,
    s = me.private_shock;
  if (!s) return "";
  return `<section class="card private-offer cost-shock ${C.entering?"cost-arrives":""}"><span class="edition">${GameVisuals.icon("lock")}${EcoI18n.t(" Information privée · ")}${me.role}</span><h2>${esc(s.title)}</h2><p>${esc(s.text)}${EcoI18n.t("</p><div class=\"cost-change\"><span>Frais par trimestre engagé</span><b>")}${money(me.base_operating_cost)} <i aria-hidden="true">→</i> ${money(me.operating_cost)}${EcoI18n.t(" <small>crédits</small></b></div><p class=\"small\">Ce nouveau coût s’applique jusqu’en décembre quand votre activité est engagée dans la flotte. Le dernier accord prévoyait ")}${money(C.st.team.contract?.allocations[me.role]??0)}${EcoI18n.t(" crédits de recettes à pleine capacité. Les autres entreprises ne voient pas le montant de cette hausse.</p>")}${!me.outside_position?`${EcoI18n.t("<p class=\"small muted\">Négociez les montants en crédits ou suspendez votre activité si vos droits le permettent. Comparez frais et activité extérieure dans votre dossier.</p><button id=\"requestRenegotiation\" class=\"block\" ")}${C.st.team.renegotiation_requests?.[me.role]?"disabled":""} onclick="send('renegotiate')">${C.st.team.renegotiation_requests?.[me.role]?EcoI18n.t("Votre demande de discussion est publiée"):EcoI18n.t("Demander une renégociation")}</button>${me.can_withdraw?EcoI18n.t('<button id="withdrawCapacity" class="ghost block" onclick="withdrawCapacity()">Suspendre mon activité dans la flotte</button>'):""}`:EcoI18n.t('<p class="small muted">Votre capacité est actuellement hors de l’exploitation : ces frais ne sont pas débités pendant cette période.</p>')}</section>`;
}

function withdrawCapacity() {
  if (confirm(EcoI18n.t(
      "Suspendre votre activité ? La flotte s’arrête jusqu’à un accord de retour ou de remplacement. Les investissements restent engagés ; l’activité extérieure disponible sera rémunérée à la clôture."
    ))) send("withdraw");
}

function renegotiations() {
  const requests = C.st.team.renegotiation_requests || {};
  return Object.keys(requests).length ? GameVisuals.note("message", EcoI18n.t(
    "La discussion est rouverte"), Object.keys(requests).join(", ") + EcoI18n.t(
    " demande une révision. Parts inchangées sans nouvel accord ; chacun contrôle ses informations privées."
  ), "message") : "";
}

function leaveCompany() {
  if (confirm(EcoI18n.t(
      "Quitter l’exploitation ? Votre départ interrompt le service jusqu’à sa recomposition. Vos gains et dépenses antérieurs sont conservés."
    ))) send("leave");
}

function allocation(p) {
  return GameVisuals.shares(p.allocations) +
    `<dl class="allocation">${Object.entries(p.allocations).map(([role,share])=>`<div class="${role===C.st.me.role?"my-allocation":""}" style="--role-color:${GameVisuals.colors[role]||GameVisuals.colors.ALT}"><dt>${role==="ALT"?EcoI18n.t("SUBSTITUT"):role}</dt><dd>${money(share)}<small>${EcoI18n.t("crédits de recettes")}</small></dd><dd class="allocation-investment">${money(p.funding?.[role] || 0)}<small>${EcoI18n.t("crédits investis")}</small></dd></div>`).join("")}</dl>`;
}

function negotiation() {
  const t = C.st.team, role = C.st.me.role, d = C.draft;
  const positions = Object.values(t.positions || {}).filter(p => p.date === C.st.phase);
  const messages = (t.discussion || []).filter(p => p.date === C.st.phase);
  return `<section class="card negotiation"><h2>${EcoI18n.t("Négocier ensemble")}</h2>
    <p class="small">${EcoI18n.t("MOBI répartit les crédits. Chaque partenaire peut proposer ses conditions et expliquer ses décisions. Les demandes et messages sont visibles par toute la table.")}</p>
    <p class="small"><b>${EcoI18n.t("Sans accord unanime pour ce tour : 0 crédit de gain.")}</b></p>
    ${positions.map(p => `<article class="message-entry"><p><b>${esc(p.role)}</b> · ${money(p.minimum)} ${EcoI18n.t("crédits de recettes demandés")} · ${money(p.maximum)} ${EcoI18n.t("crédits d’investissement proposés au maximum")}<br>${esc(p.text)}</p></article>`).join("")}
    ${live() ? `<details><summary>${EcoI18n.t("Publier mes conditions en crédits")}</summary>
      <label for="minimum">${EcoI18n.t("Recettes demandées pour ce tour (crédits)")}</label>
      <input id="minimum" type="number" min="0" max="100" step="0.01" data-k="minimum" value="${esc(d.minimum ?? "")}">
      <label for="maximum">${EcoI18n.t("Investissement collectif maximal proposé (crédits)")}</label>
      <input id="maximum" type="number" min="0" max="100" step="0.01" data-k="maximum" value="${esc(d.maximum ?? "")}">
      <label for="positionText">${EcoI18n.t("Pourquoi ces conditions ?")}</label>
      <textarea id="positionText" maxlength="400" data-k="positionText">${esc(d.positionText ?? "")}</textarea>
      <button class="block" onclick="publishPosition()">${EcoI18n.t("Soumettre mes conditions à la table")}</button>
    </details>` : ""}
    <h3>${EcoI18n.t("Discussion du tour")}</h3>
    ${messages.map(p => `<article class="message-entry"><p><b>${esc(p.role)} → ${p.target === "ALL" ? EcoI18n.t("Toute la table") : esc(p.target)}</b> · V${p.revision}${p.choice ? " · " + (p.choice === "ACCEPT" ? EcoI18n.t("J’accepte") : EcoI18n.t("Je refuse")) : ""}<br>${esc(p.text)}</p></article>`).join("") || `<p class="small muted">${EcoI18n.t("Interrogez un partenaire sur son choix ou proposez une concession.")}</p>`}
    ${live() ? `<label for="discussionTarget">${EcoI18n.t("Interpeller un partenaire (message public)")}</label>
      <select id="discussionTarget" data-k="discussionTarget"><option value="ALL">${EcoI18n.t("Toute la table")}</option>${ROLES.filter(r => r !== role).map(r => `<option value="${r}" ${d.discussionTarget === r ? "selected" : ""}>${r}</option>`).join("")}</select>
      <label for="discussionText">${EcoI18n.t("Question, concession ou explication de votre décision")}</label>
      <textarea id="discussionText" maxlength="400" data-k="discussionText">${esc(d.discussionText ?? "")}</textarea>
      <button class="block" onclick="send('discuss',{target:$('discussionTarget').value,text:$('discussionText').value})">${EcoI18n.t("Envoyer à la table")}</button>` : ""}
  </section>`;
}

function publishPosition() {
  if ($("minimum").value === "" || $("maximum").value === "") {
    toast(EcoI18n.t("Précisez les deux montants en crédits."));
    return;
  }
  send("negotiate", {
    minimum: Math.round(Number($("minimum").value) * 100),
    maximum: Math.round(Number($("maximum").value) * 100),
    text: $("positionText").value
  });
}

function contract(p, title) {
  const t = C.st.team,
    me = C.st.me;
  return `<section class="card"><div class="spread"><h3>${esc(title)}</h3><span class="edition">Version ${p.revision}</span></div>${allocation(p)}${t.full_capacity_revenue!=null?`${EcoI18n.t("<p class=\"small\">Recettes actuelles à pleine capacité : <b>")}${money(t.full_capacity_revenue)}${EcoI18n.t(" crédits par trimestre</b>.")}${t.revenue_adjustment?`${EcoI18n.t(" La baisse de contribution de ")}${money(-t.revenue_adjustment)}${EcoI18n.t(" crédits est déjà déduite.")}`:""}</p>`:""}${EcoI18n.t("<p class=\"tiny muted\">Montants en crédits pour ce tour. Les incidents réduisent les montants versés avec les recettes réelles. Chacun paie ses frais d’exploitation.</p>")}${live()&&C.st.rules_version==="campaign-3.0"&&!me.outside_position&&!me.private_shock?`<button id="requestRenegotiation" class="ghost small" ${t.renegotiation_requests?.[me.role]?"disabled":""} onclick="send('renegotiate')">${t.renegotiation_requests?.[me.role]?EcoI18n.t("Demande de renégociation publiée"):EcoI18n.t("Demander une renégociation")}</button>`:""}</section>`;
}

function proposal() {
  const p = C.st.team.proposal,
    me = C.st.me;
  if (!p || p.status !== "OPEN") return "";
  const myCost = p.funding[me.role] + (p.kind === "INSTALL" ? me.cost + (me.profile_options.find(
    x => x[0] === me.profile)?.[2] || 0) : 0);
  return `${EcoI18n.t("<section class=\"card accent\"><div class=\"spread\"><h3>Proposition à engager</h3><span class=\"edition\">Version ")}${p.revision}</span></div>${allocation(p)}
    ${p.kind==="PAUSE"?EcoI18n.t('<p class="small">Les recettes de transport seront suspendues. Les actifs déjà financés restent installés.</p>'):`${EcoI18n.t("<p class=\"small\">Recettes à pleine capacité : <b>")}${money(p.full_capacity_revenue)}${EcoI18n.t(" crédits par trimestre</b>, avant les frais propres à chaque entreprise.</p>")}`}
    <h3>${esc(actionName(p.kind))}</h3><label for="decisionReason">${EcoI18n.t("Expliquer ma décision à la table (facultatif)")}</label><textarea id="decisionReason" data-k="decisionReason" maxlength="400">${esc(C.draft.decisionReason ?? "")}</textarea>${p.kind==="INSTALL"?`<p class="small muted">Interfaces ${p.architecture==="MODULAR"?EcoI18n.t("communes et documentées"):EcoI18n.t("intégrées sur mesure")} · ${p.launch==="PILOT"?EcoI18n.t("pilote progressif"):EcoI18n.t("ouverture dès validation")}.</p>`:""}
    ${p.consequence?`<p class="small muted">${esc(p.consequence)}</p>`:""}
    ${GameVisuals.note("commit",p.required.includes(me.role)?EcoI18n.t("À l’entrée en vigueur de l’accord"):EcoI18n.t("Votre position"),p.required.includes(me.role)?`${EcoI18n.t("Votre dépense : ")}${money(myCost)}${EcoI18n.t(" crédits.")}`:EcoI18n.t("Votre entreprise ne fait pas partie de cet engagement."),"receipt")}
    ${p.required.includes(me.role)?`${EcoI18n.t("<p class=\"tiny muted\">L’unanimité des partenaires concernés applique l’accord et débite les contributions. Vous pouvez expliquer votre décision dans la discussion partagée.</p><div class=\"choice-pair\"><button id=\"acceptProposal\" aria-pressed=\"")}${p.mine==="ACCEPT"}" onclick="send('consent',{reason:$('decisionReason').value,choice:'ACCEPT',revision:${p.revision}${EcoI18n.t("})\">J’accepte</button><button id=\"refuseProposal\" aria-pressed=\"")}${p.mine==="REFUSE"}" onclick="send('consent',{reason:$('decisionReason').value,choice:'REFUSE',revision:${p.revision}${EcoI18n.t("})\">Je refuse</button></div><p class=\"tiny muted\">Votre réponse : ")}${p.mine==="ACCEPT"?"acceptation":p.mine==="REFUSE"?"refus":EcoI18n.t("non déposée")} · ${p.answered} / ${p.required.length}${EcoI18n.t(" réponses reçues.</p>")}`:""}</section>`;
}
const NAMES = {
  INSTALL: EcoI18n.t("Constituer et mettre en service la flotte"),
  REVISE: EcoI18n.t("Réviser le partage des revenus"),
  GROW: EcoI18n.t("Étendre le service"),
  REPAIR: EcoI18n.t("Adapter et remettre en service"),
  REPLACE: EcoI18n.t("Changer de fournisseur"),
  PAUSE: EcoI18n.t("Suspendre l’exploitation"),
  RESUME: EcoI18n.t("Reprendre l’exploitation"),
  STANDARDIZE: EcoI18n.t("Financer des interfaces communes"),
  RETURN: EcoI18n.t("Réintégrer le partenaire")
};

function actionName(key) {
  return NAMES[key] || key;
}

function setPlan(key, value) {
  C.draft[key] = value;
  render();
}

function selectedPlan() {
  const opts = C.st.team.options;
  return opts.length === 1 ? opts[0].key : opts.some(o => o.key === C.draft.kind) ? C.draft.kind :
    null;
}

function editor() {
  const t = C.st.team,
    kind = selectedPlan(),
    d = C.draft;
  const target = kind === "REPLACE" ? (t.incident?.target || t.missing) : kind === "RETURN" ? null :
    t.replaced;
  const keys = ROLES.filter(r => r !== target).concat(target ? ["ALT"] : []);
  const cost = kind === "INSTALL" ? (d.architecture === "MODULAR" ? 600 : 0) + (d.launch ===
    "PILOT" ? 300 : 0) : (t.options.find(o => o.key === kind)?.cost || 0);
  const revenue = kind === "INSTALL" ? (d.architecture === "MODULAR" ? 3800 : 4000) +
    (t.profile_keys?.MOBI === "SUPPORT" ? 200 : 0) +
    (t.profile_keys?.BRAIN === "COMMITTED" ? 200 : 0) :
    (t.full_capacity_revenue || 0) + (kind === "GROW" && !t.growth ? 1000 : 0) -
    (kind === "STANDARDIZE" && t.architecture === "INTEGRATED" ? 200 : 0) +
    (kind === "RETURN" && t.replaced === "BRAIN" && C.st.team.profile_keys?.BRAIN === "COMMITTED" ? 200 : 0) -
    (kind === "REPLACE" && target === "BRAIN" && C.st.team.profile_keys?.BRAIN === "COMMITTED" ? 200 : 0);
  const total = keys.reduce((s, r) => s + (Number(d["share_" + r]) || 0), 0),
    funded = cost ? ROLES.filter(r => r !== target).reduce((s, r) => s + (Number(d["fund_" + r]) ||
      0), 0) : 0;
  const ready = kind && Math.round(total * 100) === revenue && Math.round(funded * 100) === cost && (!target || Number(d.share_ALT) >=
    6) && (kind !== "INSTALL" || d.architecture && d.launch && ROLES.every(r => t.profiles[r]));
  return `<details class="proposal-editor" ${!t.proposal && !t.installed?"open":""}${EcoI18n.t("><summary>Préparer une proposition · MOBI</summary><p class=\"small muted\">Aucune dépense avant consentement. Une révision annule les réponses précédentes.</p><div class=\"seg\">")}${t.options.map(o=>`<button id="plan-${o.key}" aria-pressed="${kind===o.key}" onclick="setPlan('kind','${o.key}')">${esc(o.label)}</button>`).join("")}</div>${!kind?"":`${kind==="INSTALL"?`${EcoI18n.t("<h3 style=\"margin-top:1rem\">Les interfaces</h3><div class=\"seg\"><button id=\"arch-INTEGRATED\" aria-pressed=\"")}${d.architecture==="INTEGRATED"}${EcoI18n.t("\" onclick=\"setPlan('architecture','INTEGRATED')\">Intégrées sur mesure</button><button id=\"arch-MODULAR\" aria-pressed=\"")}${d.architecture==="MODULAR"}${EcoI18n.t("\" onclick=\"setPlan('architecture','MODULAR')\">Communes et documentées</button></div><p class=\"small muted\">Sur mesure : 40 crédits/trimestre, interfaces spécifiques. Communes : 38 crédits/trimestre, 6 crédits d’installation, remplacement facilité. MOBI et BRAIN peuvent ajouter des recettes.</p><h3>Le lancement</h3><div class=\"seg\"><button id=\"launch-EARLY\" aria-pressed=\"")}${d.launch==="EARLY"}${EcoI18n.t("\" onclick=\"setPlan('launch','EARLY')\">Ouvrir dès validation</button><button id=\"launch-PILOT\" aria-pressed=\"")}${d.launch==="PILOT"}${EcoI18n.t("\" onclick=\"setPlan('launch','PILOT')\">Pilote progressif</button></div><p class=\"small muted\">Ouverture : pleine capacité, tests de base. Pilote : 3 crédits de préparation, trois quarts des recettes au premier trimestre exploité, risque d’interruption réduit. Sécurité obligatoire dans les deux cas.</p>")}`:""}${kind==="GROW"?EcoI18n.t('<p class="small">L’extension ajoute 10 crédits de recettes par trimestre de service, avec un risque de surcharge au premier trimestre. Les réserves de GRID et la préparation de FLEET réduisent ce risque.</p>'):""}${EcoI18n.t("<h3 style=\"margin-top:1rem\">Partager les recettes en crédits pour ce tour</h3><div class=\"edit-grid\">")}${keys.map(r=>`<label>${r==="ALT"?EcoI18n.t("Substitut · minimum 6 crédits"):r}<input id="share_${r}" type="number" min="0" max="100" step="0.01" data-k="share_${r}" value="${esc(d["share_"+r]??"")}"></label>`).join("")}</div><p class="small">Total : ${money(Math.round(total * 100))} / ${money(revenue)} ${EcoI18n.t("crédits")}</p>${cost?`${EcoI18n.t("<h3>Financer ")}${money(cost)}${EcoI18n.t(" crédits d’investissement collectif</h3><div class=\"edit-grid\">")}${ROLES.filter(r=>r!==target).map(r=>`<label>${r}<input id="fund_${r}" type="number" min="0" max="100" step="0.01" data-k="fund_${r}" value="${esc(d["fund_"+r]??0)}"></label>`).join("")}${EcoI18n.t("</div><p class=\"small\">Financé : ")}${funded} / ${money(cost)}${EcoI18n.t(" crédits. Les investissements privés d’installation s’ajoutent à ces contributions.</p>")}`:""}<button id="publishProposal" class="primary block" ${ready?"":"disabled"}${EcoI18n.t(" onclick=\"publish()\">Publier cette proposition</button>")}${kind==="INSTALL" && !ROLES.every(r=>t.profiles[r])?EcoI18n.t('<p class="small muted">Chaque entreprise doit encore préciser son engagement d’installation.</p>'):""}`}</details>`;
}

function publish() {
  const t = C.st.team,
    d = C.draft,
    kind = selectedPlan();
  const target = kind === "REPLACE" ? (t.incident?.target || t.missing) : kind === "RETURN" ? null :
    t.replaced;
  const keys = ROLES.filter(r => r !== target).concat(target ? ["ALT"] : []);
  const cost = kind === "INSTALL" ? (d.architecture === "MODULAR" ? 600 : 0) + (d.launch ===
    "PILOT" ? 300 : 0) : (t.options.find(o => o.key === kind)?.cost || 0);
  send("propose", {
    kind,
    architecture: d.architecture,
    launch: d.launch,
    allocations: Object.fromEntries(keys.map(r => [r, Math.round((Number(d["share_" + r]) || 0) * 100)])),
    funding: Object.fromEntries(ROLES.map(r => [r, cost && r !== target ? Math.round((Number(d["fund_" +
      r]) || 0) * 100) : 0]))
  });
}

function company() {
  const me = C.st.me;
  return heading(EcoI18n.t("Dossier confidentiel"), me.role + " · " + ASSETS[me.role], EcoI18n.t(
      "Vous choisissez quelles informations révéler."
    ), me.role) +
    `<p>${esc(me.card.brief)}${EcoI18n.t("</p><div class=\"private-ledger\"><div><span>Trésorerie disponible</span><b>")}${money(me.cash)}${EcoI18n.t(" <small>crédits</small></b></div><div><span>Dotation unique au début de l’année</span><b>")}${money(me.initial)}</b></div><div><span>${C.st.team.installed?EcoI18n.t("Installation de base déjà payée"):EcoI18n.t("Installation de base à financer une fois")}</span><b>${money(me.cost)}${EcoI18n.t("</b></div><div><span>Frais par trimestre d’exploitation engagée</span><b>")}${money(me.operating_cost)}${EcoI18n.t("</b></div><div><span>Revenu trimestriel de votre activité extérieure de base</span><b>")}${money(me.outside)}</b></div></div>${me.profile?`${EcoI18n.t("<p class=\"small\">Engagement choisi : ")}${esc(C.st.team.profiles[me.role])} · ${money(me.profile_cost)}${EcoI18n.t(" crédit(s) en plus. ")}${C.st.team.installed?EcoI18n.t("Investissement déjà engagé."):EcoI18n.t("À financer à la signature du premier accord.")}</p>`:""}${EcoI18n.t("<p class=\"tiny muted\">Une dépense collective acceptée peut s’ajouter à votre installation. La trésorerie conserve tous les paiements de l’année.</p>")}${!C.st.team.installed && live()?profileChoice():""}${privateCost()}${transactions()}${rules()}`;
}

function transactions() {
  const labels = {
    INSTALLATION: "Installation",
    PROFILE: EcoI18n.t("Engagement supplémentaire"),
    ADAPTATION: EcoI18n.t("Investissement collectif"),
    OPERATION: EcoI18n.t("Frais d’exploitation"),
    REVENUE: EcoI18n.t("Part des recettes du transport"),
    OUTSIDE: EcoI18n.t("Activité extérieure")
  };
  return `${EcoI18n.t("<details><summary>Les mouvements de ma trésorerie</summary><table><tbody>")}${C.st.me.transactions.map(row=>`<tr><td>${dateName(row.economic_date)}<span class="seat-asset">${labels[row.kind]||row.kind}</span></td><td class="num">${row.amount>0?"+":""}${money(row.amount)}</td></tr>`).join("")||EcoI18n.t('<tr><td>Aucun paiement à ce jour.</td></tr>')}</tbody></table></details>`;
}

function inspectRole(role) {
  if (ROLES.includes(role)) {
    C.inspectRole = role;
    render();
  }
}

function table() {
  const t = C.st.team;
  return heading(EcoI18n.t("Territoire ") + t.team, EcoI18n.t("La table"), EcoI18n.t(
      "Les cinq activités du transport autonome."
    )) +
    GameVisuals.ecosystem(t, C.st.me.role, C.inspectRole) + negotiation() +
    `${EcoI18n.t("<section class=\"card\"><h2>Paroles de la table</h2>")}${ROLES.filter(r=>t.claims[r]?.text).map(r=>`<div class="message-entry" style="--role-color:${GameVisuals.colors[r]}">${GameVisuals.icon(r)}<p><b>${r}</b><br>${esc(t.claims[r].text)}</p></div>`).join("")||EcoI18n.t('<p class="small muted">Aucun message publié.</p>')}${live()?`${EcoI18n.t("<label for=\"claimText\">Ce que vous souhaitez dire aux partenaires</label><input id=\"claimText\" type=\"text\" maxlength=\"160\" data-k=\"claimText\" value=\"")}${esc(C.draft.claimText??t.claims[C.st.me.role]?.text??"")}${EcoI18n.t("\"><button class=\"block\" style=\"margin-top:.6rem\" onclick=\"send('claim',{text:$('claimText').value})\">Prendre la parole →</button>")}`:""}</section>${history()}`;
}

function history() {
  const groups = [];
  C.st.team.history.forEach(event => {
    let group = groups[groups.length - 1];
    if (!group || group.date !== event.date) {
      group = {
        date: event.date,
        messages: []
      };
      groups.push(group);
    }
    group.messages.push(event.text);
  });
  return `${EcoI18n.t("<details><summary>L’histoire de votre territoire</summary><ol class=\"story-timeline\">")}${groups.map(group=>`<li><b>${esc(dateName(group.date))}</b>${group.messages.map(text=>`<p>${esc(text)}</p>`).join("")}</li>`).join("")||EcoI18n.t('<li><p>Le mandat de la ville ouvre votre histoire.</p></li>')}</ol></details>`;
}

function dateName(key) {
  return {
    JANUARY: EcoI18n.t("Janvier"),
    APRIL: EcoI18n.t("Avril"),
    JULY: EcoI18n.t("Juillet"),
    OCTOBER: EcoI18n.t("Octobre"),
    FINAL: EcoI18n.t("Décembre"),
    DEBRIEF: EcoI18n.t("Débrief")
  } [key] || EcoI18n.t("Accueil");
}

function rules() {
  return `${EcoI18n.t("<details class=\"game-rules\"><summary>Les règles utiles pour décider</summary><p class=\"small\">Dotation unique : 20 crédits. Améliorez le résultat annuel de votre entreprise, sans remise à zéro entre les dates.</p><p class=\"small\">Toutes les entreprises concernées doivent accepter la proposition ; les contributions sont alors payées. Les recettes et investissements sont négociés en crédits à chaque tour. Les frais d’exploitation engagée restent dus, même si essais ou délais interrompent les recettes.</p><p class=\"small\">L’enseignant clôt le trimestre pour tous, même sans accord partout ; le chronomètre ne le fait pas. Sans flotte, aucune recette de transport. Le groupe peut négocier à la date suivante, sans rattrapage ni blocage des autres territoires.</p><p class=\"small\">Toutes les activités doivent être assurées pour facturer les trajets. Une capacité disponible hors exploitation peut percevoir un revenu extérieur, sans double rémunération. Les circonstances locales varient selon les groupes.</p><p class=\"small\">Aucun accord ne rembourse les dépenses passées. Sans accord unanime à chaque tour : gain nul, sans frais d’exploitation ni revenu extérieur. Le contrat précédent ne produit aucun gain. Un binôme partage entreprise et décision.</p><button class=\"small ghost\" onclick=\"EcoIntro.open()\">Revoir le briefing animé →</button></details>")}`;
}

function final() {
  const t = C.st.team,
    me = C.st.me;
  return heading(EcoI18n.t("Décembre 2032"), EcoI18n.t("Votre année a laissé des traces."), EcoI18n
      .t("Vos résultats cumulés et leur histoire.")) +
    quarterReceipt() + `<div class="kpi"><div><b>${money(me.cash-me.initial)}${EcoI18n.t("</b><span>Résultat de votre entreprise · crédits</span></div><div><b>")}${money(t.created)}${EcoI18n.t("</b><span>Valeur collective du transport · crédits</span></div></div><section class=\"card\"><h2>Entreprises de votre territoire</h2><table><thead><tr><th>Entreprise</th><th class=\"num\">Trésorerie</th><th class=\"num\">Résultat annuel</th></tr></thead><tbody>")}${ROLES.map(r=>`<tr class="${r===me.role?"me":""}"><td>${r}</td><td class="num">${money(t.cash[r])}</td><td class="num">${money(t.cash[r]-me.initial)}</td></tr>`).join("")}${EcoI18n.t("</tbody></table></section><p class=\"small muted\">Les activités extérieures contribuent au résultat individuel. La valeur collective du transport rapproche les recettes clients et les coûts réels, sans compter deux fois les parts distribuées.</p>")}${history()}`;
}
document.addEventListener("input", event => {
  const key = event.target.dataset.k;
  if (!key) return;
  C.draft[key] = event.target.value;
  if (key.startsWith("share_") || key.startsWith("fund_")) render();
});
$("gojoin").addEventListener("click", join);
$("pname").addEventListener("keydown", e => {
  if (e.key === "Enter") $("plastname").focus();
});
$("plastname").addEventListener("keydown", e => {
  if (e.key === "Enter") $("pcode").focus();
});
$("pcode").addEventListener("keydown", e => {
  if (e.key === "Enter") join();
});
$("pcode").value = (new URLSearchParams(location.search).get("c") || localStorage.getItem(
  "eco_code") || "").toUpperCase();
if (C.token) start();
else $("pname").focus();
