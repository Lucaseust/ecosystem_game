/* Briefing local : règles communes, sans annoncer les événements futurs. */
"use strict";
(() => {
  const dialog = document.getElementById("intro");
  const stage = document.getElementById("introStage");
  const next = document.getElementById("introNext");
  const back = document.getElementById("introBack");
  const pause = document.getElementById("introPause");
  const reduced = matchMedia("(prefers-reduced-motion: reduce)");
  const storageKey = "eco_briefing_seen_v3";
  const durations = [11000, 12000, 15000, 18000, 17000, 16000];
  const chapters = ["Mission", EcoI18n.t("Partenaires"), EcoI18n.t("Votre entreprise"), EcoI18n.t("Les accords"), EcoI18n.t("Le calendrier"), EcoI18n.t("Les conséquences")];
  document.querySelector(".intro-progress").innerHTML = chapters.map(title => `<span title="${title}"><i></i></span>`).join("");
  const partners = [
    ["MOBI", EcoI18n.t("L’application et les clients"), EcoI18n.t("Assemble le service et publie les contrats.")],
    ["AUTO", EcoI18n.t("Les véhicules"), EcoI18n.t("Fabrique et adapte les navettes.")],
    ["BRAIN", EcoI18n.t("La conduite autonome"), EcoI18n.t("Fournit l’IA qui pilote les navettes.")],
    ["GRID", EcoI18n.t("L’énergie et les dépôts"), EcoI18n.t("Assure la recharge et l’infrastructure.")],
    ["FLEET", EcoI18n.t("Les opérations sur le terrain"), EcoI18n.t("Exploite les navettes au quotidien.")]
  ];
  let me = null, token = null, seen = null, step = 0, elapsed = 0;
  let paused = false, timer = null, last = 0, returnFocus = null;
  try { seen = localStorage.getItem(storageKey); } catch (_) {}

  const city = `<svg class="intro-city" viewBox="0 0 360 190" aria-hidden="true" fill="none">
    <g class="city-buildings" stroke="currentColor" stroke-width="1"><path d="M8 145V85H34V145M42 145V48H68V145M47 48V34H63V48M80 145V70H114V145M125 145V18H157V145M132 18V6M166 145V56H192V145M205 145V88H238V145M250 145V36H282V145M294 145V65H326V145M335 145V100H352V145"/>
    <path d="M49 63H61M49 77H61M49 91H61M132 38H150M132 52H150M132 66H150M132 80H150M258 51H274M258 65H274M258 79H274M302 79H318M302 93H318"/></g>
    <path class="city-route" d="M0 160H360" stroke="currentColor" stroke-width="2" stroke-dasharray="6 6"/>
    <path d="M32 170V178H328V170" stroke="currentColor" opacity=".35"/>
    <g class="city-shuttle"><path d="M0 151V131L5 123H44L52 134V151Z" fill="var(--bg)" stroke="currentColor" stroke-width="2"/><path d="M8 128H24V139H8ZM29 128H40L46 139H29Z" stroke="currentColor"/><path d="M8 151V155H15V151M36 151V155H43V151" stroke="currentColor" stroke-width="3"/></g>
    <path class="city-stop" d="M38 151V112H54M306 151V112H322" stroke="currentColor" stroke-width="2"/>
  </svg>`;
  const capital = `${EcoI18n.t("<div class=\"intro-capital\" aria-label=\"20 crédits par entreprise, une seule fois\"><div class=\"capital-units\" aria-hidden=\"true\">")}${Array.from({length:20},(_,i)=>`<i style="--order:${i}"></i>`).join("")}${EcoI18n.t("</div><strong>20 <small>crédits</small></strong><span>par entreprise · une seule dotation</span></div>")}`;
  const consent = `${EcoI18n.t("<figure class=\"intro-agreement\"><figcaption>Un contrat, des engagements réels</figcaption><ol><li><b>Discuter</b><span>Activités, dépenses, recettes</span></li><li><b>MOBI publie</b><span>Une version du contrat</span></li><li><b>Tous acceptent</b><span>Les partenaires concernés s’engagent</span></li></ol><div class=\"intro-signals\" aria-hidden=\"true\">")}${partners.map(([r],i)=>`<span style="--order:${i}">${r}<i></i></span>`).join("")}${EcoI18n.t("</div><p>Schéma de signature · vos réponses restent libres.</p></figure>")}`;
  const calendar = `${EcoI18n.t("<figure class=\"intro-calendar\"><figcaption>Une année économique commune</figcaption><ol>")}${[EcoI18n.t("Jan–mars"),EcoI18n.t("Avr–juin"),EcoI18n.t("Juil–sept"),EcoI18n.t("Oct–déc")].map((s,i)=>`<li style="--order:${i}"><b>0${i+1}</b>${s}</li>`).join("")}</ol><div class="intro-territories" aria-hidden="true">${["#7abfff","#85e0b2","#ff9c92"].map((c,i)=>`<div style="--lane:${c};--order:${i}${EcoI18n.t("\"><span>Territoire ")}${String.fromCharCode(65+i)}</span><i></i><i></i><i></i></div>`).join("")}${EcoI18n.t("</div><p>Des trajectoires différentes, sans attendre les accords des autres groupes.</p></figure>")}`;
  const accounts = `${EcoI18n.t("<div class=\"intro-accounts\"><span>Trajets réellement facturés</span><i aria-hidden=\"true\">↓</i><span>Recettes partagées selon le contrat</span><i aria-hidden=\"true\">↓</i><span>Chaque entreprise paie ses propres frais</span></div>")}`;

  function syncRole() {
    if (!me) return;
    stage.querySelectorAll("[data-role]").forEach((node) => {
      const mine = node.dataset.role === me.role;
      node.classList.toggle("is-you", mine);
      node.querySelector(".intro-you").hidden = !mine;
    });
    stage.querySelectorAll("[data-my-role]").forEach((node) => { if (node.textContent !== me.role) node.textContent = me.role; });
  }

  let sceneDuration = durations[0];

  function updateReadHint() {
    document.getElementById("introReadHint").hidden = !dialog.open || stage.scrollTop + stage.clientHeight + 12 >= stage.scrollHeight;
  }

  function paint() {
    if (step === 0) stage.innerHTML = `${EcoI18n.t("<section class=\"intro-scene\"><span class=\"edition\">Transmission 01 · Métropole, janvier 2032</span>")}${city}${EcoI18n.t("<h1 id=\"introTitle\">Votre mission : créer<br>une flotte autonome.</h1><p id=\"introText\">Sur un territoire pilote confié par la ville, construisez et exploitez des navettes sans chauffeur, réservables à la demande.</p><p>Réunissez véhicules, IA de conduite, recharge, exploitation quotidienne et application voyageurs.</p><p class=\"intro-emphasis\">Vous avez jusqu’en décembre pour faire vivre ce service.</p></section>")}`;
    else if (step === 1) stage.innerHTML = `${EcoI18n.t("<section class=\"intro-scene\"><span class=\"edition\">Transmission 02 · Les partenaires</span><h1 id=\"introTitle\">Cinq entreprises.<br>Un même projet.</h1><p id=\"introText\">Vous dirigez l’une de ces entreprises complémentaires.</p><ol class=\"intro-partners\">")}${partners.map(([role, asset, text], i) => `<li data-role="${role}" style="--order:${i}"><div><strong>${role}${EcoI18n.t("</strong><span class=\"intro-you\" hidden>VOUS</span></div><div><b>")}${asset}</b><p>${text}</p></div></li>`).join("")}</ol></section>`;
    else if (step === 2) stage.innerHTML = `${EcoI18n.t("<section class=\"intro-scene\"><span class=\"edition\">Transmission 03 · Votre entreprise</span><h1 id=\"introTitle\">Un projet commun.<br>Vos propres intérêts.</h1><p id=\"introText\">Vous dirigez <b data-my-role></b>. Votre but : maximiser le résultat financier annuel de votre entreprise, mesuré par l’évolution de sa trésorerie.</p>")}${capital}${EcoI18n.t("<p>Votre dossier privé détaille installation, frais d’exploitation et activité extérieure. Vous décidez quelles informations partager.</p><p class=\"intro-emphasis\">En binôme, vous dirigez une seule entreprise : même budget, mêmes décisions.</p></section>")}`;
    else if (step === 3) stage.innerHTML = `${EcoI18n.t("<section class=\"intro-scene\"><span class=\"edition\">Transmission 04 · Les accords</span><h1 id=\"introTitle\">Négociez.<br>Puis engagez-vous.</h1><p id=\"introText\">Chacun choisit son engagement. Négociez dépenses, financement et recettes en crédits à répartir intégralement à chaque tour.</p>")}${consent}${EcoI18n.t("<p>L’accord prend effet quand <b>toutes les entreprises concernées acceptent</b> ; les dépenses sont alors débitées. Vous pouvez refuser ou demander une autre proposition.</p><p class=\"intro-emphasis\">Une nouvelle version annule les réponses précédentes. Sans accord à la clôture, la proposition expire ; le gain est nul pour tous, sans frais d’exploitation ni revenu extérieur. Un accord précédent ne rapporte rien pour ce tour.</p></section>")}`;
    else if (step === 4) stage.innerHTML = `${EcoI18n.t("<section class=\"intro-scene\"><span class=\"edition\">Transmission 05 · Le calendrier</span><h1 id=\"introTitle\">Le temps passe.<br>Les choix restent.</h1><p id=\"introText\">L’enseignant clôt le trimestre : les comptes sont réglés, puis tous passent à la date suivante. Le chronomètre ne fait pas avancer le jeu.</p>")}${calendar}${EcoI18n.t("<p><b>Un groupe sans accord ne bloque pas les autres.</b> Sa flotte ne rapporte rien ; il peut négocier à la date suivante, avec moins de temps d’exploitation.</p><p class=\"intro-emphasis\">Argent, investissements et contrats sont conservés entre les trimestres.</p></section>")}`;
    else stage.innerHTML = `${EcoI18n.t("<section class=\"intro-scene\"><span class=\"edition\">Transmission 06 · Les conséquences</span><h1 id=\"introTitle\">Créer de la valeur.<br>En obtenir une part.</h1><p id=\"introText\">Une signature ne garantit aucun bénéfice. Les recettes dépendent des trajets assurés et des capacités réunies.</p>")}${accounts}${EcoI18n.t("<p>Essais ou délais peuvent réduire les recettes ; les frais d’exploitation engagée restent dus. Une capacité disponible hors du service peut rapporter un revenu extérieur, sans double rémunération.</p><p>Les circonstances varient selon les groupes ; vos choix passés déterminent vos réactions possibles.</p><p class=\"intro-emphasis\">Consultez votre dossier et négociez. Vous pouvez demander une renégociation. Retirer une activité, si vos droits le permettent, interrompt la flotte. Au bilan, comparez résultats des entreprises et valeur collective du transport.</p></section>")}`;
    syncRole();
    sceneDuration = Math.max(durations[step], stage.textContent.trim().split(/\s+/).length * 280);
    stage.scrollTop = 0;
    back.disabled = step === 0;
    next.textContent = step === durations.length - 1 ? EcoI18n.t("Entrer dans la partie →") : EcoI18n.t("Suivant →");
    document.getElementById("introCount").textContent = `0${step + 1} / 0${durations.length} · ${chapters[step]}`;
    dialog.dataset.step = String(step);
    updateProgress();
    updateReadHint();
  }

  function updateProgress() {
    dialog.querySelectorAll(".intro-progress > span").forEach((node, index) => {
      const fraction = index < step ? 1 : index > step ? 0 : elapsed / sceneDuration;
      node.firstElementChild.style.transform = `scaleX(${Math.min(1, fraction)})`;
      if (index === step) node.setAttribute("aria-current", "step");
      else node.removeAttribute("aria-current");
    });
  }

  function setPaused(value) {
    paused = value;
    last = performance.now();
    dialog.classList.toggle("intro-paused", paused);
    pause.textContent = paused ? EcoI18n.t("Lire ▷") : "Pause Ⅱ";
    pause.setAttribute("aria-pressed", String(paused));
    pause.setAttribute("aria-label", paused ? EcoI18n.t("Lire le briefing automatiquement") : EcoI18n.t("Mettre le briefing en pause"));
  }

  function finish(remember = true) {
    clearInterval(timer);
    timer = null;
    if (remember && token) {
      seen = token;
      try { localStorage.setItem(storageKey, token); } catch (_) {}
    }
    dialog.close();
    document.body.classList.remove("intro-open");
    const target = returnFocus?.isConnected && returnFocus.getClientRects().length ? returnFocus : document.getElementById("replayIntro");
    if (target?.getClientRects().length) target.focus({ preventScroll: true });
  }

  function move(direction) {
    if (step + direction >= durations.length) return finish();
    step = Math.max(0, step + direction);
    elapsed = 0;
    last = performance.now();
    paint();
  }

  function open() {
    if (!me || me.identity_required || dialog.open) return;
    returnFocus = document.activeElement;
    step = 0;
    elapsed = 0;
    paint();
    setPaused(reduced.matches);
    document.body.classList.add("intro-open");
    dialog.showModal();
    updateReadHint();
    timer = setInterval(() => {
      const now = performance.now();
      const delta = now - last;
      last = now;
      if (paused || document.hidden) return;
      elapsed += delta;
      if (elapsed >= sceneDuration) {
        // Ne pas quitter un écran dont la partie basse n'a pas encore été lue.
        if (stage.scrollTop + stage.clientHeight + 12 < stage.scrollHeight) setPaused(true);
        else move(1);
      }
      else updateProgress();
    }, 100);
  }

  next.addEventListener("click", () => move(1));
  stage.addEventListener("scroll", updateReadHint, {passive:true});
  new ResizeObserver(updateReadHint).observe(stage);
  back.addEventListener("click", () => move(-1));
  pause.addEventListener("click", () => setPaused(!paused));
  document.getElementById("introSkip").addEventListener("click", () => finish());
  dialog.addEventListener("cancel", (event) => { event.preventDefault(); finish(); });
  document.addEventListener("visibilitychange", () => { last = performance.now(); });
  reduced.addEventListener("change", () => { if (dialog.open && reduced.matches) setPaused(true); });
  window.EcoIntro = {
    open,
    sync(player, sessionToken) {
      me = { role: player.role, identity_required: player.identity_required };
      token = sessionToken;
      if (me.identity_required && dialog.open) finish(false);
      if (dialog.open) syncRole();
      else if (token && seen !== token && !me.identity_required) open();
    },
    reset() { if (dialog.open) finish(false); me = null; token = null; }
  };
})();
