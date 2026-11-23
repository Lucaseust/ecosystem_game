# Revue des informations fournies aux participants

Revue appliquée au parcours de campagne courant. Le téléphone charge `campagne-joueur.js` ; l'ancien script à manches n'est servi que dans le mode historique explicitement sélectionné.

## Critère de présence

Une information est affichée si elle explique le mandat, une activité, un engagement, une contrainte présente, un mouvement réel de trésorerie ou une décision actuellement possible. Les détails secondaires se déplient ou restent dans le dossier privé.

| Information | Destinataire et moment | Utilité et contrôle |
| --- | --- | --- |
| Créer une flotte de transport autonome | Accueil et premier écran du briefing | Explique le projet physique : navettes sans chauffeur, territoire pilote, trajets réservables. |
| Les cinq activités | Briefing et table | Rend explicite la complémentarité entre application, véhicules, IA, recharge et exploitation. |
| Une année jusqu'en décembre | Briefing puis calendrier courant | Donne un horizon économique pour apprécier les investissements sans annoncer les événements. |
| Objectif individuel et dépendances collectives | Briefing et dossier | Donne le but sans recommander un partage ou un vote. |
| Dotation unique de 20 crédits et règles de résultat | Briefing commun ; montants propres dans le dossier privé | Explique le budget et le but. Aucun seuil calculé ni comparaison automatique du meilleur choix. |
| Signature, révisions, refus et expiration | Briefing animé et proposition courante | Distingue discussion et engagement ; tous les acteurs requis doivent accepter, les dépenses ne sont débitées qu’à la signature. |
| Calendrier commun, groupes indépendants | Briefing, repère de trimestre, règles repliables et tableau enseignant | Seul l’enseignant clôt la date. Un groupe sans accord ne bloque pas les autres ; sa négociation peut continuer, sans rattraper les trimestres écoulés. |
| Compte rendu du trimestre précédent | Relevé repliable dans La situation et à la clôture de décembre ; tableau enseignant | Le téléphone affiche la variation de trésorerie de l’entreprise en crédits, puis ses recettes de transport, son activité extérieure et ses dépenses. Les montants proviennent de ses mouvements réellement enregistrés, avec les arrondis et le contrat du trimestre clôturé. Le message collectif explique les recettes du territoire ou le non-lancement, sans dévoiler les comptes privés des partenaires. |
| Recettes, frais engagés et capacité extérieure | Dernier écran du briefing ; chiffres propres dans le dossier | Une part ne garantit pas un bénéfice ; la même capacité n’est pas rémunérée simultanément en exploitation et en activité extérieure. |
| Deux engagements propres au rôle | Avant le premier accord | Chaque option précise sa mise en situation, le payeur du supplément, le bénéficiaire de l'effet et ses conditions. Le supplément est distingué de l'installation de base et des revenus collectifs partagés. Aucun choix humain n'est précoché. |
| Engagement déjà choisi | Récapitulatif repliable ; dossier privé | Évite de répéter le formulaire devant une proposition en attente. Peut être révisé avant installation, avec invalidation de l'ancienne proposition. |
| Proposition publiée | Entreprises de la table | Permet de vérifier les parts, les recettes à pleine capacité, le financement, les interfaces, le lancement et le délai connus. Le montant collectif est nécessaire pour apprécier un pourcentage ; aucun gain individuel optimal n'est calculé. |
| Dépense personnelle à la signature | Entreprise concernée | Comprend installation, engagement supplémentaire et contribution collective lorsqu'ils sont dus. |
| Consentement | Acteurs requis de la proposition actuelle | « J'accepte » engage réellement ; la règle d'entrée en vigueur est annoncée. La version est contrôlée par le serveur. |
| Réponses en cours | Seulement la réponse propre et le nombre de réponses | Les réponses des partenaires restent privées ; l'API enseignant n'expose pas leurs votes ouverts. |
| Accord déjà signé | Table concernée | Reste distinct d'une proposition non acceptée ; continue à s'appliquer tant qu'il reste valable. |
| Incident, demande locale ou baisse de contribution publique | Territoire concerné, après tirage | Donne le fait présent, pas les événements des autres territoires ni les probabilités futures. |
| Intervention possible | Situation actuelle | Le coût, les conditions et la perte éventuelle de recettes sont annoncés avant signature, sans solution optimale recommandée. |
| Hausse de frais privée | Rôle AUTO, GRID ou FLEET touché, après tirage | Affiche le passage de ses frais de base aux frais courants, la durée et le droit de suspension disponible. Aucun montant privé ni seuil optimal n’est transmis aux autres entreprises ou au tableau projeté. |
| Demande de renégociation | Publiée volontairement par un partenaire | Signale qui souhaite rouvrir la discussion sans en révéler automatiquement le motif. L’ancien contrat reste distinct de l’avenant à négocier. |
| Offre extérieure à BRAIN | Montant et droits visibles de BRAIN seul | Offre et exclusivité sont cohérentes avec les choix antérieurs. Les autres voient l'existence de la situation, pas le montant privé. |
| Partenaire écarté | Entreprise et table concernées | Aucun vote ni prélèvement imposé à l'acteur exclu ; son parcours explique activité extérieure et proposition de retour. |
| Histoire et mouvements de trésorerie | Histoire publique du territoire ; mouvements privés de l'entreprise | Permet de comprendre les conséquences des choix déjà faits. Aucun arbre futur dans le téléphone. |
| Résultats cumulés | Clôture de décembre | Sépare variation de trésorerie, activité extérieure et valeur collective du transport. |

## Contradictions supprimées

- Pas de manche à répartition imposée, d'échec programmé ou de nouvelle dotation après un résultat.
- Pas de pouvoir annonçant une phase future, de frise des chocs à venir ou de liste des familles d'événements avant leur tirage.
- Pas de demande « à renégocier » sans variable négociable : les réponses portent sur un véritable contrat.
- Pas de seuil privé automatiquement calculé, de proposition équitable préremplie ni de comparateur JOIN/OUT.
- Pas d'ancienne alerte disant que la flotte est arrêtée une fois l'intervention acceptée. L'annonce reste dans l'histoire, le présent est mis à jour.
- Pas d'annonce de « flotte qui poursuit ses trajets » dans un territoire qui n'a pas encore constitué son premier accord.
- Pas de frais d'exploitation présentés comme effacés si les essais interrompent les recettes ; pas d'activité extérieure rémunérée en même temps que la même capacité engagée.
- Pas de réparation gratuite obtenue en suspendant puis reprenant, ni de reprise implicite en changeant seulement les interfaces.
- Pas de badge récompensant une réponse théorique attendue et modifiant les résultats.

## Contrôles réalisés

La révision éditoriale du 15 novembre 2026 réduit le texte des écrans participants d’environ 16 % en français et 15 % en anglais. Le comptage porte sur les chaînes traduites de `intro.js` et `campagne-joueur.js`, hors balises HTML, comparées à l’archive source précédente. Les répétitions et les invitations générales à discuter sont réduites ; montants, conditions, droits et risques restent présents. Les pourcentages servent toujours à négocier les contrats ; les comptes rendus affichent les montants réalisés en crédits.

Le parcours anglais rapproche les quatre montants du relevé avec les mouvements privés pour chacun des quatre trimestres, décembre compris, et vérifie l’affichage mobile sans pourcentage dans le relevé.

Le moteur teste les révisions, les contraintes financières, les restrictions de mobilité, la reprise des aléas, le compte de chaque entreprise et le rapprochement recettes/coûts/valeur collective. Une référence de décision empêche les doubles dépenses.

Deux tests de campagne vérifient un refus maintenu pendant les quatre trimestres sans bloquer un service voisin et un lancement tardif sans rattrapage. Le parcours navigateur contrôle les six écrans du briefing, la lecture manuelle en réduction des animations, les repères de trimestre et un territoire sans accord pendant toute l’année.

Le parcours navigateur couvre cinq rôles sur trois rubriques, vingt participants, quatre territoires et plusieurs branches réelles : accord, infrastructure indisponible, remplacement, retour, départ de BRAIN, hausse privée des frais de FLEET, demande de renégociation, suspension de sa capacité, avenant de retour, baisse collective des recettes et clôture. Les vues étroites sont contrôlées. Les comptes sont repris par un nouveau processus serveur et l'export du bilan est vérifié.

Les données complètes et les paramètres des tirages sont accessibles au seul enseignant authentifié, après clôture des décisions de l'année. Les téléphones reçoivent leur propre nœud, leurs chiffres privés et le passé public de leur territoire.

## Débrief et visualisations

Les données nécessaires aux cinq visualisations sont transmises uniquement au tableau enseignant, après clôture de décembre. Les comptes des autres groupes et les informations privées ne sont pas ajoutés aux téléphones des participants. L'accès HTTP au rapport HTML demande la clé enseignant et une campagne terminée.

Les vues distinguent recettes, résultat net, valeur collective et revenus extérieurs. Les pourcentages des accords signés ne sont pas présentés comme des parts de bénéfice. Les périodes sans accord, sans recettes et sans nouvel événement sont représentées comme telles. Une sélection de faits marquants et leurs séquences est disponible ; le journal complet conserve aussi les choix et réponses individuels.

Le rapport autonome contient les agrégats et faits nécessaires aux graphiques, sans annuaire des participants ni jetons. Le CSV d'une vue est en crédits ; les montants du ZIP sont en centièmes de crédit. Les chiffres exacts restent consultables sous chaque graphique.
