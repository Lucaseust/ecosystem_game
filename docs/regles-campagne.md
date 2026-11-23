# Règles de la campagne 2032 — enseignant

Le moteur courant est `eco/campaign.py`, schéma de sauvegarde `campaign-2.0`, règles `campaign-3.0`. Ces paramètres sont ceux de cette première calibration jouable. Les chiffres privés des autres rôles et les événements futurs ne sont pas à projeter pendant la négociation.

## Une seule dotation et des flux persistants

Chaque entreprise commence avec **20 crédits**. Les comptes ne sont jamais réinitialisés. Les coûts d'installation sont payés une fois lorsque le premier accord entre en vigueur.

| Entreprise | Installation de base | Frais par trimestre d'exploitation engagée | Activité extérieure de base par trimestre disponible |
| --- | ---: | ---: | ---: |
| MOBI | 3 | 1 | 0 |
| AUTO | 5 | 2 | 3 |
| BRAIN | 4 | 2 | 4 |
| GRID | 4 | 1 | 2 |
| FLEET | 5 | 2 | 4 |

Les frais d'exploitation sont dus lors d'une exploitation engagée même si les essais ou un délai empêchent des recettes. L'activité extérieure est payée seulement lorsque la même capacité n'est pas engagée dans cette exploitation. Un partenaire sorti perçoit son activité extérieure ; il ne perçoit plus de part du transport.

Un défaut de financement empêche une nouvelle exploitation : aucune trésorerie négative n'est créée silencieusement. Le contrat peut être révisé pour permettre la reprise. Les dépenses initiales restent perdues si le projet ne rapporte rien.

## Engagements individuels

Chaque humain choisit avant le premier accord ; un changement invalide la proposition ouverte. Les coûts supplémentaires sont privés jusqu'à leur révélation volontaire.

- MOBI : service local, ou relation client renforcée pour 2 crédits ; celle-ci ajoute 2 crédits aux recettes trimestrielles du transport.
- AUTO : véhicules dédiés, ou reconfigurables pour 2 crédits ; une intervention ultérieure coûte 1 crédit de moins.
- BRAIN : licence sans exclusivité, ou engagement jusqu'en décembre ; l'exclusivité ajoute 2 crédits aux recettes trimestrielles et interdit d'accepter une activité concurrente avant la fin de l'année.
- GRID : recharge initiale, ou réserve pour 2 crédits ; cette réserve réduit de 2 crédits le coût d'une intervention sur l'infrastructure ou d'une extension tant que GRID assure cette position.
- FLEET : exploitation standard, ou préparation renforcée pour 2 crédits ; celle-ci réduit le risque d'interruption au lancement et de 2 crédits le coût d'intervention.

Les sièges sans étudiant sont explicitement automatiques. Ils retiennent l'engagement de base et consentent si les revenus projetés sur l'horizon restant, nets de leurs coûts et contributions, couvrent leur activité extérieure. Ils ne révèlent pas leur seuil dans l'interface.

## Premier accord

À chaque tour, MOBI propose des recettes et des investissements en crédits (au centième près). Les recettes attribuées doivent totaliser les recettes collectives à pleine capacité ; les contributions doivent financer exactement le devis. Un nouvel accord unanime est obligatoire à chaque tour. Sans accord, les recettes, frais d’exploitation et revenus extérieurs du tour sont nuls ; aucun contrat précédent n’est reconduit. Les investissements déjà payés restent acquis. Les incidents peuvent réduire les recettes et les versements convenus dans la même proportion.

- **Interfaces intégrées** : 40 crédits de recettes par trimestre à pleine capacité, avant les effets des engagements et de l'extension. Pas de coût collectif initial supplémentaire.
- **Interfaces communes/documentées** : 38 crédits et 6 crédits d'installation collective. Les interventions sont plus rapides et moins coûteuses.
- **Ouverture dès validation** : pleine capacité au premier trimestre de fonctionnement, sous réserve des essais obligatoires.
- **Pilote progressif** : 3 crédits de préparation collective, 75 % des recettes au premier trimestre exploité et risque d'interruption réduit.

Les contributions collectives financent exactement le devis. Les coûts privés d'installation et d'engagement s'y ajoutent. Aucune dépense n'est engagée avant le consentement de tous les acteurs requis. Une nouvelle version efface les réponses précédentes, pas le contrat déjà signé.

## Aléas du lancement et de l'extension

Un seul tirage de mise en service, au premier trimestre effectivement exploité, même si le démarrage est tardif :

| Lancement | FLEET standard | FLEET préparé |
| --- | ---: | ---: |
| Dès validation | 45 % d'interruption | 25 % |
| Pilote progressif | 5 % | 3 % |

Une interruption supprime les recettes de la période ; les actifs restent installés et les frais d'exploitation engagée sont payés. Les essais ne sont pas tirés de nouveau au trimestre suivant.

Une extension coûte 6 crédits, ou 4 avec la réserve de GRID actif, et ajoute 10 crédits aux recettes des trimestres suivants, y compris le trimestre où elle est engagée. Sa première mise en charge comporte un risque de recettes réduites de moitié pour la période : 35 % sans réserve/préparation, 8 % avec une réserve GRID ou une préparation FLEET. Les capacités restent installées après cet essai.

L'extension est disponible lors d'une demande locale ou dans la dernière fenêtre si l'exploitation est active. Une seule extension par territoire.

## Événements locaux

À l'ouverture d'avril, juillet **et octobre**, chaque territoire reçoit un tirage local. Les poids de base sont :

| Famille | Poids de base | Effet |
| --- | ---: | --- |
| Activité ordinaire | 15 % | Nouvel accord en crédits requis pour ce tour. |
| Demande supplémentaire | 15 % | Possibilité d'extension à financer. |
| Offre à BRAIN | 15 % | Nouvelle activité extérieure et négociation possible. |
| Hausse de coûts privée | 20 % | AUTO, GRID ou FLEET voit ses frais trimestriels augmenter de 2, 3 ou 4 crédits jusqu'en décembre. |
| Baisse de contribution publique | 15 % | Les recettes collectives à pleine capacité diminuent de 6, 10 ou 14 crédits par trimestre jusqu'en décembre. |
| Infrastructure indisponible | 10 % | Le service est interrompu jusqu'à adaptation ou remplacement. |
| Exigence de certification | 10 % | Une adaptation doit être financée pour reprendre le service. |

Ces nombres sont des **poids initiaux**, pas des probabilités inconditionnelles garanties. Les familles incompatibles avec la situation sont écartées avant le tirage, puis les poids restants sont normalisés. Une flotte active ne peut pas tirer deux périodes ordinaires consécutives. Une extension déjà réalisée, une baisse de contribution déjà appliquée ou une offre de mobilité incompatible ne donnent pas une carte sans effet. Les entreprises déjà touchées par une hausse ne subissent pas deux fois cette même hausse.

Le tirage utilise une valeur unique déterministe par graine, territoire, date et canal. Il n'y a pas de relance jusqu'à obtenir un résultat souhaité. Le journal conserve les poids de base, les candidats réellement disponibles, les exclusions et leurs motifs, la valeur tirée et l'intensité. Les canaux distincts d'intensité et de cible préservent la reproduction des scénarios. Les intensités ont trois niveaux équiprobables ; la cible privée est choisie parmi les rôles AUTO/GRID/FLEET éligibles.

Un territoire non constitué, suspendu ou toujours en difficulté conserve sa situation avec un texte approprié. Les autres groupes continuent. Il ne reçoit pas une panne de navettes qu'il n'exploite pas.

**Hausse privée.** Le montant n'est envoyé qu'au rôle concerné, y compris en binôme. Il est effectivement ajouté à ses frais lorsqu'il est engagé dans la flotte ; il n'est pas débité en activité extérieure. Le rôle peut conserver le contrat, publier une demande de renégociation sans révéler le montant, ou suspendre sa capacité si aucune autre position n'est déjà manquante/remplacée et qu'aucun incident n'a déjà arrêté la flotte. Cette suspension interrompt les trajets ; un retour ou un remplacement exige un nouvel accord. La hausse persiste si l'entreprise revient. Les autres entreprises et le tableau projeté ne voient pas ses chiffres privés.

À chaque tour, MOBI propose des recettes et des investissements en crédits (au centième près). Les recettes attribuées doivent totaliser les recettes collectives à pleine capacité ; les contributions doivent financer exactement le devis. Un nouvel accord unanime est obligatoire à chaque tour. Sans accord, les recettes, frais d’exploitation et revenus extérieurs du tour sont nuls ; aucun contrat précédent n’est reconduit. Les investissements déjà payés restent acquis. Les incidents peuvent réduire les recettes et les versements convenus dans la même proportion.

L'offre à BRAIN porte son revenu extérieur à **9 crédits par trimestre** à partir d'un départ accepté dans la fenêtre concernée, jusqu'en décembre. Le montant est connu de BRAIN seul. Une exclusivité consentie interdit le départ et exclut une nouvelle offre sans effet. Une seule position peut être confiée à un substitut dans un territoire.

Les sauvegardes et tirages déjà réalisés restent inchangés. Chaque nouvel événement indique sa version de règles. L'export distingue la version du moteur, celle des derniers événements de la séance et les paramètres des versions présentes dans le journal ; il ne réattribue pas les nouveaux poids à un ancien tirage.

## Intervenir ou recomposer

| Solution | Interfaces intégrées | Interfaces communes |
| --- | --- | --- |
| Réparer/adapter | 7 crédits ; moitié des recettes de la période | 3 crédits ; reprise pendant la période |
| Remplacer un fournisseur indisponible/sorti | 9 crédits ; pas de recette de transport durant l'intégration | 3 crédits ; reprise pendant la période |
| Financer ultérieurement des interfaces communes | 8 crédits ; les actifs et dépenses précédents restent conservés | Déjà réalisées |

Les réductions de coût liées aux engagements s'appliquent, avec un minimum d'un crédit d'intervention. Le devis exact et le délai sont affichés dans la proposition avant tout consentement. Les risques de mise en service ou de montée en charge peuvent également s'appliquer si ces essais n'ont pas encore eu lieu.

Le substitut exige au moins 6 crédits de recettes par trimestre. Le partenaire écarté ne vote pas sur cette proposition et ne peut être facturé pour son remplacement. Il conserve ses résultats, peut travailler à l'extérieur et proposer son retour. Le retour nécessite un nouvel accord des cinq partenaires ; il ne rembourse pas une substitution antérieure.

Suspendre l'exploitation ne répare pas un incident. Changer le partage ne modifie pas gratuitement les interfaces ou un engagement individuel déjà payé. Revoir les interfaces d'un service suspendu ne le remet pas automatiquement en exploitation.

## Bilan et comptes

Résultat individuel : trésorerie finale moins la dotation initiale de 20 crédits, comprenant le projet et l'activité extérieure.

Valeur collective du transport : recettes clients moins les coûts d'installation, d'engagement, d'intervention, d'exploitation et de fournisseur extérieur. Les parts reçues par les partenaires répartissent une recette ; elles ne constituent pas cinq recettes différentes. L'activité extérieure des acteurs n'est pas ajoutée à la valeur collective du transport.

Le journal et les transactions reconstruisent les soldes sans arrondi flottant ; le moteur travaille en centièmes de crédit. Les éventuels centièmes de répartition sont attribués de manière déterministe à la première part du contrat.

## Calibration initiale

`python tests/simuler_campagne.py` compare 320 campagnes synthétiques avec les mêmes 80 graines pour quatre combinaisons d'interfaces et de lancement. La politique de réaction répare les incidents, sans faire quitter les partenaires ni optimiser la négociation après une hausse de coûts ou une baisse de recettes. Chaque combinaison obtient le meilleur résultat dans au moins un contexte testé. Cette vérification ne couvre pas toutes les négociations humaines ni toutes les politiques possibles ; une séance pilote permettra de revoir les paramètres à partir des données exportées, en changeant alors explicitement la version des règles.

Chaque joueur peut publier les recettes qu’il demande, l’investissement collectif maximal qu’il propose et ses raisons. Une discussion publique permet d’interpeller un partenaire, de proposer une concession et d’expliquer une acceptation ou un refus. Les demandes ne remplacent pas le consentement au contrat publié. Les informations privées ne sont révélées que par leur propriétaire.
