/* Vues du débrief, calculées à partir des faits enregistrés, sans dépendance réseau. */
"use strict";
(() => {
  const colors = {
    BLUE: "#7abfff",
    GREEN: "#85e0b2",
    RED: "#ff9c92",
    YELLOW: "#efcf79",
    PURPLE: "#c2a8ff",
    ORANGE: "#ffb47e"
  };
  const roleColors = {
    MOBI: "#78e5ee",
    AUTO: "#efcf79",
    BRAIN: "#c2a8ff",
    GRID: "#85e0b2",
    FLEET: "#7abfff",
    ALT: "#e8ac87"
  };
  const dates = ["JANUARY", "APRIL", "JULY", "OCTOBER"],
    dateLabels = {
      JANUARY: EcoI18n.t("Jan–mars"),
      APRIL: EcoI18n.t("Avr–juin"),
      JULY: EcoI18n.t("Juil–sept"),
      OCTOBER: EcoI18n.t("Oct–déc")
    };
  const eventLabels = {
    ORDINARY: EcoI18n.t("Période calme"),
    EXISTING_SITUATION: EcoI18n.t("Situation déjà en attente"),
    DEMAND: EcoI18n.t("Demande supplémentaire"),
    PARTNER: EcoI18n.t("Offre extérieure"),
    PRIVATE_COST: EcoI18n.t("Hausse privée des frais"),
    PRICE_DROP: EcoI18n.t("Baisse des recettes"),
    INFRA: EcoI18n.t("Recharge indisponible"),
    AUDIT: "Certification"
  };
  const actionLabels = {
    INSTALL: EcoI18n.t("Lancement"),
    REVISE: EcoI18n.t("Nouveau partage"),
    REPAIR: "Adaptation",
    REPLACE: EcoI18n.t("Remplacement"),
    RETURN: EcoI18n.t("Retour"),
    GROW: "Extension",
    PAUSE: "Suspension",
    RESUME: EcoI18n.t("Reprise"),
    STANDARDIZE: EcoI18n.t("Interfaces communes")
  };
  const categories = {
    circumstance: [EcoI18n.t("Circonstance / essai"), "#efcf79"],
    decision: [EcoI18n.t("Décision des joueurs"), "#78e5ee"],
    outcome: [EcoI18n.t("Conséquence observée"), "#e8ac87"],
    context: [EcoI18n.t("Contexte maintenu"), "#8fa7b5"]
  };
  const views = {
    trajectory: EcoI18n.t("Trajectoires"),
    value: EcoI18n.t("Création de valeur"),
    actors: EcoI18n.t("Résultats des entreprises"),
    contracts: EcoI18n.t("Contrats"),
    events: EcoI18n.t("Chocs et réactions")
  };
  const metrics = {
    created: EcoI18n.t("Valeur collective cumulée"),
    revenue: EcoI18n.t("Recettes du trimestre"),
    company_result: EcoI18n.t("Résultats cumulés des cinq entreprises")
  };
  const state = {
    data: null,
    team: null,
    view: "trajectory",
    metric: "created",
    date: "APRIL",
    projection: false
  };
  const safe = v => String(v ?? "").replace(/[&<>"']/g, c => ({
    "&": "&amp;",
    "<": "&lt;",
    ">": "&gt;",
    '"': "&quot;",
    "'": "&#39;"
  } [c]));
  const number = n => new Intl.NumberFormat(EcoI18n.locale, {
    maximumFractionDigits: 2
  }).format((n === 0 ? 0 : n) / 100);
  const signed = n => (n > 0 ? "+" : "") + number(n);
  const text = (x, y, value, extra = "") =>
    `<text x="${x}" y="${y}" ${extra}>${safe(value)}</text>`;
  const svg = (title, body, height = 420) =>
    `<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 1000 ${height}" role="${body.includes('role="button"')?"group":"img"}" aria-label="${safe(title)}"><title>${safe(title)}</title>${body}</svg>`;
  const team = () => state.data.teams.find(t => t.team === state.team) || state.data.teams[0];
  const title = e => eventLabels[e.title] || e.title;
  const legend = items =>
    `<div class="db-legend">${items.map(([label,color])=>`<span><i style="background:${color}"></i>${safe(label)}</span>`).join("")}</div>`;

  function table(headers, rows) {
    return `${EcoI18n.t("<details class=\"db-table\"><summary>Consulter les chiffres et faits exacts</summary><div class=\"db-scroll\" tabindex=\"0\" role=\"region\" aria-label=\"Données du graphique\"><table><thead><tr>")}${headers.map(h=>`<th scope="col">${safe(h)}</th>`).join("")}</tr></thead><tbody>${rows.map(row=>`<tr>${row.map(v=>`<td>${safe(v)}</td>`).join("")}</tr>`).join("")}</tbody></table></div></details>`;
  }

  function panel(titleText, subtitle, graphic, rows, headers, question, note, extra = "", key =
    "") {
    state.exportRows = [headers, ...rows];
    state.exportTitle = titleText;
    return `<section class="db-panel" id="debriefPanel" aria-labelledby="dbChartTitle"><header><span class="edition">${safe(key)}</span><h2 id="dbChartTitle">${safe(titleText)}</h2><p>${safe(subtitle)}</p></header>${extra}${EcoI18n.t("<figure id=\"debriefChart\"><div class=\"db-scroll db-chart\" tabindex=\"0\" role=\"region\" aria-label=\"Graphique défilable horizontalement sur petit écran\">")}${graphic}</div><figcaption>${safe(note)}${EcoI18n.t("</figcaption></figure><div class=\"db-downloads\"><button class=\"small ghost\" id=\"downloadChart\" onclick=\"Debrief.downloadSVG()\">Télécharger le graphique · SVG</button><button class=\"small ghost\" id=\"downloadChartCSV\" onclick=\"Debrief.downloadCSV()\">Données de cette vue · CSV</button></div>")}${table(headers,rows)}${EcoI18n.t("<aside class=\"db-question\"><span>Pour la discussion</span><p>")}${safe(question)}</p></aside></section>`;
  }

  function domain(values) {
    let lo = Math.min(0, ...values),
      hi = Math.max(100, ...values);
    const pad = (hi - lo) * .07;
    return [lo < 0 ? lo - pad : 0, hi > 0 ? hi + pad : 0];
  }

  function ticks(lo, hi) {
    const raw = (hi - lo) / 4,
      unit = 10 ** Math.floor(Math.log10(raw)),
      ratio = raw / unit,
      step = (ratio <= 1 ? 1 : ratio <= 2 ? 2 : ratio <= 2.5 ? 2.5 : ratio <= 5 ? 5 : 10) * unit;
    const values = [];
    for (let v = Math.ceil(lo / step) * step; v <= hi; v += step) values.push(v);
    return values;
  }

  function trajectory() {
    const metric = state.metric,
      teams = state.data.teams,
      [lo, hi] = domain(teams.flatMap(t => t.periods.map(p => p[metric])));
    const y = v => 345 - (v - lo) / (hi - lo) * 290,
      x = i => 85 + i * 220;
    let body = text(20, 22, EcoI18n.t("Crédits"));
    for (const v of ticks(lo, hi)) {
      body += `<line class="db-grid" x1="85" x2="965" y1="${y(v)}" y2="${y(v)}"/>` + text(72, y(
        v) + 5, number(v), 'text-anchor="end"');
    }
    body += `<line class="db-zero" x1="85" x2="965" y1="${y(0)}" y2="${y(0)}"/>`;
    [EcoI18n.t("Départ"), ...dates.map(d => dateLabels[d])].forEach((label, i) => body += text(x(
      i), 380, label, `text-anchor="${i===4?"end":i===0?"start":"middle"}"`));
    const rows = [];
    teams.forEach(t => {
      const points = [
        [x(0), y(0)], ...t.periods.map(p => [x(dates.indexOf(p.date) + 1), y(p[metric])])
      ];
      body +=
        `<polyline fill="none" stroke="${colors[t.team]}" stroke-width="${t.team===state.team?4:2}" opacity="${t.team===state.team?1:.5}" points="${points.map(p=>p.join(",")).join(" ")}"/>`;
      t.periods.forEach(p => {
        const label =
          `${t.team} · ${dateLabels[p.date]} : ${number(p[metric])}${EcoI18n.t(" crédits. Afficher les événements de cette période.")}`;
        body +=
          `<circle class="db-point" cx="${x(dates.indexOf(p.date)+1)}" cy="${y(p[metric])}" r="5" fill="${colors[t.team]}" tabindex="0" role="button" aria-label="${safe(label)}" onclick="Debrief.inspect('${t.team}','${p.date}')" onkeydown="Debrief.activate(event,'${t.team}','${p.date}')"><title>${safe(label)}</title></circle>`;
        rows.push([t.team, dateLabels[p.date], number(p[metric])]);
      });
    });
    const controls =
      `${EcoI18n.t("<label class=\"db-metric\" for=\"debriefMetric\">Mesure affichée<select id=\"debriefMetric\" onchange=\"Debrief.setMetric(this.value)\">")}${Object.entries(metrics).map(([k,v])=>`<option value="${k}" ${k===metric?"selected":""}>${v}</option>`).join("")}</select></label>` +
      legend(teams.map(t => [t.team, colors[t.team]]));
    return panel(metrics[metric], EcoI18n.t(
      "Tous les territoires sont comparés ; le territoire choisi est mis en évidence. Cliquez sur un point pour retrouver les faits de la période."
      ), svg(metrics[metric], body), rows, [EcoI18n.t("Territoire"), EcoI18n.t("Période"),
      EcoI18n.t("Crédits")
    ], EcoI18n.t(
      "À quel moment les trajectoires divergent-elles ? Quel événement et quelle décision précèdent cet écart ?"
      ), metric === "company_result" ? EcoI18n.t(
      "Somme des résultats des cinq entreprises, revenus extérieurs compris, hors dotations initiales."
      ) : metric === "created" ? EcoI18n.t(
      "Recettes du transport moins coûts réels cumulés, y compris installation et fournisseur extérieur. Les revenus extérieurs sont exclus."
      ) : EcoI18n.t(
      "Recettes réellement facturées par trimestre, avant les coûts. Le départ représente la situation avant tout engagement."
      ), controls, EcoI18n.t("Complémentarités · dépendance au sentier"));
  }

  function value() {
    const t = team(),
      f = t.finances,
      steps = [
        [EcoI18n.t("Recettes"), f.revenue],
        ["Installation", -f.installation],
        [EcoI18n.t("Adaptations"), -f.adaptation],
        [EcoI18n.t("Exploitation"), -f.operation],
        [EcoI18n.t("Substitut"), -f.supplier],
        [EcoI18n.t("Valeur créée"), f.created]
      ];
    let balance = 0;
    const bars = steps.map(([label, amount], i) => {
      const start = i === 5 ? 0 : balance,
        end = i === 5 ? amount : balance + amount;
      if (i !== 5) balance = end;
      return {
        label,
        amount,
        start,
        end
      };
    });
    const [lo, hi] = domain(bars.flatMap(b => [b.start, b.end])), y = v => 335 - (v - lo) / (hi -
      lo) * 280;
    let body = text(20, 22, EcoI18n.t("Crédits"));
    for (const v of ticks(lo, hi)) {
      body += `<line class="db-grid" x1="85" x2="965" y1="${y(v)}" y2="${y(v)}"/>` + text(70, y(
        v) + 5, number(v), 'text-anchor="end"');
    }
    body += `<line class="db-zero" x1="85" x2="965" y1="${y(0)}" y2="${y(0)}"/>`;
    bars.forEach((b, i) => {
      const left = 105 + i * 145,
        top = Math.min(y(b.start), y(b.end)),
        height = Math.abs(y(b.start) - y(b.end));
      body +=
        `<rect x="${left}" y="${top}" width="105" height="${Math.max(1,height)}" fill="${i===5?(b.amount>=0?"#85e0b2":"#e8ac87"):i===0?"#78e5ee":"#efcf79"}"><title>${safe(b.label)} : ${signed(b.amount)}${EcoI18n.t(" crédits</title></rect>")}` +
        text(left + 52, top - 10, signed(b.amount), 'text-anchor="middle" class="db-value"') +
        text(left + 52, 375, b.label, 'text-anchor="middle"');
      if (i < 4) body +=
        `<line class="db-connector" x1="${left+105}" x2="${left+145}" y1="${y(b.end)}" y2="${y(b.end)}"/>`;
    });
    const equation =
      `<p class="db-equation"><b>${number(f.created)}${EcoI18n.t("</b> de valeur du transport + <b>")}${number(f.outside)}${EcoI18n.t("</b> de revenus extérieurs = <b>")}${number(f.company_result)}${EcoI18n.t("</b> de résultats cumulés des entreprises.</p>")}`;
    return panel(t.team + EcoI18n.t(" · où passe la valeur ?"), EcoI18n.t(
      "Les parts versées aux entreprises répartissent les recettes : elles ne constituent pas un coût supplémentaire."
      ), svg(EcoI18n.t("Décomposition de la valeur du transport"), body), steps.map(([l,
      v]) => [l, signed(v)]), [EcoI18n.t("Flux"), EcoI18n.t("Crédits")], EcoI18n.t(
      "Le territoire a-t-il créé de la valeur ? Quelles dépenses ont permis le service, et lesquelles sont restées sans recettes ?"
      ), EcoI18n.t(
      "Installation inclut les engagements supplémentaires. Adaptations inclut les investissements collectifs et l’extension. Le substitut est un fournisseur extérieur. Les montants sont des flux de l’année."
      ), equation, EcoI18n.t("Création de valeur · coûts irrécupérables"));
  }

  function actors() {
    const t = team(),
      rows = t.actors,
      [lo, hi] = domain(rows.flatMap(a => [-a.costs, a.revenue + a.outside]));
    const x = v => 135 + (v - lo) / (hi - lo) * 700,
      zero = x(0);
    let body = text(20, 22, EcoI18n.t("Crédits")) + text(975, 22, EcoI18n.t("Résultat net"),
      'text-anchor="end"');
    for (const v of ticks(lo, hi)) {
      body += `<line class="db-grid" x1="${x(v)}" x2="${x(v)}" y1="38" y2="455"/>` + text(x(v),
        485, number(v), 'text-anchor="middle"');
    }
    body += `<line class="db-zero" x1="${zero}" x2="${zero}" y1="38" y2="455"/>`;
    rows.forEach((a, i) => {
      const y = 66 + i * 80;
      body += text(20, y + 22, a.role, `fill="${roleColors[a.role]}" class="db-role"`);
      [
        [-a.costs, 0, "#efcf79", EcoI18n.t("Coûts")],
        [0, a.revenue, "#78e5ee", EcoI18n.t("Recettes de transport")],
        [a.revenue, a.revenue + a.outside, "#85e0b2", EcoI18n.t("Activité extérieure")]
      ].forEach(([from, to, color, label]) => {
        if (from !== to) body +=
          `<rect x="${x(from)}" y="${y}" width="${x(to)-x(from)}" height="32" fill="${color}"><title>${a.role} · ${label} : ${number(to-from)}${EcoI18n.t(" crédits</title></rect>")}`;
      });
      const net = x(a.net);
      body +=
        `<path d="M${net} ${y+8}${EcoI18n.t("l8 8-8 8-8-8Z\" fill=\"#edf5f8\" stroke=\"#07121c\" stroke-width=\"2\"><title>Résultat net ")}${a.role} : ${signed(a.net)}${EcoI18n.t(" crédits</title></path>")}` +
        text(975, y + 23, signed(a.net), 'text-anchor="end" class="db-value"');
    });
    const key = legend([
      [EcoI18n.t("Recettes de transport"), "#78e5ee"],
      [EcoI18n.t("Activité extérieure"), "#85e0b2"],
      [EcoI18n.t("Coûts engagés"), "#efcf79"],
      [EcoI18n.t("Repère blanc : résultat net"), "#edf5f8"]
    ]);
    return panel(t.team + EcoI18n.t(" · qui gagne quoi ?"), EcoI18n.t(
        "Les revenus se lisent à droite de zéro et les coûts à gauche. Le repère blanc représente les revenus moins les coûts."
        ), svg(EcoI18n.t("Revenus, coûts et résultat de chaque entreprise"), body, 520), rows
      .map(a => [a.role, number(a.revenue), number(a.outside), number(a.costs), signed(a
        .project_result), signed(a.net)]), [EcoI18n.t("Entreprise"), "Transport", EcoI18n.t(
        "Extérieur"), EcoI18n.t("Coûts"), EcoI18n.t("Résultat transport"), EcoI18n.t(
        "Résultat total")], EcoI18n.t(
        "Une grande part des recettes suffit-elle à obtenir le meilleur résultat ? Qui gagne grâce au transport, et qui gagne surtout ailleurs ?"
        ), EcoI18n.t(
        "Résultats hors dotation initiale. Les coûts comprennent les frais privés effectivement débités, y compris les hausses reçues. Un binôme représente une seule entreprise."
        ), key, EcoI18n.t("Capture de valeur · options extérieures"));
  }

  function contracts() {
    const t = team(),
      contracts = t.contracts,
      height = Math.max(240, contracts.length * 94 + 100);
    let body = text(20, 25, EcoI18n.t("Accords effectivement signés · parts des recettes"));
    contracts.forEach((c, i) => {
      const y = 55 + i * 94;
      body += text(20, y + 20, "V" + c.revision, 'class="db-value"') + text(20, y + 41,
        dateLabels[c.date] || c.date);
      let x = 200;
      for (const [role, share] of Object.entries(c.allocations)) {
        const width = share * 750 / Math.max(1, Object.values(c.allocations).reduce((a, b) => a + b, 0));
        if (width) {
          body +=
            `<rect x="${x}" y="${y}" width="${width}" height="40" fill="${roleColors[role]}"><title>${role} : ${number(share)} ${EcoI18n.t("crédits")} · V${c.revision}</title></rect>`;
          if (width >= 50) body += text(x + width / 2, y + 25, number(share) + " " + EcoI18n.t("crédits"),
            'text-anchor="middle" class="db-share"');
        }
        x += width;
      }
      body += text(200, y + 65, (actionLabels[c.kind] || c.kind || EcoI18n.t("Accord")) +
        " · interfaces " + (c.architecture === "MODULAR" ? EcoI18n.t("communes") : EcoI18n
          .t("spécifiques")));
    });
    if (!contracts.length) body += text(60, 120, EcoI18n.t(
      "Aucun accord n’a été signé dans ce territoire."));
    const roles = [...new Set(contracts.flatMap(c => Object.keys(c.allocations)))];
    const key = legend(roles.map(r => [r === "ALT" ? EcoI18n.t("Substitut") : r, roleColors[
      r]])) +
      `<p class="db-equation"><b>${t.proposal_count}${EcoI18n.t("</b> proposition(s) publiée(s) · <b>")}${contracts.length}${EcoI18n.t("</b> accord(s) signé(s) · <b>")}${t.refusal_count}${EcoI18n.t("</b> réponse(s) de refus enregistrée(s).</p>")}`;
    const rows = contracts.flatMap(c => Object.entries(c.allocations).map(([role, share]) => [c
      .revision, dateLabels[c.date], actionLabels[c.kind] || c.kind, role, number(share), number(c
        .funding[role] || 0)
    ]));
    return panel(t.team + EcoI18n.t(" · comment l’accord évolue-t-il ?"), EcoI18n.t(
      "Chaque barre représente un accord accepté par tous les partenaires concernés. Les numéros correspondent aux propositions ; une version non signée ne devient pas un contrat."
      ), svg(EcoI18n.t("Évolution du partage des recettes dans les accords signés"), body,
      height), rows, ["Version", EcoI18n.t("Période"), "Objet", EcoI18n.t("Entreprise"),
      EcoI18n.t("Recettes (crédits)"), EcoI18n.t("Contribution collective (crédits)")
    ], EcoI18n.t(
      "Qui obtient une concession après une nouvelle information ? Un partage inchangé signifie-t-il que la situation économique est restée identique ?"
      ), EcoI18n.t(
      "Les montants en crédits sont convenus pour chaque tour ; les incidents peuvent réduire les recettes effectivement versées. Le financement affiché exclut l’installation privée. Les refus comptent les réponses enregistrées, y compris une réponse ensuite révisée."
      ), key, EcoI18n.t("Orchestration · négociation · dépendances"));
  }

  function events() {
    const teams = state.data.teams,
      height = 85 + teams.length * 100;
    let body = "";
    dates.forEach((d, i) => body += text(140 + i * 215, 27, dateLabels[d], 'class="db-role"'));
    teams.forEach((t, row) => {
      const y = 48 + row * 100;
      body += text(18, y + 42, t.team, `fill="${colors[t.team]}" class="db-role"`);
      dates.forEach((d, col) => {
        const entries = t.events.filter(e => e.date === d),
          shocks = entries.filter(e => e.category === "circumstance").length,
          decisions = entries.filter(e => e.category === "decision").length,
          p = t.periods.find(p => p.date === d),
          x = 125 + col * 215,
          selected = t.team === state.team && d === state.date;
        body +=
          `<g class="db-cell" tabindex="0" role="button" aria-label="${t.team}, ${dateLabels[d]}, ${shocks}${EcoI18n.t(" circonstances ou essais, ")}${decisions}${EcoI18n.t(" décisions. Afficher le détail.\" onclick=\"Debrief.inspect('")}${t.team}','${d}')" onkeydown="Debrief.activate(event,'${t.team}','${d}')"><title>${t.team} · ${dateLabels[d]} : ${entries.length}${EcoI18n.t(" faits enregistrés</title><rect x=\"")}${x}" y="${y}" width="200" height="84" fill="${selected?"#173c4a":"#102430"}" stroke="${selected?colors[t.team]:"#31505d"}" stroke-width="${selected?2:1}"/>${text(x+13,y+24,shocks+EcoI18n.t(" circonstance(s) / essai(s)"))}${text(x+13,y+46,decisions+EcoI18n.t(" décision(s)"))}${text(x+13,y+68,p?number(p.revenue)+EcoI18n.t(" cr. de transport"):EcoI18n.t("Comptes non disponibles"),'class="db-subtext"')}</g>`;
      });
    });
    const t = team(),
      entries = t.events.filter(e => e.date === state.date),
      rows = teams.flatMap(t => t.events.map(e => [t.team, dateLabels[e.date] || e.date,
        categories[e.category]?.[0] || e.category, title(e), e.detail, e.sequence
      ]));
    const key = legend(Object.values(categories));
    const details =
      `<section class="db-events" id="dbEventsDetails" tabindex="-1"><h3>${safe(t.team)} · ${dateLabels[state.date]}${EcoI18n.t("</h3><p class=\"small muted\">Ordre exact du journal. Les numéros indiquent la séquence d’enregistrement ; plusieurs faits peuvent survenir au cours d’un même trimestre.</p><ol>")}${entries.map(e=>`<li style="--event-color:${categories[e.category]?.[1]}"><span class="edition">${safe(categories[e.category]?.[0])} · #${e.sequence}</span><h4>${safe(title(e))}</h4><p>${safe(e.detail)}</p></li>`).join("")||EcoI18n.t('<li><p>Aucun fait de ces catégories n’a été enregistré pour cette période. Cela ne signifie pas qu’un nouveau tirage a eu lieu.</p></li>')}</ol></section>`;
    return panel(EcoI18n.t("Circonstances reçues, décisions prises"), EcoI18n.t(
      "Sélectionnez une case pour reconstruire le déroulement d’un territoire, sans confondre le choc, la réponse choisie et son résultat."
      ), svg(EcoI18n.t("Chronologie comparée des territoires"), body, height), rows, [EcoI18n
      .t("Territoire"), EcoI18n.t("Période"), "Nature", "Fait", EcoI18n.t("Détail"), EcoI18n
      .t("Séquence")
    ], EcoI18n.t(
      "Face à quelle information les partenaires ont-ils agi ? Les différences de résultat viennent-elles des mêmes circonstances et des mêmes possibilités ?"
      ), EcoI18n.t(
      "Les circonstances incluent les résultats aléatoires des essais. Une période calme ou une situation déjà bloquée est classée comme contexte. L’ordre temporel permet de discuter une explication ; il ne démontre pas, à lui seul, un effet causal."
      ), key, EcoI18n.t("Aléas · adaptation · résilience")) + details;
  }

  function render(data) {
    state.data = data;
    if (!data?.teams?.length) return EcoI18n.t(
      '<section class="campaign-actions"><p>Les données de visualisation seront disponibles après redémarrage du serveur. Le ZIP et l’historique de la séance restent conservés.</p></section>'
      );
    if (!data.teams.some(t => t.team === state.team)) state.team = data.teams[0].team;
    const t = team(),
      f = t.finances,
      view = ({
        trajectory,
        value,
        actors,
        contracts,
        events
      })[state.view] || trajectory;
    return `${EcoI18n.t("<section class=\"debrief\"><header class=\"db-header\"><div><span class=\"edition\">Observatoire de la séance · décembre 2032</span><h1>Lire les trajectoires.</h1><p>Comparer ce qui a été créé, partagé et engagé. Revenir aux circonstances et aux choix avant d’expliquer les résultats.</p></div><div class=\"db-header-controls\"><label for=\"debriefTeam\">Territoire étudié<select id=\"debriefTeam\" onchange=\"Debrief.setTeam(this.value)\">")}${data.teams.map(t=>`<option ${t.team===state.team?"selected":""}>${t.team}</option>`).join("")}</select></label><button class="small ghost" id="debriefProjection" aria-pressed="${state.projection}" onclick="Debrief.toggleProjection()">${state.projection?EcoI18n.t("Quitter la projection"):EcoI18n.t("Mode projection")}${EcoI18n.t("</button></div></header><div class=\"db-kpis\"><div><span>Valeur collective du transport</span><strong>")}${signed(f.created)}${EcoI18n.t(" <small>cr.</small></strong></div><div><span>Résultats des cinq entreprises</span><strong>")}${signed(f.company_result)}${EcoI18n.t(" <small>cr.</small></strong></div><div><span>Trimestres avec recettes de transport</span><strong>")}${t.periods.filter(p=>p.revenue>0).length} <small>/ ${t.periods.length}</small></strong></div></div>${f.accounting_gap||f.distribution_gap?EcoI18n.t('<p class="db-accounting-alert">Les comptes de ce territoire présentent un écart de rapprochement. Consultez les transactions avant d’interpréter les totaux.</p>'):""}${EcoI18n.t("<nav class=\"db-views\" aria-label=\"Visualisations du débrief\">")}${Object.entries(views).map(([k,label],i)=>`<button id="db-view-${k}" aria-pressed="${k===state.view}" onclick="Debrief.setView('${k}')"><span>0${i+1}</span>${label}</button>`).join("")}</nav>${view()}${EcoI18n.t("<footer class=\"db-source\"><b>Source : la séance jouée.</b> Les montants des graphiques et du CSV sont en crédits. Le ZIP complet utilise les centièmes de crédit. Les chiffres privés sont révélés au bilan ; aucun événement ni choix manquant n’est inventé.</footer></section>")}`;
  }

  function refresh(focus) {
    const id = focus || document.activeElement?.id;
    window.render();
    if (id) document.getElementById(id)?.focus({
      preventScroll: true
    });
  }

  function inspect(t, d) {
    state.team = t;
    state.date = d;
    state.view = "events";
    refresh("dbEventsDetails");
    document.getElementById("dbEventsDetails")?.scrollIntoView({
      block: "nearest"
    });
  }

  function download(data, type, extension) {
    const blob = new Blob([data], {
        type
      }),
      url = URL.createObjectURL(blob),
      a = document.createElement("a");
    a.href = url;
    a.download = `ecosystem-${state.team}-${state.view}.${extension}`;
    a.click();
    setTimeout(() => URL.revokeObjectURL(url), 1000);
  }
  window.Debrief = {
    render,
    inspect,
    isProjecting() {
      return state.projection;
    },
    toggleProjection() {
      state.projection = !state.projection;
      document.body.classList.toggle("debrief-projecting", state.projection);
      refresh("debriefProjection");
    },
    activate(e, t, d) {
      if (e.key === "Enter" || e.key === " ") {
        e.preventDefault();
        inspect(t, d);
      }
    },
    setTeam(t) {
      if (state.data.teams.some(x => x.team === t)) {
        state.team = t;
        refresh();
      }
    },
    setView(v) {
      if (views[v]) {
        state.view = v;
        refresh("db-view-" + v);
      }
    },
    setMetric(v) {
      if (metrics[v]) {
        state.metric = v;
        refresh();
      }
    },
    downloadSVG() {
      const node = document.querySelector("#debriefChart svg");
      if (!node) return;
      const clone = node.cloneNode(true);
      clone.querySelectorAll("[onclick],[onkeydown]").forEach(n => {
        n.removeAttribute("onclick");
        n.removeAttribute("onkeydown");
        n.removeAttribute("tabindex");
        n.removeAttribute("role");
      });
      clone.insertAdjacentHTML("afterbegin",
        '<rect width="100%" height="100%" fill="#07121c"/><style>svg{background:#07121c;color:#edf5f8}text{fill:#b6cbd5;font:14px Arial,sans-serif}.db-value,.db-role{fill:#edf5f8;font-weight:bold}.db-share{fill:#07121c;font-weight:bold}.db-subtext{fill:#8fa7b5;font-size:12px}.db-grid{stroke:#28434f;stroke-width:1}.db-zero{stroke:#86a8b6;stroke-width:1.5}.db-connector{stroke:#86a8b6;stroke-dasharray:4 4}</style>'
        );
      download(new XMLSerializer().serializeToString(clone), "image/svg+xml;charset=utf-8",
        "svg");
    },
    downloadCSV() {
      const rows = state.exportRows || [];
      download("\ufeff" + rows.map(r => r.map(v => '"' + String(v ?? "").replace(
          /[\u00a0\u202f]/g, " ").replace(/"/g, '""') + '"').join(";")).join("\r\n"),
        "text/csv;charset=utf-8", "csv");
    }
  };
})();
