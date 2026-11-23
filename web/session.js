/* Repères de séance communs. Aucun appel réseau, aucune dépendance. */
"use strict";
const SESSION_STAGES = [
  ["LOBBY", "Accueil"], ["R1", "Dépendances"], ["R2", "Négociation"],
  ["MARKET", "Marché"], ["R3", "Résilience"], ["FINAL", "Bilan"]
];
function replacePanel(container, html) {
  const disclosures = new Map(Array.from(container.querySelectorAll("details"), (d) =>
    [d.querySelector("summary")?.textContent.trim(), d.open]));
  container.innerHTML = html;
  container.querySelectorAll("details").forEach((d) => {
    const key = d.querySelector("summary")?.textContent.trim();
    if (disclosures.has(key)) d.open = disclosures.get(key);
  });
}

function votingRoles(team, n, shock) {
  if (!n) return [];
  const rd = team.rounds[String(n)];
  if (n === 3 && rd.resolution === "ABANDON") return [];
  const excluded = n === 3 && rd.resolution === "REPLACE"
    ? ({ AI_FAILURE: "BRAIN", INFRA_FAILURE: "GRID" }[shock] || "BRAIN") : null;
  return ["MOBI", "AUTO", "BRAIN", "GRID", "FLEET"].filter((r) =>
    r !== excluded && !team.seats[r].bot);
}
function sessionRail(phase) {
  const key = phase === "DEBRIEF" ? "FINAL" : phase.startsWith("R") ? phase.slice(0, 2) : phase;
  const current = SESSION_STAGES.findIndex(([k]) => k === key);
  return `<nav class="session-rail" aria-label="Déroulé de la séance">${SESSION_STAGES.map(([k, label], i) =>
    `<span class="${i === current ? "current" : i < current ? "complete" : ""}" ${i === current ? 'aria-current="step"' : ""}>
      <b>${String(i + 1).padStart(2, "0")}</b>${label}</span>`).join("")}</nav>`;
}
function phaseMission(phase, role) {
  const missions = {
    LOBBY: ["Votre mission", "Lisez votre fiche privée. Retrouvez vos partenaires. Votre entreprise veut gagner, mais elle ne peut pas lancer le service seule."],
    R1_NEGO: ["Discuter de l’offre imposée", "Les parts sont fixes. Laissez les entreprises réagir à la proposition avant leur décision individuelle de participer ou de se retirer."],
    R2_NEGO: ["Construire un accord", role === "MOBI" ? "Recueillez les demandes, publiez une proposition, puis révisez-la en fonction des intentions de vos partenaires." : "Publiez votre demande. À chaque contrat, signalez « Prêt à signer » ou « À renégocier ». Votre vote final restera secret."],
    MARKET: ["Tester les dépendances", role === "MOBI" ? "Faites une offre à un BRAIN concurrent. Le transfert doit libérer un siège et sera réglé à la clôture." : role === "BRAIN" ? "Comparez les offres reçues au coût de départ. Rester est aussi une décision." : "Discutez de la fidélité de vos partenaires et préparez votre position sur l’architecture."],
    R3_ARCH: ["Choisir avant de savoir", "Comparez revenu immédiat et flexibilité. MOBI publie l’architecture ; FLEET peut exercer son veto avant cette publication."],
    R3_SHOCK: ["L’environnement a changé", "Lisez le choc. Identifiez le partenaire touché et les nouvelles contraintes avant de renégocier."],
    R3_NEGO: ["Sauver le service", role === "MOBI" ? "Choisissez une réponse au choc, répartissez les coûts et publiez le contrat de sauvetage." : "Recalculez votre position après le choc. Négociez le partage des coûts, puis indiquez votre intention."],
    FINAL: ["Deux victoires possibles", "Comparez la performance de votre entreprise et celle de votre écosystème. Qui a créé la valeur ? Qui l’a captée ?"],
    DEBRIEF: ["Relier l’expérience au cours", "Appuyez votre analyse sur un contrat, une décision et une conséquence observés pendant la partie."]
  };
  if (phase.endsWith("_DECIDE")) return ["Le moment de s’engager", "Relisez l’accord publié. JOIN engage vos ressources ; OUT active votre option extérieure. Les intentions précédentes ne remplacent pas ce vote secret."];
  if (phase.endsWith("_RESULTS")) return ["Lire les conséquences", "Regardez qui a participé, si le service a été lancé et la différence entre score individuel et valeur collective."];
  return missions[phase] || ["La séance continue", "Suivez les indications de l’enseignant."];
}
