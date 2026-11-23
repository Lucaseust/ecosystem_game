/* Briefing local : aucun chiffre prive, aucune annonce des manches a venir. */
"use strict";
(() => {
  const dialog = document.getElementById("intro");
  const stage = document.getElementById("introStage");
  const next = document.getElementById("introNext");
  const back = document.getElementById("introBack");
  const pause = document.getElementById("introPause");
  const reduced = matchMedia("(prefers-reduced-motion: reduce)");
  const storageKey = "eco_briefing_seen_v1";
  const durations = [6500, 12000, 8500];
  const partners = [
    ["MOBI", "L’application et les clients", "Assemble le service et publie les contrats."],
    ["AUTO", "Les véhicules", "Fabrique et adapte les navettes."],
    ["BRAIN", "La conduite autonome", "Fournit l’IA qui pilote les navettes."],
    ["GRID", "L’énergie et les dépôts", "Assure la recharge et l’infrastructure."],
    ["FLEET", "Les opérations sur le terrain", "Exploite les navettes au quotidien."]
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
  const network = `<svg class="intro-network" viewBox="0 0 360 150" fill="none" aria-hidden="true"><path class="network-link" pathLength="1" d="M35 35L180 115L325 35M105 35L180 115L255 35M180 35V115" stroke="currentColor" stroke-width="1.5"/><g stroke="currentColor" fill="var(--bg)"><path d="M27 27H43V43H27ZM97 27H113V43H97ZM172 27H188V43H172ZM247 27H263V43H247ZM317 27H333V43H317Z"/><path d="M164 99H196V131H164Z" stroke-width="2"/></g><path d="M176 109L185 115L176 121Z" fill="currentColor"/></svg>`;

  function syncRole() {
    if (!me) return;
    stage.querySelectorAll("[data-role]").forEach((node) => {
      const mine = node.dataset.role === me.role;
      node.classList.toggle("is-you", mine);
      node.querySelector(".intro-you").hidden = !mine;
    });
    stage.querySelectorAll("[data-my-role]").forEach((node) => { if (node.textContent !== me.role) node.textContent = me.role; });
  }

  function paint() {
    if (step === 0) stage.innerHTML = `<section class="intro-scene"><span class="edition">Transmission 01 · Métropole, 2032</span>${city}<h1 id="introTitle">La ville attend<br>sa première navette.</h1><p id="introText">Un trajet fiable. Moins de dix minutes d’attente. Un prix inférieur à celui d’un taxi.</p><p class="intro-emphasis">La technologie existe. Le service reste à construire.</p></section>`;
    else if (step === 1) stage.innerHTML = `<section class="intro-scene"><span class="edition">Transmission 02 · Les partenaires</span><h1 id="introTitle">Cinq entreprises.<br>Un même projet.</h1><p id="introText">Chacune apporte une pièce indispensable. Vous dirigez l’une d’elles.</p><ol class="intro-partners">${partners.map(([role, asset, text], i) => `<li data-role="${role}" style="--order:${i}"><div><strong>${role}</strong><span class="intro-you" hidden>VOUS</span></div><div><b>${asset}</b><p>${text}</p></div></li>`).join("")}</ol></section>`;
    else stage.innerHTML = `<section class="intro-scene"><span class="edition">Transmission 03 · Votre objectif</span>${network}<h1 id="introTitle">Un projet commun.<br>Vos propres intérêts.</h1><p id="introText">Vous dirigez <b data-my-role></b>. Votre but : obtenir le plus de points pour votre entreprise.</p><p>Le revenu du service n’existe que si tous les partenaires nécessaires participent. Chacun reste libre de s’engager ou de poursuivre son activité hors du projet.</p><p class="intro-emphasis">Vos chiffres sont privés. Vos décisions vous appartiennent.</p></section>`;
    syncRole();
    stage.scrollTop = 0;
    back.disabled = step === 0;
    next.textContent = step === 2 ? "Entrer dans la partie →" : "Suivant →";
    document.getElementById("introCount").textContent = `0${step + 1} / 03`;
    dialog.dataset.step = String(step);
    updateProgress();
  }

  function updateProgress() {
    dialog.querySelectorAll(".intro-progress > span").forEach((node, index) => {
      const fraction = index < step ? 1 : index > step ? 0 : elapsed / durations[step];
      node.firstElementChild.style.transform = `scaleX(${Math.min(1, fraction)})`;
      if (index === step) node.setAttribute("aria-current", "step");
      else node.removeAttribute("aria-current");
    });
  }

  function setPaused(value) {
    paused = value;
    last = performance.now();
    dialog.classList.toggle("intro-paused", paused);
    pause.textContent = paused ? "Lire ▷" : "Pause Ⅱ";
    pause.setAttribute("aria-pressed", String(paused));
    pause.setAttribute("aria-label", paused ? "Lire le briefing automatiquement" : "Mettre le briefing en pause");
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
    if (step + direction > 2) return finish();
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
    timer = setInterval(() => {
      const now = performance.now();
      const delta = now - last;
      last = now;
      if (paused || document.hidden) return;
      elapsed += delta;
      if (elapsed >= durations[step]) move(1);
      else updateProgress();
    }, 100);
  }

  next.addEventListener("click", () => move(1));
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
