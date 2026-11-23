/* Vues du present : uniquement les faits publics deja recus du moteur. */
"use strict";
(() => {
  const roles = ["MOBI", "AUTO", "BRAIN", "GRID", "FLEET"];
  const colors = {MOBI:"#78e5ee", AUTO:"#efcf79", BRAIN:"#c2a8ff", GRID:"#85e0b2", FLEET:"#7abfff", ALT:"#b4c3ce"};
  const assets = {MOBI:"Voyageurs", AUTO:EcoI18n.t("Véhicules"), BRAIN:EcoI18n.t("Conduite IA"), GRID:"Recharge", FLEET:EcoI18n.t("Exploitation")};
  const descriptions = {
    MOBI:EcoI18n.t("L’application relie les voyageurs au service : réservation, paiement et relation client. MOBI coordonne les propositions d’accord."),
    AUTO:EcoI18n.t("Les véhicules doivent être produits et adaptés aux trajets. AUTO apporte cette capacité au territoire."),
    BRAIN:EcoI18n.t("L’intelligence artificielle assure la conduite autonome. Son droit d’usage doit être compatible avec le projet."),
    GRID:EcoI18n.t("Les navettes ont besoin de stations de recharge et de dépôts. GRID engage les infrastructures nécessaires."),
    FLEET:EcoI18n.t("Une flotte doit être exploitée chaque jour : supervision, repositionnement et gestion des incidents. FLEET assure ces opérations.")
  };
  const paths = {
    MOBI:'<rect x="7" y="2" width="10" height="20" rx="1"/><path d="M10 5h4M10 18h4M10 11l2 2 4-4"/>',
    AUTO:'<path d="M3 17V7l3-3h11l4 5v8H3Z M3 11h18M8 4v7m8-7v7"/><path d="M6 17v3m12-3v3"/>',
    BRAIN:'<rect x="6" y="6" width="12" height="12"/><path d="M9 2v4m6-4v4M9 18v4m6-4v4M2 9h4m-4 6h4m12-6h4m-4 6h4M9 12l2 2 4-4"/>',
    GRID:'<path d="M5 21V5h11v16M3 21h15M16 9h3l2 3v6h-3v-5h-2M11 7l-3 5h4l-3 5"/>',
    FLEET:'<rect x="3" y="3" width="18" height="13"/><path d="M7 21h10m-5-5v5M6 11h3l2-4 3 6 2-3h2"/>',
    fleet:'<path d="M3 17V8l3-4h11l4 5v8H3Z M7 4v7h11M3 11h4M8 14h2m4 0h2M6 17v3m12-3v3"/>',
    alert:'<path d="M12 3L2 21h20L12 3Zm0 6v5m0 3v1"/>',
    receipt:'<path d="M5 22V2h14v20l-3-2-4 2-4-2-3 2ZM9 7h6m-6 4h6m-6 4h4"/>',
    lock:'<rect x="5" y="10" width="14" height="11"/><path d="M8 10V6a4 4 0 0 1 8 0v4m-4 4v3"/>',
    message:'<path d="M3 4h18v12H9l-6 5V4ZM7 8h10M7 12h7"/>'
  };
  const escape = value => String(value ?? "").replace(/[&<>"']/g, c => ({"&":"&amp;","<":"&lt;",">":"&gt;",'"':"&quot;","'":"&#39;"}[c]));
  function icon(key) {
    return `<svg class="game-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="square" stroke-linejoin="miter" aria-hidden="true">${paths[key] || paths.fleet}</svg>`;
  }
  function note(tone, title, text, key="message") {
    return `<aside class="visual-note note-${tone}">${icon(key)}<div><span class="note-label">${escape(title)}</span><p>${escape(text)}</p></div></aside>`;
  }
  function mode(team) {
    if (team.node === "CLOSED") return ["closed", EcoI18n.t("Année clôturée")];
    if (!team.installed) return ["planning", EcoI18n.t("Flotte à constituer")];
    if (team.incident || team.missing) return ["interrupted", EcoI18n.t("Trajets interrompus")];
    return team.operating ? ["running", EcoI18n.t("Exploitation engagée")] : ["paused", EcoI18n.t("Exploitation suspendue")];
  }
  function fleet(team) {
    const [state, label] = mode(team);
    return `<figure class="fleet-map fleet-${state}${EcoI18n.t("\" aria-label=\"Schéma de la flotte : ")}${label}${EcoI18n.t("\">\n      <figcaption><span class=\"edition\">Territoire ")}${escape(team.team)}</span><strong><i aria-hidden="true"></i>${label}</strong></figcaption>
      <svg viewBox="0 0 360 155" fill="none" aria-hidden="true">
        <g class="fleet-buildings"><path d="M12 84V50h26v34m13 0V22h28v62m17 0V41h40v43m142 0V27h24v57m13 0V47h32v37M58 33h12m-12 12h12m-12 12h12m215-19h11m-11 12h11M104 52h23m-23 12h23"/></g>
        <path class="fleet-road" d="M19 106H341M19 130H341"/>
        <path class="fleet-route" d="M38 118H322"/>
        ${team.growth?'<path class="fleet-extension" d="M174 118V76h80V44h72"/><path class="fleet-stop" d="M321 39h10v10h-10z"/>':""}
        <path class="fleet-stop" d="M33 113h10v10H33zm284 0h10v10h-10z"/>
        <g class="fleet-depot"><path d="M152 91V58l24-16 24 16v33M163 91V68h26v23M172 52h8"/></g>
        <g class="fleet-shuttle"><path d="M0 115V99l5-6h31l8 8v14H0Z"/><path d="M8 97h11v9H8zm17 0h8l6 9H25zM6 115v4m29-4v4"/></g>
        <g class="fleet-charger"><path d="M245 91V61h15v30m-19 0h23m-11-25-5 8h6l-5 9m11-14h6l4 5v11h-5v-9h-5"/></g>
        ${state==="interrupted"?'<g class="fleet-break"><path d="M206 109l16 18m0-18-16 18"/></g>':""}
      </svg>
      <div class="fleet-caption"><span>${team.growth?EcoI18n.t("Périmètre étendu"):EcoI18n.t("Périmètre pilote")}${EcoI18n.t("</span><span>Schéma de service · hors échelle</span></div>\n    </figure>")}`;
  }
  function status(team, role) {
    if (team.missing === role) return ["missing", EcoI18n.t("Position vacante")];
    if (team.replaced === role) return ["substitute", EcoI18n.t("Substitut en place")];
    if (team.incident?.target === role) return ["interrupted", EcoI18n.t("Activité interrompue")];
    if (team.installed) return ["installed", EcoI18n.t("Activité installée")];
    return team.profiles[role] ? ["defined", EcoI18n.t("Apport défini")] : ["pending", EcoI18n.t("Apport à définir")];
  }
  function ecosystem(team, myRole, inspected) {
    const selected = roles.includes(inspected) ? inspected : myRole;
    const [current, label] = status(team, selected);
    const names = team.seats[selected].bot ? EcoI18n.t("Siège automatique") : team.seats[selected].names.join(", ");
    const profiles = team.profiles[selected];
    const position = {MOBI:[180,28],AUTO:[51,128],BRAIN:[309,128],GRID:[93,265],FLEET:[267,265]};
    const state = mode(team);
    return `${EcoI18n.t("<section class=\"ecosystem-panel\"><div class=\"spread\"><h2>Les cinq activités</h2><span class=\"edition\">Touchez une entreprise</span></div>\n      <div class=\"ecosystem-map\">\n        <svg class=\"ecosystem-links\" viewBox=\"0 0 360 300\" preserveAspectRatio=\"none\" aria-hidden=\"true\">")}${roles.map(role=>`<path class="link-${status(team,role)[0]}" style="--role-color:${colors[role]}" d="M${position[role][0]} ${position[role][1]}L180 155"/>`).join("")}</svg>
        <div class="ecosystem-core">${icon("fleet")}${EcoI18n.t("<b>Flotte autonome</b><span>")}${state[0]==="interrupted"?EcoI18n.t("À rétablir"):team.installed?EcoI18n.t("Activités réunies"):EcoI18n.t("À assembler")}</span></div>
        ${roles.map(role=>{
          const [key, text] = status(team,role);
          return `<button type="button" id="role-map-${role}" class="ecosystem-node node-${role} state-${key} ${role===myRole?"is-mine":""}" data-role="${role}" data-status="${key}" style="--role-color:${colors[role]}" aria-label="${role} · ${assets[role]} · ${text}${role===myRole?EcoI18n.t(" · Votre rôle"):""}" aria-pressed="${selected===role}" aria-controls="role-insight" onclick="inspectRole('${role}')">${icon(role)}<b>${role}${role===myRole?`<small>${key==="missing"||key==="substitute"?"HORS":EcoI18n.t("VOUS")}</small>`:""}</b><span>${assets[role]}</span><i class="node-status" aria-hidden="true"></i></button>`;
        }).join("")}${EcoI18n.t("\n      </div><p class=\"ecosystem-key\"><span><i class=\"key-your\"></i>Votre rôle</span><span><i class=\"key-attention\"></i>Position ou activité à rétablir</span></p>\n      <div id=\"role-insight\" class=\"role-insight insight-")}${current}${EcoI18n.t("\" role=\"region\" aria-label=\"Activité sélectionnée\" style=\"--role-color:")}${colors[selected]}"><div class="role-insight-heading">${icon(selected)}<div><b>${selected} · ${assets[selected]}</b><span>${escape(names)}</span></div><span class="role-state">${label}</span></div>
      <p>${descriptions[selected]}</p>${current==="substitute"?EcoI18n.t('<p class="small">Cette position est assurée par un fournisseur extérieur. L’entreprise initiale poursuit son activité hors de l’exploitation et peut proposer son retour.</p>'):current==="missing"?EcoI18n.t('<p class="small">L’entreprise a quitté l’exploitation. Cette activité doit être couverte par un nouvel accord pour permettre les trajets.</p>'):profiles?`${EcoI18n.t("<p class=\"role-profile\">Engagement annoncé : ")}${escape(profiles)}.</p>`:EcoI18n.t('<p class="role-profile">L’engagement d’installation reste à préciser.</p>')}</div></section>`;
  }
  function shares(values) {
    const label = Object.entries(values).map(([role, value]) => `${role==="ALT"?EcoI18n.t("Substitut"):role} ${new Intl.NumberFormat(EcoI18n.locale).format(value / 100)} ${EcoI18n.t("crédits")}`).join(", ");
    return `${EcoI18n.t("<div class=\"share-ribbon\" role=\"img\" aria-label=\"Répartition des recettes : ")}${escape(label)}">${Object.entries(values).filter(([,value])=>value>0).map(([role,value])=>`<span style="flex:${Number(value)};--role-color:${colors[role]||colors.ALT}" title="${escape(role)} · ${new Intl.NumberFormat(EcoI18n.locale).format(value / 100)} ${EcoI18n.t("crédits")}"></span>`).join("")}</div>`;
  }
  window.GameVisuals = {icon,note,fleet,ecosystem,shares,colors};
})();
