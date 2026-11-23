# ECOSYSTEM

**Un jeu de stratégie sur l'alignement, l'orchestration et l'architecture des écosystèmes**

Conception pédagogique et guide d'animation.

Ce document décrit le concept historique à manches. La campagne narrative cumulative désormais jouable par défaut est développée dans [architecture-narrative.md](architecture-narrative.md), et ses règles chiffrées dans [docs/regles-campagne.md](docs/regles-campagne.md).
Pour faire tourner la plateforme, voir [README.md](README.md).

---

## L'essentiel en une page

| | |
| --- | --- |
| **Durée** | 60 minutes, débrief compris |
| **Effectif** | 15 à 25 étudiants (calibré pour 20) |
| **Niveau** | Master — stratégie, innovation, management de la technologie |
| **Format** | 4 écosystèmes concurrents de 5 rôles, 3 rounds, 1 choc |
| **Matériel** | un ordinateur, un vidéoprojecteur, un téléphone par étudiant |
| **Références** | Adner (*ecosystem as structure*), Jacobides (complémentarités, modularité) |

**Le ressort du jeu.** Quatre consortiums doivent lancer le même service de
navettes autonomes. Aucun ne peut le faire seul : il faut cinq entreprises
indépendantes, et il suffit qu'une seule refuse pour que rien n'existe. Le
premier round est truqué — la répartition imposée des revenus est
collectivement rentable mais individuellement inacceptable pour deux acteurs.
Les écosystèmes échouent. Les étudiants découvrent alors qu'ils doivent
redistribuer la valeur avant de pouvoir la créer.

**Les trois messages à faire passer.**

1. La valeur collective ne suffit pas : chaque acteur compare sa part à ce
   qu'il obtiendrait ailleurs. `Collective Value ≠ Individual Incentives`
2. Orchestrer n'est pas commander : l'orchestrateur négocie, il n'ordonne pas.
   `Orchestration ≠ Hierarchy`
3. L'architecture technique redistribue le pouvoir de négociation.
   `Modularity → Substitutability → Bargaining Power`

**Le résultat recherché.** Qu'un étudiant puisse dire, à la fin :

> « J'étais l'orchestrateur et j'avais le meilleur business model, mais je ne
> pouvais pas lancer le service parce que deux partenaires n'avaient aucun
> intérêt à faire les investissements nécessaires. Quand j'ai redistribué la
> valeur, le service est devenu possible. Ensuite notre architecture
> propriétaire était plus efficace, mais elle nous a rendus dépendants de
> notre fournisseur d'IA. »

À ce moment-là, l'étudiant a compris la logique d'un écosystème.

---

# Partie I — Intentions pédagogiques

## 1. Le problème que le jeu met en scène

Un cours magistral sur les écosystèmes produit des étudiants capables de
réciter une définition d'Adner et incapables de l'utiliser. La difficulté
n'est pas conceptuelle, elle est expérientielle : tant qu'on n'a pas soi-même
été le partenaire dont la participation était indispensable et la rémunération
insuffisante, la notion d'*alignment structure* reste un mot.

Le jeu place donc chaque étudiant dans une position où :

- il dépend d'acteurs qu'il ne contrôle pas ;
- il détient une information que les autres n'ont pas ;
- il a un intérêt individuel qui peut diverger de l'intérêt collectif ;
- il doit décider sans certitude sur ce que les autres feront.

## 2. Ce que les étudiants doivent avoir compris à la fin

- la proposition de valeur comme point de départ de l'écosystème ;
- les notions d'**activities, actors, positions, links** chez Adner ;
- l'**alignment structure** : un partenaire techniquement capable peut
  refuser de participer ;
- la différence entre **création** de valeur collective et **capture**
  individuelle de valeur ;
- pourquoi l'orchestration ne correspond pas à une autorité hiérarchique ;
- comment la modularité, les standards et les interfaces structurent les
  complémentarités ;
- le compromis entre optimisation d'une architecture et capacité à remplacer
  un partenaire ;
- pourquoi un écosystème n'est ni simplement une supply chain, ni
  nécessairement une plateforme.

## 3. Comment chaque round produit son apprentissage

| Round | Ce que l'étudiant vit | Ce qu'il en tire |
| ----- | --------------------- | ---------------- |
| **1 — The Great Idea** | Une bonne idée, des partenaires compétents, et pourtant l'échec | Une proposition de valeur ne suffit pas ; l'alignement est un problème à part entière |
| **2 — Alignment** | La négociation de la répartition, avec information privée et bluff | Il faut redistribuer assez de valeur pour que chacun accepte sa position |
| **3 — Architecture** | Un choix technique, puis un choc qui en révèle le prix | L'architecture n'est pas une question technique : elle décide qui dépend de qui |

Le round 1 doit **échouer**. C'est son rôle. Ne cherchez pas à le sauver.

---

# Partie II — Le dispositif

## 4. La situation

Les étudiants sont en **2032**. Quatre consortiums concurrents cherchent à
lancer, dans une grande métropole européenne, un service de navettes
autonomes. La proposition de valeur est identique pour tous :

> **Permettre à un utilisateur de réserver à la demande une navette autonome,
> avec moins de dix minutes d'attente, un trajet fiable et un prix inférieur à
> celui d'un taxi.**

Aucune entreprise ne possède seule les ressources nécessaires. Chaque
écosystème comprend cinq organisations indépendantes. Chaque étudiant conserve
le même rôle pendant toute la partie.

Les quatre écosystèmes s'appellent **BLUE**, **GREEN**, **RED** et **YELLOW**.
Ils ne négocient pas entre eux : la concurrence est un décor qui met la
pression, pas un mécanisme de jeu.

## 5. Les cinq rôles

### MOBI — Orchestrateur

Possède l'application, la marque, la relation client, le système de
réservation, le paiement, une partie des données utilisateurs. MOBI formule la
proposition de valeur et assemble l'écosystème.

MOBI ne possède ni les véhicules, ni l'IA de conduite, ni les stations de
recharge, ni les opérations terrain. **MOBI ne peut donner d'ordres à
personne.**

### AUTO — Constructeur automobile

Fournit et adapte les véhicules : intégration du système de conduite
autonome, modifications, conformité, interfaces avec les systèmes des autres
partenaires.

### BRAIN — Fournisseur d'IA

Fournit le système de conduite autonome, les modèles, la cartographie, les
flux de données temps réel. Sa technologie est propriétaire et peut être
vendue à d'autres clients — ce qui lui donne une bonne option extérieure.

### GRID — Infrastructure

Possède et exploite les stations de recharge, certains dépôts, les
infrastructures de maintenance, les interfaces énergétiques. Le projet
nécessite des adaptations spécifiques de son infrastructure.

### FLEET — Opérateur

Assure l'exploitation quotidienne, la supervision, le repositionnement des
véhicules, la maintenance légère, la gestion des incidents. **Sans opérateur,
le service n'existe pas, même lorsque toutes les technologies fonctionnent.**

FLEET est le rôle le moins prestigieux et le plus instructif : indispensable à
la création de valeur, mal placé pour la capturer.

## 6. Ressources, coûts et options extérieures

Chaque acteur reçoit **10 points de ressources à chaque round**. Ils
représentent son budget, son temps et ses capacités disponibles.

| Acteur | Coût d'investissement `C` | Option extérieure `O` |
| ------ | ------------------------: | --------------------: |
| MOBI | 3 | 0 |
| AUTO | 5 | 3 |
| BRAIN | 4 | 4 |
| GRID | 4 | 2 |
| FLEET | 5 | 4 |
| **Total** | **21** | **13** |

L'**option extérieure** est ce que l'entreprise obtient si elle refuse de
participer et emploie ses ressources ailleurs. C'est le cœur du jeu : elle
transforme « est-ce rentable ? » en « est-ce plus rentable que mon
alternative ? ».

Ces deux chiffres sont **privés**. Chaque étudiant ne voit que les siens. Il
peut les révéler, les cacher, ou mentir.

## 7. Calcul des scores

Pour chaque acteur `i`, à chaque round :

| Situation | Score |
| --------- | ----- |
| Participe, et l'écosystème réussit | `10 − C + R` |
| Participe, et l'écosystème échoue | `10 − C` |
| Refuse de participer | `10 + O` |

où `R` est le revenu reçu dans l'écosystème.

**Valeur collective de l'écosystème :**

| Situation | Score collectif |
| --------- | --------------- |
| Le service est lancé | `V − Σ coûts engagés` |
| Le service n'est pas lancé | `− Σ investissements perdus` |

Deux classements distincts sont affichés à la fin :

- **INDIVIDUAL WINNER** — l'entreprise ayant accumulé le plus de points ;
- **ECOSYSTEM WINNER** — l'écosystème ayant créé la plus grande valeur
  collective.

Les deux comptent. Ne récompensez pas seulement le meilleur écosystème : la
tension entre rationalité individuelle et réussite collective disparaîtrait,
et les étudiants coopéreraient parfaitement dès le départ.

## 8. Condition de réussite

Le service nécessite simultanément **MOBI + AUTO + BRAIN + GRID + FLEET**.

- Si les cinq participent : `V = 40`
- Si un seul manque : `V = 0`

Il n'existe pas de service « à 80 % ». Cette mécanique représente une forte
complémentarité entre activités : la valeur d'un investissement dépend
entièrement de la présence des autres.

---

# Partie III — Règles des trois rounds

## 9. Round 1 — The Great Idea

### Objectif

Faire découvrir que **bonne proposition de valeur ≠ écosystème viable**.

### Règle

MOBI annonce une répartition **imposée et non modifiable** des 40 points :

| Acteur | Revenu |
| ------ | -----: |
| MOBI | 14 |
| AUTO | 10 |
| BRAIN | 6 |
| GRID | 6 |
| FLEET | 4 |
| **Total** | **40** |

Les étudiants disposent de **5 minutes** pour discuter. Ils peuvent expliquer
leurs contraintes, argumenter, promettre, bluffer, révéler ou cacher leur
coût. **Aucun transfert de points n'est autorisé.**

À la fin, tous choisissent simultanément **JOIN** ou **OUT**. Les décisions
sont secrètes jusqu'à révélation.

### Ce qui va se passer

| Acteur | Participer | Sortir | Décision rationnelle |
| ------ | ---------: | -----: | -------------------- |
| MOBI | `10−3+14 = 21` | `10+0 = 10` | participe |
| AUTO | `10−5+10 = 15` | `10+3 = 13` | participe |
| BRAIN | `10−4+6 = 12` | `10+4 = 14` | **refuse** |
| GRID | `10−4+6 = 12` | `10+2 = 12` | indifférent |
| FLEET | `10−5+4 = 9` | `10+4 = 14` | **refuse** |

Deux acteurs sur cinq ont intérêt à sortir. L'écosystème ne peut pas se
lancer. C'est le résultat attendu.

### Ce que vous ne dites pas encore

Il y a largement assez de valeur pour rendre tout le monde gagnant :

```
Valeur créée                40
Coûts totaux              − 21
Options extérieures       − 13
                          ────
Surplus disponible           6
```

Le problème n'est donc pas l'absence de valeur. C'est **la distribution de
cette valeur**, et donc l'alignement des acteurs.

## 10. Round 2 — Alignment

### Objectif

Introduire les contraintes de participation, l'orchestration, la négociation,
la capture de valeur et l'information privée. La question devient :

> Quelle configuration rend chacun suffisamment gagnant pour accepter sa
> position dans l'écosystème ?

### Reset

Chaque joueur reçoit à nouveau 10 points de ressources. Le score du round 1
reste au classement mais n'handicape pas le round 2 : un écosystème qui a
échoué n'est pas condamné pour le reste de la partie.

### Règle

La valeur reste `V = 40`, mais les 40 points sont désormais **librement
répartissables**. Seule contrainte : `Σ R = 40`.

Les étudiants disposent de **8 minutes** pour négocier les revenus, les
compensations, les responsabilités et les conditions de participation. MOBI
dépose le contrat final, mais **ne peut imposer aucune signature**.

Puis chacun choisit secrètement JOIN ou OUT. Le contrat ne peut plus être
modifié après ouverture des votes.

### Les seuils réels

Pour qu'un acteur préfère l'écosystème à son option extérieure, il faut
`R − C ≥ O`, donc `R ≥ C + O` :

| Acteur | Seuil `C + O` |
| ------ | ------------: |
| MOBI | 3 |
| AUTO | 8 |
| BRAIN | 8 |
| GRID | 6 |
| FLEET | 9 |
| **Total** | **34** |

Il reste `40 − 34 = 6` points de surplus à se partager. **C'est là que
commence la négociation stratégique.**

Ces seuils doivent rester privés. Les étudiants peuvent dire la vérité,
exagérer leur coût, prétendre avoir une meilleure option extérieure, ou
menacer de sortir. FLEET peut annoncer « en dessous de 12 je ne participe
pas » alors que son seuil réel est 9. L'orchestrateur doit aligner ses
partenaires **sans connaître leurs contraintes**.

## 11. Round 3 — Architecture

### Objectif

Faire comprendre que la structure technique influence les dépendances, la
substituabilité, le pouvoir de négociation, la résilience et la capacité
d'évolution. L'architecture n'est pas une question purement technique.

### Le choix — 3 minutes

Chaque écosystème choisit, **sans savoir ce qui va suivre** :

| | **A — Intégrée / propriétaire** | **B — Modulaire / standardisée** |
| --- | --- | --- |
| Description | intégrations optimisées spécifiquement entre membres | API communes, formats standardisés, interfaces documentées |
| Valeur du service | **46** | **40** |
| Coût collectif initial | 0 | **6**, à répartir entre les acteurs |
| Remplacer un partenaire | 8 | 2 |
| Retard en cas de remplacement | **−12** de valeur | aucun |

Si MODULAR est choisi, l'équipe répartit les 6 points du standard entre les
cinq acteurs. Ces contributions sont retirées de leur score, **quoi qu'il
arrive ensuite**.

### Le choc — une fois les architectures verrouillées

> **BREAKING NEWS — AI CERTIFICATION FAILURE**
>
> Le régulateur vient d'annoncer que la version actuelle du système autonome
> de BRAIN ne pourra pas obtenir la certification nécessaire dans les délais.
>
> BRAIN peut adapter son système, mais cette adaptation nécessite un
> investissement supplémentaire de **6 points**.
>
> Vous pouvez également remplacer BRAIN par **ALT-AI**, un fournisseur
> compatible mais légèrement moins performant, qui n'acceptera pas la position
> en dessous de **8 points** de revenu.
>
> Vous disposez de cinq minutes pour sauver votre écosystème.

### Les trois solutions — 5 minutes

**Solution 1 — conserver BRAIN.** BRAIN paie 6 points supplémentaires.
L'équipe peut renégocier la répartition pour le compenser. Si BRAIN refuse, le
service ne peut pas utiliser sa technologie. Cette situation permet souvent à
BRAIN de renégocier fortement sa position — laissez faire, c'est le but.

**Solution 2 — remplacer BRAIN par ALT-AI.** Le coût d'intégration est à
répartir entre les quatre acteurs restants. BRAIN bascule sur son option
extérieure. ALT-AI refuse en dessous de 8 points.

**Solution 3 — abandonner.** `V = 0`. Chacun reprend son option extérieure ;
les contributions déjà versées au standard restent perdues.

### Résultats selon la configuration

| Architecture | Solution | Valeur du service | Valeur collective |
| ------------ | -------- | ----------------: | ----------------: |
| Propriétaire | conserver BRAIN | 46 | `46 − 21 − 6` = **19** |
| Propriétaire | remplacer | `46 − 12` = 34 | `34 − 21 − 8` = **5** |
| Modulaire | conserver BRAIN | 40 | `40 − 21 − 6 − 6` = **7** |
| Modulaire | remplacer | 40 | `40 − 21 − 6 − 2` = **11** |

Le barème n'est **volontairement pas** construit pour faire de la modularité
une solution universellement supérieure. L'architecture propriétaire qui garde
son partenaire reste la plus performante. La modularité est une **assurance
contre l'incertitude**, pas une recette.

C'est le point le plus subtil du jeu, et celui qui mérite le plus de temps au
débrief.

---

# Partie IV — Guide d'animation

## 12. Avant la séance

### La veille

- [ ] Lancer la plateforme et **vérifier la connexion depuis votre propre
      téléphone, Wi-Fi coupé, en 4G** (voir [README.md](README.md), section 2).
      C'est le seul point qui peut ruiner la séance.
- [ ] Parcourir une fois l'onglet « Débrief » du tableau de bord : ce sont vos
      planches de projection, dans l'ordre.
- [ ] Décider de la récompense symbolique annoncée aux deux gagnants.

### Le jour même, avant l'arrivée des étudiants

- [ ] Lancer le serveur, projeter le tableau de bord, afficher le QR.
- [ ] Vérifier que le chrono est visible depuis le fond de la salle.
- [ ] Disposer la salle en **quatre îlots séparés**. Les équipes doivent
      pouvoir parler sans être entendues des autres. C'est plus important
      qu'il n'y paraît : l'information privée est le moteur du jeu.

### Ce que vous n'annoncez pas au début

- qu'il existe un surplus de 6 points ;
- que le round 1 est conçu pour échouer ;
- qu'un choc arrivera au round 3.

## 13. Minutage

| Temps | Séquence | Durée |
| ----- | -------- | ----: |
| 0–5 | Accueil, connexion, distribution des rôles | 5 min |
| 5–10 | Round 1 — négociation | 5 min |
| 10–12 | Round 1 — décisions | 2 min |
| 12–15 | Round 1 — résultats et question ouverte | 3 min |
| 15–23 | Round 2 — négociation | 8 min |
| 23–25 | Round 2 — décisions | 2 min |
| 25–29 | Round 2 — résultats et mini-débrief | 4 min |
| 29–32 | Round 3 — choix d'architecture | 3 min |
| 32–34 | Ecosystem shock — lecture de la carte | 2 min |
| 34–39 | Round 3 — sauvetage | 5 min |
| 39–41 | Round 3 — décisions | 2 min |
| 41–45 | Résultats et classements | 4 min |
| 45–60 | Débrief | 15 min |

Le tableau de bord affiche à chaque phase un rappel de ce que vous avez à
dire. Vous avancez avec **Suivant ▶** ou la flèche droite ; la barre d'espace
démarre et arrête le chrono.

## 14. Séquence par séquence

### 0–5 min · Accueil

**Vous dites :**

> « Nous sommes en 2032. Une grande métropole européenne veut un service de
> navettes autonomes à la demande. Quatre consortiums sont en compétition.
> Vous allez chacun diriger une entreprise. »

Faites scanner le QR. Attendez que tout le monde soit connecté avant de
lancer le round 1 — les rôles se stabilisent à mesure que la classe arrive.

Lisez la proposition de valeur à voix haute, lentement. Puis :

> « Chacun d'entre vous reçoit 10 points de ressources à chaque round. Votre
> fiche est privée : vous seul connaissez votre coût d'investissement et ce
> que vous pourriez gagner ailleurs si vous refusiez ce projet. Vous êtes
> libres d'en parler, de le cacher, ou de mentir. »

> « Deux prix seront décernés : la meilleure entreprise, et le meilleur
> écosystème. Ce ne sera pas forcément le même. »

**Vous ne dites pas** : que le round 1 va échouer.

### 5–10 min · Round 1, négociation

**Vous dites :**

> « MOBI a annoncé la répartition des 40 points de revenu. Elle est affichée
> sur vos téléphones. Elle est imposée : personne ne peut la modifier ce
> round, pas même MOBI. »

> « Vous avez cinq minutes pour discuter. Vous pouvez tout faire sauf vous
> transférer des points. Ensuite chacun choisira JOIN ou OUT, en secret. »

**Ce que vous surveillez :** circulez entre les îlots. Vous devriez entendre
BRAIN et FLEET expliquer que le compte n'y est pas, et MOBI répondre que
c'est comme ça. Ne commentez pas. Ne validez ni n'infirmez leurs calculs.

**Si un étudiant vous demande** « est-ce que j'ai intérêt à participer ? » —
renvoyez-le à sa fiche : « comparez les deux lignes vous-même. »

### 10–12 min · Round 1, décisions

> « Décisions simultanées et secrètes. Vous pouvez encore changer d'avis tant
> que je n'ai pas révélé les résultats. »

Surveillez le compteur « n/5 décisions reçues » sur chaque écosystème.
Attendez les retardataires. Un étudiant qui ne répond pas est compté comme
OUT — dites-le à voix haute pour que personne ne subisse ce sort par
inattention.

### 12–15 min · Round 1, résultats

Passez aux résultats. Laissez l'écran parler : la ligne rouge du dernier
acteur manquant est très efficace visuellement.

**Ne faites pas de cours maintenant.** Posez une seule question :

> « Vous aviez une technologie qui marche, des clients qui veulent le service,
> et 40 points de valeur à créer. Pourquoi cela n'a-t-il pas fonctionné ? »

Prenez deux ou trois réponses. N'en corrigez aucune. Puis :

> « Vous avez une deuxième tentative. Cette fois, vous pouvez modifier
> l'accord. »

Ne dites rien de plus. La compréhension doit venir du round 2, pas de vous.

### 15–23 min · Round 2, négociation

> « Les 40 points sont toujours là, mais ils sont désormais librement
> répartissables. La seule règle : le total doit faire exactement 40. »

> « MOBI dépose le contrat. Mais MOBI ne peut imposer aucune signature. Si
> quelqu'un refuse, il n'y a pas de service, et MOBI perd son investissement
> comme les autres. »

> « Huit minutes. »

**Ce que vous surveillez :**

- **Un écosystème qui bloque** : généralement MOBI refuse de descendre en
  dessous de 12. Ne soufflez pas la réponse. Demandez plutôt à MOBI :
  « qu'est-ce que vous gagnez si le service ne se lance pas ? »
- **Un écosystème qui converge trop vite** vers 8 points chacun : c'est un
  contrat viable mais peu réfléchi. Demandez à FLEET, à voix basse : « êtes-vous
  sûr que c'est votre meilleure offre ? »
- **Les surenchères** : un acteur qui annonce un seuil très supérieur à son
  seuil réel. C'est exactement le comportement recherché. Notez qui le fait,
  vous vous en servirez au débrief.

MOBI peut publier plusieurs versions du contrat pendant la négociation : les
partenaires voient la proposition évoluer sur leur téléphone.

### 23–25 min · Round 2, décisions

> « Le contrat est verrouillé. Il ne peut plus être modifié. Chacun choisit. »

### 25–29 min · Round 2, résultats et mini-débrief

La plupart des écosystèmes se lancent. Deux minutes de questions, pas plus :

> « Qui avait réellement le pouvoir de négociation ? Était-ce nécessairement
> MOBI ? »

> « L'orchestrateur pouvait-il simplement décider ? »

> « Pourquoi certains acteurs ont-ils reçu davantage qu'au round 1 ? »

Puis enchaînez sans conclure :

> « Votre écosystème fonctionne maintenant. Mais vous devez choisir son
> architecture technique avant son déploiement à grande échelle. »

### 29–32 min · Round 3, architecture

**Vous dites, et rien d'autre :**

> « Le marché et l'environnement réglementaire sont incertains. Une
> architecture doit maintenant être choisie pour les trois prochaines
> années. »

> « Trois minutes. »

**N'annoncez surtout pas le choc.** Toute la valeur pédagogique du round 3
repose sur le fait que le choix est fait dans l'ignorance de ce qui suit.
C'est la seule information que vous devez protéger absolument.

Si un étudiant demande « à quoi sert la modularité si on ne change personne ? »
— répondez : « c'est exactement la question. »

### 32–34 min · Ecosystem shock

Une fois **tous** les choix verrouillés, passez à la carte de choc.
**Lisez-la lentement, à voix haute.** Laissez trois secondes de silence après
la dernière phrase.

Vous verrez les équipes propriétaires réaliser ce qui vient de leur arriver.
C'est le moment le plus utile de la séance : ne le comblez pas par du
commentaire.

### 34–39 min · Round 3, sauvetage

> « Cinq minutes. Vous pouvez redistribuer les revenus, financer BRAIN, le
> remplacer, ou renoncer au projet. »

**Ce que vous surveillez :** BRAIN est en position de force dans les
écosystèmes propriétaires et en position faible dans les écosystèmes
modulaires. Circulez pour observer les deux cas — vous en aurez besoin au
débrief. Si un BRAIN exige beaucoup, ne le freinez pas : c'est la
démonstration.

### 39–41 min · Round 3, décisions

> « Décisions finales. Plus aucune modification. »

### 41–45 min · Résultats et classements

Affichez l'onglet « Classements ». Prenez le temps sur deux points :

1. Comparez les écosystèmes propriétaires et modulaires. S'ils ont fait des
   choix différents face au même choc, vous avez votre démonstration.
2. Cherchez un étudiant qui est **meilleure entreprise sans être dans le
   meilleur écosystème**. Nommez-le. C'est l'illustration la plus nette de
   `Value Creation ≠ Value Capture`.

## 15. Problèmes fréquents et conduite à tenir

| Situation | Conduite |
| --------- | -------- |
| **Le round 1 réussit dans un écosystème** | Excellent matériau. Demandez à BRAIN et FLEET pourquoi ils ont accepté un score inférieur à leur option extérieure. La réponse est presque toujours « pour que ça marche » — c'est-à-dire une erreur de rationalité individuelle, très instructive |
| **Un étudiant refuse de jouer le jeu** (« je participe toujours ») | Rappelez-lui que le classement individuel compte, et qu'il est en train de perdre |
| **Une équipe finit très en avance** | Demandez-leur d'écrire ce qu'ils feraient si un partenaire doublait ses exigences |
| **Un étudiant arrive en retard** | Il rejoint jusqu'au lancement du round 1. Après, faites-en un observateur affecté à un îlot, ou ajoutez-le en binôme depuis l'onglet Joueurs |
| **Un téléphone tombe en panne** | Binôme immédiat avec un voisin de la même équipe ; le siège se partage sans difficulté |
| **Le débat déborde sur le temps** | Sacrifiez le mini-débrief du round 2, jamais le débrief final |
| **Il reste moins de 12 minutes pour le débrief** | Faites les étapes 1 à 5 et l'étape 13. Le reste est un bonus |

## 16. Les erreurs d'animation à éviter

1. **Expliquer le round 1 avant le round 2.** L'échec doit rester une énigme
   pendant dix minutes. Si vous donnez la réponse, le round 2 devient un
   exercice d'application au lieu d'une découverte.
2. **Annoncer le choc, même à demi-mot.** « Choisissez bien, on ne sait jamais »
   suffit à ruiner le round 3.
3. **Confirmer les calculs des étudiants.** Vous deviendriez l'arbitre de
   l'information privée, qui est précisément ce qu'ils doivent gérer seuls.
4. **Ne récompenser que le meilleur écosystème.** Les étudiants coopèrent
   alors parfaitement dès le début et la tension disparaît.
5. **Traiter la modularité comme la bonne réponse.** Le barème dit le
   contraire, et les étudiants qui ont choisi propriétaire et gardé BRAIN ont
   le meilleur score collectif. C'est voulu.

---

# Partie V — Débrief (15 minutes)

Les treize planches sont dans l'onglet « Débrief » du tableau de bord.
Progressez au tableau en parallèle : le schéma se construit sous leurs yeux.

## Étape 1 — Repartir de la proposition de valeur

Écrivez au tableau : **Navette autonome à la demande**.

> « Quelles activités étaient nécessaires pour produire effectivement cette
> proposition ? »

Faites émerger : relation client, réservation, paiement, production des
véhicules, conduite autonome, cartographie, recharge, maintenance, opérations,
supervision.

Écrivez : **ACTIVITIES**

## Étape 2 — Ajouter les acteurs

> « Qui contrôlait ces activités ? »

MOBI, AUTO, BRAIN, GRID, FLEET.

Écrivez : **ACTORS**

## Étape 3 — Positions

> « Les cinq entreprises occupaient-elles la même position ? »

Non. Certaines sont proches du client, certaines contrôlent un complément
critique, certaines possèdent l'infrastructure, certaines orchestrent.

Écrivez : **POSITIONS**

## Étape 4 — Links

Dessinez les dépendances : AUTO ↔ BRAIN, AUTO ↔ GRID, BRAIN ↔ MOBI,
FLEET ↔ AUTO, FLEET ↔ MOBI.

> « Le système ressemblait-il vraiment à une chaîne linéaire
> fournisseur → entreprise → client ? »

Non.

Écrivez : **LINKS**, puis entourez l'ensemble :

> **Activities + Actors + Positions + Links**

C'est le point d'entrée vers Adner, *ecosystem as structure*.

## Étape 5 — La question centrale du round 1

> « Pourquoi le premier écosystème échouait-il alors qu'il était
> collectivement rentable ? »

Montrez le calcul : `40 − 21 − 13 = 6` points de surplus disponibles. Le
problème n'était pas l'absence de valeur, mais sa distribution.

Écrivez :

> **Collective Value ≠ Individual Incentives**
>
> **Participation ≠ Alignment**

La présence d'un acteur théoriquement nécessaire ne signifie pas qu'il
acceptera d'occuper la position qui lui est proposée.

## Étape 6 — Orchestration

> « Quel était réellement le travail de MOBI ? »

Pas de commander. MOBI devait identifier les acteurs nécessaires, comprendre
leurs dépendances, négocier leur participation, redistribuer suffisamment de
valeur, coordonner les investissements, concevoir des règles acceptables.

Écrivez : **Orchestration ≠ Hierarchy**

## Étape 7 — Création et capture de valeur

Comparez deux acteurs réels de la séance. FLEET est indispensable à la
création de valeur et capture souvent très peu ; MOBI capture une large part.

> « Un acteur important techniquement reçoit-il nécessairement beaucoup de
> valeur ? »

Non.

> « Un acteur peut-il capturer tellement de valeur qu'il détruit l'écosystème
> dont il dépend ? »

Oui — et vous en avez probablement vu un exemple au round 1.

Écrivez : **Value Creation ≠ Value Capture**

## Étape 8 — Jacobides : complémentarités

> « Pourquoi ne pouviez-vous pas simplement acheter chaque élément
> indépendamment ? »

Parce que la valeur dépendait de la compatibilité entre les investissements.
Le véhicule doit être compatible avec l'IA, les stations, l'opérateur, les
systèmes de MOBI. La valeur d'un élément dépend de la présence et de la
configuration des autres.

## Étape 9 — Jacobides : modularité

> « Qu'avez-vous réellement acheté avec les 6 points du standard ? »

Pas des clients. Pas des véhicules. Ils ont acheté de la substituabilité, de
la flexibilité, une réduction des coûts de coordination futurs, des
interfaces, et la capacité à modifier la composition de l'écosystème.

Écrivez :

> **Modularity → Reduced Specificity → Greater Substitutability**

## Étape 10 — Le standard redistribue le pouvoir

> « Que devient le pouvoir de BRAIN si BRAIN peut être remplacé facilement ? »

Il diminue. Appuyez-vous sur les chiffres de la séance : comparez ce que BRAIN
a obtenu dans un écosystème propriétaire et dans un écosystème modulaire.

La modularité ne modifie donc pas seulement des coûts techniques. Elle modifie
le bargaining power, la dépendance, la capture de valeur et les possibilités
stratégiques. **C'est le message central du jeu.**

Insistez sur le fait que la modularité n'est pas gratuite : elle coûte 6
points et 6 points de performance. C'est une assurance, avec une prime.

## Étape 11 — Ce n'est pas une supply chain

Une supply chain stylisée : `A → B → C → Client`.

Un écosystème : plusieurs activités interdépendantes coordonnées autour d'une
même proposition de valeur, avec des dépendances multilatérales, et sans
entreprise disposant d'une autorité complète sur les autres.

## Étape 12 — Ce n'est pas nécessairement une plateforme

> « Avions-nous besoin d'un marché à deux faces ou d'une plateforme numérique
> pour avoir un écosystème ? »

Non. L'écosystème existe parce qu'une proposition de valeur dépend de
l'alignement d'acteurs indépendants et complémentaires. Une plateforme n'est
qu'une architecture possible parmi d'autres.

## Étape 13 — Conclusion

> « La stratégie d'écosystème commence là où la performance de ma propre
> organisation ne suffit plus à déterminer si ma proposition de valeur sera
> effectivement produite. »

Écrivez :

> **Success = Strategy + Partners + Alignment + Architecture**

## Ce que vous devez entendre avant de partir

Si un étudiant formule spontanément l'une de ces trois idées, l'objectif est
atteint :

- « on avait tout, sauf une raison pour eux d'accepter » ;
- « je ne pouvais pas leur donner d'ordre, je pouvais seulement leur donner
  une part » ;
- « notre architecture nous a rendus dépendants ».

---

# Annexes

## A. Fiches de rôle

Distribuées automatiquement par la plateforme. Reproduites ici pour
information et pour la version papier.

### Vous êtes MOBI — orchestrateur

Vous contrôlez l'application, le paiement, la marque et la relation client.
Votre entreprise a imaginé le service. Mais vous ne contrôlez aucune des
quatre autres entreprises.

**Coût d'investissement : 3 — Option extérieure : 0**

Objectif : maximisez votre score individuel. Vous êtes également responsable
de déposer les accords collectifs de votre équipe.

> Être « orchestrateur » ne signifie pas que les autres joueurs doivent vous
> obéir.

### Vous êtes AUTO — constructeur automobile

Vous produisez les véhicules. Votre usine doit réaliser des adaptations
spécifiques au projet. Si vous refusez le projet, vous pouvez utiliser vos
capacités sur une autre commande.

**Coût d'investissement : 5 — Option extérieure : 3**

Objectif : maximisez votre score individuel.

### Vous êtes BRAIN — fournisseur d'IA

Vous fournissez l'IA de conduite et la cartographie. Votre technologie est
demandée par plusieurs marchés.

**Coût d'investissement : 4 — Option extérieure : 4**

Objectif : maximisez votre score individuel. Vous pouvez révéler ou non la
valeur de votre option extérieure.

### Vous êtes GRID — infrastructure

Vous gérez l'infrastructure de recharge et de maintenance. L'adaptation au
projet nécessite des investissements spécifiques.

**Coût d'investissement : 4 — Option extérieure : 2**

Objectif : maximisez votre score individuel.

### Vous êtes FLEET — opérateur

Vous êtes responsable des opérations quotidiennes. Sans vous, aucun véhicule
ne peut être exploité commercialement.

**Coût d'investissement : 5 — Option extérieure : 4**

Objectif : maximisez votre score individuel.

> Votre position est moins visible technologiquement que celles de MOBI ou
> BRAIN. Cela ne signifie pas qu'elle est moins importante.

## B. Toutes les valeurs numériques

| Paramètre | Valeur |
| --------- | -----: |
| Ressources par acteur et par round | 10 |
| Valeur du service, rounds 1 et 2 | 40 |
| Somme des coûts d'investissement | 21 |
| Somme des options extérieures | 13 |
| Surplus théorique disponible | 6 |
| Somme des seuils de participation | 34 |
| Surplus négociable au round 2 | 6 |
| Valeur du service — architecture propriétaire | 46 |
| Valeur du service — architecture modulaire | 40 |
| Coût collectif du standard | 6 |
| Mise en conformité de BRAIN | 6 |
| Remplacement — coût d'intégration, propriétaire | 8 |
| Remplacement — coût d'intégration, modulaire | 2 |
| Remplacement — retard, propriétaire | −12 |
| Remplacement — retard, modulaire | 0 |
| Revenu minimal exigé par ALT-AI | 8 |
| Coût d'investissement d'ALT-AI | 4 |

### Deux règles que la version d'origine laissait ouvertes

**Le prix d'ALT-AI.** Le concept initial introduisait ALT-AI sans lui donner
de prix. Il reçoit la même structure que BRAIN — coût 4, option extérieure 4 —
donc un revenu minimal de 8, annoncé publiquement dans la carte de choc. En
dessous, il refuse et l'écosystème échoue. Ses 4 points de coût entrent dans
la valeur collective, ce qui produit exactement les résultats attendus : 5 en
propriétaire, 11 en modulaire.

**L'absence de réponse.** Un étudiant qui ne vote pas est traité comme OUT :
il n'a rien investi. Annoncez-le clairement avant le premier vote.

## C. Version papier

Si la plateforme est indisponible, le jeu fonctionne intégralement sur papier.

**Matériel** : 4 exemplaires de la fiche « proposition de valeur », 4 × 5
fiches de rôle (annexe A), 4 contrats de round 2, 4 feuilles d'architecture,
4 cartes de choc, 20 feuilles individuelles de score, 1 feuille de score
enseignant, des stylos, un chronomètre visible. Aucun jeton n'est nécessaire :
les points s'écrivent.

**Feuille individuelle**

Nom : \_\_\_\_\_\_ Écosystème : \_\_\_\_\_\_ Rôle : \_\_\_\_\_\_

| Round | Ressources | Coûts | Revenus / option extérieure | Score |
| ----- | ---------: | ----: | --------------------------: | ----: |
| 1 | 10 | | | |
| 2 | 10 | | | |
| 3 | 10 | | | |
| **Total** | | | | |

**Tableau à projeter après chaque round**

| Écosystème | Acteurs JOIN | Service lancé ? | Valeur collective |
| ---------- | -----------: | --------------- | ----------------: |
| BLUE | | | |
| GREEN | | | |
| RED | | | |
| YELLOW | | | |

## D. Variantes

À réserver à une deuxième utilisation du jeu, quand vous maîtrisez le
déroulé de base.

**Incertitude sur les coûts (round 2).** Les coûts deviennent aléatoires. Par
exemple, FLEET tire son coût dans `{3, 5, 7}` et seul FLEET connaît la valeur.
L'orchestrateur doit alors construire l'écosystème sans connaître même
l'ordre de grandeur des contraintes de ses complémenteurs.

**Écosystèmes concurrents (après le round 2).** BRAIN et AUTO peuvent recevoir
une offre d'un autre écosystème et changer de camp. Cela introduit le
multi-homing, la concurrence entre écosystèmes, la guerre pour les
complémenteurs et le pouvoir des acteurs rares. Très riche, mais difficile à
tenir dans 60 minutes.

## E. Ce que la plateforme calcule à votre place

- l'attribution des rôles et l'équilibrage des équipes selon l'effectif ;
- l'information privée : chacun ne voit que ses propres chiffres ;
- la validation des contrats (`Σ R = 40`, contributions, seuil d'ALT-AI) ;
- tous les scores individuels et collectifs, à chaque round ;
- les deux classements finaux ;
- le chronomètre, les rappels d'animation et les planches de débrief.

Installation, connexion et dépannage : [README.md](README.md).
