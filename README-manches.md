> Archive du fonctionnement à manches. Le guide courant de la campagne narrative est [README.md](README.md). Les mentions de refonte non implémentée ci-dessous décrivent l’état historique de cette archive.

# ECOSYSTEM — préparer et animer une séance

Un jeu de négociation sur les écosystèmes d’entreprises : cinq acteurs indépendants doivent lancer un service de navettes autonomes. Chaque joueur maximise son score ; la réussite du service exige leur coopération. L’enseignant prépare la partie dans une application de bureau, puis conduit la séance depuis un tableau de bord web projeté. Les étudiants jouent sur téléphone.

**Format conseillé : 60 minutes, 10 à 30 étudiants, un ordinateur et un vidéoprojecteur.** Un rôle peut être partagé en binôme. Le serveur fonctionne avec Python 3.10 ou plus récent, sans paquet à installer. Les règles économiques détaillées et les références de cours sont dans [concept.md](concept.md).

La refonte proposée vers une campagne narrative cumulative est décrite dans [architecture-narrative.md](architecture-narrative.md), avec [son arbre de décision](docs/arbre-narratif.mmd) et le dispositif de données pour le débrief. Le présent guide décrit la version jouable actuelle à manches ; le nouveau moteur n'est pas encore implémenté.

## Démarrer avec l’application de bureau

1. Ouvrez le dossier `Serious game` dans l’Explorateur Windows et double-cliquez sur **[ouvrir-interface.bat](ouvrir-interface.bat)**. La fenêtre s’intitule **« ecosystem · Votre séance »**.
2. Pour répéter seul, choisissez **Ce PC uniquement (répétition)**, **2** écosystèmes, le port **8000**, la clé **repetition** et le dossier **donnees-repetition**.
3. Sélectionnez **Créer une nouvelle partie** pour un premier essai, puis cliquez sur **Démarrer le serveur**. Pour retrouver une partie existante, choisissez **Reprendre la dernière partie sauvegardée** avec le même dossier.
4. Attendez l’affichage du code, puis cliquez sur **Ouvrir le tableau de bord**. Le bouton **Tester** ouvre l’écran étudiant dans le navigateur.
5. À la fin, cliquez sur **Arrêter et sauvegarder**. Gardez l’application ouverte pendant la séance.

Pour le cours, choisissez **Réseau local (Wi-Fi commun)** ou **Adresse publique (tunnel)** selon le réseau disponible. Pour 20 étudiants, prévoyez **4** écosystèmes et un dossier distinct, par exemple **donnees-seance**.

| Interface | Commandes disponibles |
| --- | --- |
| Application de bureau | Paramètres de connexion, équipes, port, clé, sauvegardes, démarrage et arrêt du serveur |
| Tableau enseignant | QR, phases, chronomètre, retrait d’étudiants, demande de nom et prénom, résultats et débrief |
| Écran étudiant | Inscription avec prénom et nom, fiche privée, négociation et vote |

Le conducteur de 60 minutes est en **section 4** ; la répétition avec les scores attendus est en **section 6**.

## Ce qui change dans cette version

- Le téléphone garde trois rubriques pendant toute la partie : **La situation** (contexte et accord en cours), **Mon entreprise** (dossier privé et actions spéciales), **La table** (partenaires et annonces publiques). Une nouvelle phase ouvre la situation ; les mises à jour conservent l’onglet choisi et les saisies en cours.
- Le contexte est celui de Métropole en 2032 : cinq entreprises cherchent à lancer des navettes autonomes. Chaque étape apporte un fait nouveau et un enjeu, sans donner une méthode de négociation ni conseiller une décision.
- Les informations arrivent avec les événements. Les participants ne voient plus la frise des étapes futures. Les pouvoirs apparaissent à leur première phase d’utilisation ; le marché, le choc et les badges ne sont pas révélés en avance. L’API participant filtre également ces données, y compris dans une sauvegarde reprise et lors d’un retour à une phase antérieure.
- Le dossier privé donne les ressources, le coût et le revenu hors du projet. Les seuils de rentabilité et la comparaison automatique des scores JOIN / OUT ont été retirés : les joueurs font leur calcul et choisissent ce qu’ils révèlent. Les règles de score restent consultables. Le choix d’architecture expose le revenu, le coût initial et les différences d’interfaces ; les coûts d’un incident précis arrivent après son annonce.
- Le design participant garde une esthétique futuriste : bleu nuit, trame de terminal, accents cyan et vert, typographie géométrique et surfaces droites. La répartition des revenus tient sur une ligne de cinq colonnes ; les détails secondaires se déplient à la demande. Aucune police ni image distante n’est nécessaire.
- À la première connexion, un briefing animé d’environ 27 secondes présente Métropole en 2032, les cinq entreprises et l’objectif du jeu. Le rôle du participant est mis en évidence. Les commandes permettent de mettre en pause, avancer, revenir ou passer ; **Brief** permet de revoir la séquence à tout moment. Elle ne redémarre pas après une actualisation une fois terminée ou passée. Les préférences de réduction des animations activent une lecture manuelle. Les manches et les événements futurs restent inconnus.
- Une application de bureau permet de démarrer, reprendre et arrêter le serveur sans PowerShell. Les réglages sont mémorisés et l’arrêt écrit une sauvegarde.
- Deux commandes du tableau enseignant permettent de **Retirer un étudiant** et de **Demander nom et prénom** aux personnes déjà connectées. Les deux champs sont aussi obligatoires à l’inscription.
- Un vrai tour de table numérique : en manche 1, chaque acteur peut se dire « Favorable » ou « Réservé » sur l’offre imposée, sans demander une autre part. À partir de la manche 2, il peut annoncer « Prêt à signer » ou « À renégocier » sur le contrat publié. Ce sont des intentions publiques dans son équipe, pas des votes.
- Les propositions sont numérotées et conservées dans un historique. Toute nouvelle publication efface les intentions précédentes : on se prononce sur la nouvelle version.
- Le projecteur montre les accords publiés et le nombre de partenaires prêts, sans révéler leurs intentions individuelles. Les votes JOIN / OUT restent secrets jusqu’aux résultats, y compris dans la réponse de l’API enseignant.
- Les contrats des rounds 2 et 3 sont figés pendant le vote après une première publication. Un dépôt initial tardif reste possible pour débloquer une équipe sans contrat.
- Le tableau enseignant conserve la frise complète, les missions d’animation et le suivi de progression.
- Le journal technique de l’application est replié derrière **Détails de connexion** et s’ouvre automatiquement si le serveur s’arrête avec une erreur.

Aperçus : [accueil sur téléphone](docs/accueil-mobile.png), [briefing : contexte](docs/intro-contexte-mobile.png), [les cinq rôles](docs/intro-roles-mobile.png), [objectif](docs/intro-objectif-mobile.png), [négociation sur téléphone](docs/negociation-mobile.png), [dossier privé](docs/dossier-mobile.png), [table des partenaires](docs/table-mobile.png), [tableau enseignant](docs/tableau-enseignant.png), [gestion des étudiants](docs/gestion-etudiants.png).

## 1. Initialiser le jeu

### Régler la séance depuis le bureau

L’application utilise Tkinter, fourni avec l’installation Windows standard de Python. Aucun paquet supplémentaire n’est requis. Vous pouvez aussi ouvrir directement `interface.pyw` si les fichiers Python sont associés à Python sur votre PC.

| Paramètre | Réglage et effet |
| --- | --- |
| Connexion des étudiants | **Ce PC uniquement** pour une répétition sans téléphone ; **Réseau local** pour un Wi-Fi commun autorisant les échanges entre appareils ; **Adresse publique** pour ouvrir le tunnel et accepter les données mobiles |
| Nombre d’écosystèmes | De **2 à 6**, ou **Automatique**. Sur une nouvelle partie, l’automatisme adapte le nombre aux arrivées. Sur une reprise, il conserve le réglage enregistré ; sélectionner un nombre fixe réapplique ce nombre au démarrage |
| Port du serveur | **8000** par défaut. Si ce port est occupé, choisir par exemple **8080**, ou arrêter l’ancien serveur dans sa propre fenêtre |
| Clé enseignant | Une valeur comme **repetition** donne un lien facile à retrouver. Vide : conserver la clé d’une sauvegarde reprise, ou en générer une pour une nouvelle partie |
| Dossier des sauvegardes | **donnees-repetition** pour les essais, **donnees-seance** pour le cours. Les chemins relatifs partent de `Serious game` ; **Parcourir…** permet de choisir un autre dossier |
| Adresse IPv4 locale | Facultative ; sert à forcer l’adresse affichée si le PC possède plusieurs interfaces réseau. Le mode **Ce PC uniquement** garde toujours des liens locaux |
| Au démarrage | **Reprendre la dernière partie sauvegardée** charge la sauvegarde la plus récente du dossier. Sans sauvegarde, une première partie est créée. **Créer une nouvelle partie** génère un nouveau code et conserve les anciens fichiers |

Après **Démarrer le serveur**, les paramètres sont mémorisés dans `.interface.json` et deviennent non modifiables jusqu’à l’arrêt. Le mode « nouvelle partie » n’est pas mémorisé : après un arrêt, l’option **Reprendre** est sélectionnée automatiquement.

Le bouton **Ouvrir le tableau de bord** ouvre le pilotage de la séance. **Copier le lien étudiant** copie l’adresse à partager ; le QR se trouve dans le tableau de bord. **Ouvrir le dossier des sauvegardes** affiche les fichiers de la séance. **Lire le guide d’animation (README)** ouvre ce document.

La zone centrale défile sur les petits écrans ou avec un zoom élevé ; les boutons de démarrage et d’arrêt restent en bas de la fenêtre. **Détails de connexion** affiche le journal et **Masquer les détails** le replie. Si le tunnel échoue, l’application indique que seule la connexion locale est disponible.

À la fin, cliquez sur **Arrêter et sauvegarder**. Fermer la fenêtre pendant une partie propose aussi un arrêt propre. L’application ne prend pas le contrôle d’un serveur déjà ouvert dans PowerShell : arrêtez celui-ci avec `Ctrl+C`, puis choisissez son dossier de sauvegarde et **Reprendre** dans l’application.

### Démarrage manuel dans PowerShell

Dans l’Explorateur Windows, ouvrez `Serious game`, cliquez dans la barre d’adresse, tapez `powershell`, puis appuyez sur **Entrée**. Pour vérifier que vous êtes dans le bon dossier :

```powershell
Test-Path .\serveur.py
```

Le résultat doit être `True`. Si PowerShell est déjà ouvert dans le dossier parent, entrez d’abord :

```powershell
cd '.\Serious game'
python --version
```

Si `python` est introuvable, essayez `py -3` à sa place dans les commandes suivantes.

### Première répétition, sur votre ordinateur uniquement

```powershell
python serveur.py --host 127.0.0.1 --port 8000 --cle repetition --equipes 2 --nouvelle --donnees donnees-repetition
```

1. Ouvrez le tableau enseignant : `http://127.0.0.1:8000/hote?cle=repetition`.
2. Relevez le code de quatre lettres dans le bandeau ou la console.
3. Ouvrez `http://127.0.0.1:8000/?c=CODE` dans un **autre profil de navigateur** ou une fenêtre privée ; remplacez `CODE` par le vrai code.
4. Saisissez votre prénom et votre nom de famille dans les deux champs obligatoires. Repérez votre équipe et votre rôle sur votre fiche.
5. Pour créer plusieurs joueurs sur le même PC, utilisez des contextes de navigateur séparés : les onglets d’un même profil partagent la session stockée. Plusieurs fenêtres privées peuvent aussi partager le même contexte. Pour dix joueurs, préférez dix profils ou plusieurs appareils.
6. Les sièges vides sont joués automatiquement à la clôture du vote. Deux joueurs suffisent pour explorer les commandes, mais la négociation complète se répète mieux avec cinq personnes par équipe.

Le dossier `donnees-repetition` isole cette répétition des vraies séances. Gardez le terminal ouvert ; `Ctrl+C` arrête le serveur et sauvegarde la partie.

### Jour J, réseau local

```powershell
python serveur.py --port 8000 --equipes 4 --nouvelle --donnees donnees-seance
```

Pour 20 étudiants, quatre équipes de cinq. Sans `--equipes`, le nombre d’équipes s’ajuste aux arrivées, entre deux et six. La console affiche le lien enseignant avec sa clé et le lien étudiant avec son code. Sur le PC enseignant, vous pouvez toujours utiliser `http://127.0.0.1:8000/hote?cle=VOTRE_CLE`.

Les étudiants doivent être sur le même réseau que le PC et ce réseau doit autoriser les connexions entre appareils. Projetez le QR du tableau enseignant ; il contient déjà le code de partie. Autorisez Python sur le réseau privé si Windows le demande.

### Jour J, étudiants en 4G ou Wi-Fi isolé

```powershell
python serveur.py --tunnel --equipes 4 --nouvelle --donnees donnees-seance
```

Ou double-cliquez sur `lancer-tunnel.bat`. L’exécutable `cloudflared.exe` fourni ouvre une adresse publique temporaire. Le PC doit avoir accès à Internet. Ouvrez le lien enseignant **local** affiché par la console ; le QR pointe vers l’adresse publique du tunnel. Testez ce QR avec votre téléphone en données mobiles avant l’arrivée des étudiants. Le tunnel et son adresse cessent de fonctionner à l’arrêt du processus.

L’option `--cle` rend la clé enseignant fixe. Sans cette option, elle est générée : utilisez le lien exact de la console. Gardez cette clé pour vous, elle permet de piloter toute la partie.

### Reprendre après une interruption

```powershell
python serveur.py --port 8000 --donnees donnees-seance
```

Reprenez avec **le même dossier et sans `--nouvelle`** : le serveur charge sa sauvegarde la plus récente. N’ajoutez `--equipes` que si vous souhaitez réellement changer l’organisation. Si vous utilisiez un tunnel, ajoutez `--tunnel` : sa nouvelle adresse impose de rescanner le QR et de rejoindre depuis cette adresse.

## 2. Installer la salle — checklist de cinq minutes

- [ ] Une table par écosystème, nommée BLUE, GREEN, RED, YELLOW ; les partenaires d’une même équipe peuvent discuter de vive voix.
- [ ] PC branché, application de bureau ou terminal laissé ouvert, mise en veille désactivée pendant la séance.
- [ ] Vidéoprojecteur sur le tableau enseignant, pas sur les fiches privées des étudiants.
- [ ] QR essayé depuis un vrai téléphone sur le réseau qui sera utilisé.
- [ ] Chaque étudiant connaît son équipe et lit son coût, son option extérieure et son pouvoir.
- [ ] Onglet « Joueurs & réglages » vérifié : un MOBI humain par équipe, pas de siège vide inattendu. Réattribuez les rôles avant le lancement.
- [ ] Compte à rebours essayé : espace pour démarrer / mettre en pause, bouton +1 min pour prolonger.

**Ne lancez pas le round 1 pendant que les étudiants arrivent** : leurs rôles peuvent encore être rééquilibrés. Les binômes partagent un siège, donc une décision et un score. Pour un binôme, faites choisir un porte-parole avant le premier vote.

### Gérer les étudiants

Deux boutons se trouvent sous le bandeau du tableau enseignant :

- **Retirer un étudiant** ouvre « Joueurs & réglages » sur la liste. Cliquez sur **Retirer** à côté de la personne et confirmez. Sa session est déconnectée et son téléphone revient à l’inscription. Si elle occupait seule son siège, celui-ci devient automatique ; ses demandes, intentions et votes non clôturés sont effacés. Un partenaire de binôme conserve la décision commune. Les résultats des rounds déjà calculés restent inchangés. Une nouvelle inscription reste possible tant que les inscriptions sont ouvertes : le retrait n’est pas un bannissement.
- **Demander nom et prénom** affiche un formulaire chez tous les étudiants déjà connectés. Ils doivent compléter les deux champs pour continuer à jouer ; leur rôle, leur équipe et leurs votes restent conservés. La liste indique les identités encore à compléter. Une ancienne sauvegarde sans identité complète déclenche aussi ce formulaire lors de la reprise.

Les nouveaux inscrits remplissent leur prénom et leur nom dès l’accueil. Le nom complet apparaît dans les équipes et les classements. Pour charger une mise à jour, utilisez la procédure de la section 8.

## 3. Brief oral — à lire en deux minutes

> Vous représentez cinq entreprises qui veulent lancer un service de navettes autonomes. MOBI apporte la marque et la relation client, AUTO les véhicules, BRAIN l’IA, GRID l’infrastructure et FLEET les opérations. Aucun de vous ne peut livrer le service seul.
>
> Votre objectif individuel est de maximiser votre score. Chaque round commence avec 10 points de ressources. Si vous choisissez JOIN, vous investissez votre coût. Vous ne touchez le revenu promis que si tous les partenaires nécessaires participent. Si vous choisissez OUT, vous n’investissez pas et vous gagnez votre option extérieure. Une absence de réponse compte comme OUT.
>
> Vos coûts et vos options extérieures sont privés : vous pouvez les révéler, les cacher ou négocier sans les donner. MOBI publie les accords, mais ne peut imposer votre participation. Vos intentions pendant la négociation sont visibles dans votre équipe ; le vrai vote final reste secret. Nous comparerons le classement des entreprises et celui des écosystèmes.

Lisez ensuite la proposition de valeur affichée : réserver une navette en moins de dix minutes, avec un trajet fiable et un prix inférieur à celui d’un taxi. N’annoncez pas les chocs futurs ni les seuils des autres rôles.

## 4. Conduire la séance — 60 minutes

Les horaires ci-dessous partent du début de la séance. Ils comprennent les transitions et les discussions. **Suivant** ou la flèche droite change de phase ; **espace** démarre le chrono de la nouvelle phase. Le chrono ne démarre pas tout seul et son expiration ne ferme pas les votes. Le menu de phases sert surtout à la répétition ; pendant le cours, avancez dans l’ordre.

| Minutes | Écran / action enseignant | Consigne et critère pour avancer |
| --- | --- | --- |
| 00–06 | Accueil : projeter le QR, contrôler les sièges, lire le brief | « Retrouvez vos partenaires et lisez votre fiche. » Avancer quand chacun a un rôle. |
| 06–11 | R1 discussion : **Suivant**, puis **espace** | « La répartition est imposée. Pouvez-vous lancer le service ? » Laisser chacun réagir à l’offre et indiquer une intention. Les parts ne se renégocient pas. |
| 11–12 | R1 décision | « Votre intention n’était pas un vote. Choisissez maintenant JOIN ou OUT. » Attendre les réponses humaines ; les automates répondent à la clôture. |
| 12–15 | R1 résultats | « Qui manque ? Pourquoi une activité rentable peut-elle échouer ? » Deux réponses, sans révéler tous les seuils. |
| 15–23 | R2 négociation | « Les 40 points sont maintenant négociables. MOBI publie un contrat. » Première proposition, tour de table, révision, nouveau tour de table. |
| 23–24 | R2 décision | Faire relire la dernière version. Une intention favorable n’oblige pas à voter JOIN. |
| 24–27 | R2 résultats | « Qui a obtenu une meilleure part ? Quel acteur pouvait vraiment bloquer le lancement ? » |
| 27–30 | Marché | « MOBI peut faire une offre à un BRAIN concurrent. BRAIN peut accepter ou rester. » Révéler les transferts uniquement en quittant cette phase. |
| 30–33 | R3 architecture | « Choisissez avant de connaître la suite : revenu immédiat ou flexibilité ? » Vérifier qu’une architecture est déposée par chaque équipe. FLEET doit exercer son veto avant le dépôt. |
| 33–34 | Choc | Lire le choc révélé lentement, puis laisser quelques secondes. Ne pas conseiller de solution. |
| 34–39 | R3 sauvetage | « Sauvez le service, répartissez le coût, ou abandonnez. » Faire publier une solution et refaire le tour des intentions. |
| 39–40 | R3 décision | Relire le contrat de sauvetage, puis voter. Le partenaire remplacé n’a plus à voter ; le fournisseur de remplacement est automatique. |
| 40–43 | R3 résultats puis classements | Comparer les architectures et les deux classements. Demander un fait précis aux gagnants comme aux perdants. |
| 43–58 | Débrief | Utiliser les questions de la section 7 et les planches de l’onglet Débrief. |
| 58–60 | Conclusion | Faire écrire une décision à changer lors d’une prochaine partie, avec sa justification. |

Le panneau repliable « Conduite de la séance » rappelle les consignes par phase. Le tableau de progression permet de voir les accords déposés, les intentions favorables et les votes reçus. Les automates et les partenaires remplacés ne répondent pas sur téléphone : ne bloquez pas la séance en attendant cinq réponses humaines si l’équipe n’a pas cinq sièges humains actifs.

## 5. Faire vivre la négociation

Au round 2, imposez un rythme oral simple, sans ajouter de règle de score :

1. **Premières deux minutes :** chaque partenaire annonce une demande et une raison. MOBI écoute avant de publier.
2. **Minute 3 :** MOBI publie sa première proposition. Chaque acteur indique « Prêt à signer » ou « À renégocier » sur son écran.
3. **Minutes 4 à 6 :** donnez d’abord la parole aux acteurs qui demandent une renégociation. « Qu’est-ce qui vous ferait accepter ? Qu’offrez-vous en échange ? » MOBI publie une nouvelle version si nécessaire.
4. **Deux dernières minutes :** faire relire l’accord final et demander ce qui a changé. Les intentions sont remises à zéro à chaque publication. Tous les accords n’ont pas besoin d’obtenir cinq intentions favorables pour passer au vote : le désaccord fait partie du jeu.
5. **Vote :** rappeler que le contrat est désormais figé et que chacun doit vraiment choisir JOIN ou OUT.

En cas de silence : « Qui perd le plus si le projet échoue ? Qui a une alternative ? » Si MOBI décide pour tout le monde : « Est-ce que les autres entreprises ont signé ? » Si un joueur bloque : « Quel accord rendrait votre participation préférable à votre autre activité ? » N’annoncez pas son seuil à sa place.

### Marché et pouvoirs — expliquer au bon moment

Seul BRAIN peut changer d’équipe. Une offre vaut de 1 à 5 points et est payée par le MOBI recruteur ; partir coûte 2 points à BRAIN. Un seul BRAIN par équipe : les transferts aboutissent lorsqu’un siège est libéré dans un échange ou un cycle. Une acceptation isolée peut donc être annulée. Une exclusivité acceptée empêche le départ.

| Rôle | Pouvoir unique | Moment utile |
| --- | --- | --- |
| MOBI | Subvention de 1 à 3 points, pris sur son propre score | R1 ou R3, négociation ou décision |
| BRAIN | Propose 3 points supplémentaires contre l’exclusivité ; MOBI accepte ou refuse | R2 ou marché |
| AUTO | Multi-homing : +2 individuels, −2 au collectif | Marché |
| GRID | Réduit de 2 le coût d’adaptation d’une architecture modulaire | Sauvetage, avant le dépôt de la solution |
| FLEET | Veto sur l’architecture propriétaire | Choix d’architecture, avant le dépôt |

Les transferts des pouvoirs et du marché sont des ajustements ajoutés au classement final. Le calculateur du round décrit le contrat et ses coûts ; il ne réintègre pas ces ajustements de fin de partie. Les pouvoirs ne sont utilisables qu’une fois. Le standard et les coûts d’intégration engagés restent payés même si le projet échoue ou est abandonné.

## 6. Répétition guidée — résultats vérifiables

Cette section est **réservée à l’enseignant**. Ne projetez pas les seuils pendant la partie.

Utilisez le dossier `donnees-repetition`. Pour une démonstration complète à la main, réunissez dix joueurs de test, cinq par équipe. Si des sièges sont automatiques, ils acceptent lorsque le revenu couvre leur coût et leur option extérieure ; aucun signal préalable n’est envoyé par un automate.

### R1 : constater l’échec de l’alignement

La répartition MOBI / AUTO / BRAIN / GRID / FLEET vaut `14 / 10 / 6 / 6 / 4`. Faites voter OUT à FLEET et JOIN aux quatre autres, sans pouvoir activé.

Résultat attendu : service non lancé ; scores `7 / 5 / 6 / 6 / 14` ; valeur collective `−16`. BRAIN peut aussi refuser : il gagne 12 si tout le monde participe, contre 14 avec son option extérieure. FLEET gagne 9 en participant à un succès, contre 14 dehors.

### R2 : deux propositions et un accord

1. MOBI publie `8 / 8 / 8 / 8 / 8`, total 40 : c’est la version 1.
2. FLEET indique « À renégocier ». Vérifiez que l’équipe voit son intention et que le projecteur n’affiche que les nombres agrégés.
3. MOBI publie `6 / 9 / 9 / 6 / 10`, total 40 : version 2. Les intentions précédentes disparaissent ; la version 1 reste dans l’historique.
4. Faites voter JOIN aux cinq acteurs pendant la phase de décision.

Résultat attendu sans pouvoirs : scores `13 / 14 / 15 / 12 / 15` ; valeur collective `19`. GRID est exactement indifférent à son option extérieure. Les seuils privés valent `3 / 8 / 8 / 6 / 9`, soit 34 ; les six points restants font l’objet du partage du surplus.

### Marché : une permutation facultative

MOBI BLUE offre 4 au BRAIN GREEN ; MOBI GREEN offre 4 au BRAIN BLUE. Chaque BRAIN accepte l’offre reçue. Passez à l’architecture pour clôturer le marché : les deux changent d’équipe, les MOBI perdent chacun 4 en ajustement et chaque BRAIN gagne `4 − 2 = 2`. Pour une répétition simple, faites rester tout le monde.

### R3 : comparer deux architectures face au même choc

À l’étape architecture, BLUE publie MODULAR et les contributions au standard `2 / 1 / 1 / 1 / 1`, total 6. GREEN publie PROPRIETARY, sans contribution. Passez au choc, puis utilisez **Imposer AI FAILURE** pour rendre cette répétition reproductible. Au sauvetage :

- BLUE remplace BRAIN. Revenus : MOBI 9, AUTO 9, GRID 6, FLEET 8, ALT-AI 8, total 40. Intégration : MOBI 2, les autres 0. Sans STANDARD READY, c’est exactement le coût requis. Faites voter JOIN aux quatre acteurs restants.
- GREEN garde BRAIN. Revenus `6 / 9 / 14 / 6 / 11`, total 46 ; aucune contribution d’intégration. BRAIN supporte ses 6 points d’adaptation. Faites voter JOIN aux cinq acteurs.

Valeurs collectives attendues : BLUE `11`, GREEN `19`. Scores BLUE, dans l’ordre des cinq rôles : `12 / 13 / 13 / 11 / 12` ; BRAIN a pris son option extérieure après avoir payé sa part du standard. Scores GREEN : `13 / 14 / 14 / 12 / 16`. Le propriétaire fait mieux ici ; d’autres chocs favorisent le modulaire. Ne présentez pas la modularité comme une réponse universelle.

Pour vérifier les autres chocs sans refaire toute la répétition, lancez les tests de la section 9.

## 7. Débrief en quinze minutes

| Durée | Question | Notion à faire émerger |
| --- | --- | --- |
| 3 min | « Au R1, pourquoi la valeur potentielle n’a-t-elle pas suffi ? Citez le partenaire manquant. » | Complémentarités et alignement des incitations |
| 3 min | « Comparez la première et la dernière version du contrat R2. Qui a fait bouger quoi ? » | Orchestration sans autorité, création et capture de valeur |
| 2 min | « Une intention favorable a-t-elle été suivie d’un vote différent ? Pourquoi ? » | Incertitude, confiance, engagement et information privée |
| 2 min | « L’offre d’une autre équipe a-t-elle changé le pouvoir de BRAIN avant même un transfert ? » | Option extérieure et dépendance |
| 3 min | « Qu’avez-vous payé avec le standard ? Que seriez-vous devenus sous une autre architecture ? » | Spécificité, substituabilité, verrouillage et résilience |
| 2 min | « La meilleure entreprise appartient-elle au meilleur écosystème ? » | Tension entre performance individuelle et collective |

Pour finir, demander une phrase écrite : « Au prochain tour, je changerais … parce que … ». Les badges décrivent des phénomènes observés ; ils n’ajoutent aucun point. Les planches de l’onglet Débrief développent les liens avec le cours.

## 8. Dépannage et commandes utiles

### Charger une mise à jour sans perdre la partie

1. Repérez le dossier de sauvegarde de la partie en cours.
2. Cliquez sur **Arrêter et sauvegarder**, puis fermez et rouvrez l’application avec `ouvrir-interface.bat`. Pour un serveur lancé dans PowerShell, utilisez `Ctrl+C`.
3. Choisissez **le même dossier** et **Reprendre la dernière partie sauvegardée**, puis démarrez le serveur. En ligne de commande, conservez le même `--donnees` et retirez `--nouvelle`.
4. Sur le tableau enseignant, appuyez sur **Ctrl+F5** pour recharger le design et les scripts. Actualisez aussi les téléphones. Si un tunnel a été relancé, faites rescanner le nouveau QR.

### Résoudre un problème

| Problème | Action concrète |
| --- | --- |
| La fenêtre de bureau ne s’ouvre pas | Depuis PowerShell dans `Serious game`, lancer `python interface.pyw` pour voir l’erreur. `python -m tkinter` permet de vérifier que Tkinter est disponible. |
| Le démarrage échoue depuis l’application | Ouvrir **Détails de connexion** et lire le journal ; vérifier le port et le dossier choisis. |
| L’ancien design s’affiche encore | Fermer et rouvrir l’application, puis actualiser le navigateur avec **Ctrl+F5**. Utiliser la procédure de reprise ci-dessus si une partie est en cours. |
| Le téléphone ne charge pas le jeu | Essayer le QR depuis les données mobiles si le tunnel est actif. En local, vérifier le réseau commun et le pare-feu. Un Wi-Fi universitaire peut isoler ses appareils ; utiliser alors `--tunnel`. |
| Mauvaise adresse réseau | Relancer avec `--ip 192.168.1.42`, en remplaçant par l’IPv4 du PC. |
| Port déjà occupé | Utiliser `--port 8080` et les liens correspondants. |
| Le chrono ne démarre pas | Appuyer sur espace hors d’un champ de saisie, ou sur le bouton lecture. Chaque nouvelle phase est initialement en pause. |
| L’équipe n’a pas de contrat | Revenir en négociation pour en publier un ; un premier dépôt tardif est également possible pendant le vote. R2 sans contrat produit un échec sans investissement. |
| Le contrat est erroné pendant le vote | Revenir à la négociation, publier la correction, rouvrir le vote. La nouvelle publication efface les votes précédents ; tout le monde doit revoter. |
| Un joueur est remplacé au R3 | Il prend son option extérieure ; il n’a plus de vote à envoyer. Les coûts déjà engagés restent payés. |
| Connexion perdue | Garder l’onglet ouvert : il retente la connexion. Recharger si nécessaire ; sur la même adresse et le même navigateur, la session est retrouvée. |
| Une démonstration a pollué le classement | Arrêter la répétition et démarrer une nouvelle partie dans un autre dossier. Ne pas utiliser « Rejouer » pour effacer tous les effets historiques. |

**Rejouer un round** efface son contrat, ses votes, ses intentions, son historique et ses résultats ; au R3, l’architecture et le choc sont conservés. Les pouvoirs déjà consommés, les ajustements du marché et les autres rounds restent en place : utilisez une nouvelle partie pour une remise à zéro complète. « Précédent » seul ne rouvre pas un round déjà calculé.

| Option | Utilité |
| --- | --- |
| `--port 8080` | Choisit le port du serveur ; 8000 est utilisé par défaut |
| `--tunnel` | Ouvre une adresse publique temporaire via `cloudflared` |
| `--ip 192.168.1.42` | Force l’adresse IPv4 locale affichée aux étudiants |
| `--nouvelle` | Crée une nouvelle partie et un nouveau code, sans supprimer les anciennes sauvegardes |
| `--donnees dossier` | Isole les fichiers de la séance ; indispensable pour distinguer répétition et cours |
| `--equipes 4` | Fixe le nombre d’équipes |
| `--cle votre-cle` | Fixe la clé d’accès enseignant |
| `--host 127.0.0.1` | Écoute uniquement sur le PC local |
| `--public https://votre-adresse` | Utilise un tunnel déjà ouvert ailleurs |

Les sauvegardes JSON sont écrites automatiquement environ 1,5 seconde après une modification, et lors d’un arrêt propre par **Arrêter et sauvegarder** ou `Ctrl+C`. Les anciennes sauvegardes sont complétées au chargement avec les nouveaux champs d’intentions et d’historique. Les étudiants dont l’identité est incomplète doivent saisir leur prénom et leur nom.

## 9. Vérifier et modifier

Depuis `Serious game` :

```powershell
python tests/test_scores.py
python tests/test_places.py
python tests/test_partie.py
python tests/test_extensions.py
python tests/test_negociation.py
python tests/test_etudiants.py
python tests/test_desktop.py
python tests/test_participants.py
```

Les tests vérifient respectivement les scores, les effectifs, une séance HTTP à 20 joueurs, le marché/chocs/pouvoirs, et les révisions/intentions/confidentialité/reprises. Aucun paquet de test n’est requis. Le test HTTP utilise temporairement le port 8099 et son propre dossier de données.

`test_etudiants.py` vérifie l’inscription avec prénom et nom, les demandes d’identité, le retrait d’un étudiant, les binômes et la reprise d’anciennes sauvegardes. `test_desktop.py` lance de vrais serveurs dans des dossiers temporaires sur des ports libres : paramètres, conflit de port, arrêt authentifié avec sauvegarde immédiate, reprise et nouvelle partie. Les tests utilisent leurs propres données.

`test_participants.py` vérifie la révélation progressive des informations, les chiffres privés sans seuil calculé, l’arrivée des pouvoirs et le masquage des données futures lors d’une reprise. Pour un contrôle visuel facultatif, `python tests/verifier_parcours.py` utilise Playwright s’il est installé : cinq rôles, quinze phases, trois rubriques, saisies, intentions, votes, publications et captures mobiles. Ce script démarre son propre serveur sur un port libre et ne touche pas aux données du cours. Playwright n’est pas requis pour jouer ni pour les tests précédents.

```text
serveur.py               Serveur HTTP, API et démarrage
ouvrir-interface.bat     Ouvre l’application de bureau sous Windows
interface.pyw            Point d’entrée de la fenêtre Tkinter
lancer.bat               Démarrage Windows en réseau local
lancer-tunnel.bat        Démarrage Windows avec tunnel public
concept.md               Intentions pédagogiques et barèmes d’origine
README.md                Installation et conducteur de séance
 eco/rules.py            Rôles, constantes, pouvoirs et phases
 eco/engine.py           Machine de jeu, révisions, intentions et scores
 eco/desktop.py          Fenêtre de bureau, paramètres et contrôle du serveur
 eco/store.py            Sauvegarde JSON atomique
 eco/qr.py               QR local, sans service externe
 web/joueur.html|js      Interface téléphone
 web/intro.js            Briefing animé local, navigation et mémorisation
 web/hote.html|js        Tableau enseignant
 web/session.js          Utilitaires partagés, frise et missions enseignant
 web/style.css           Style commun, responsive et impression
 web/participant.css     Terminal de jeu mobile, briefing et surfaces droites
 web/mark.svg            Identité visuelle et icône du jeu
 tests/                  Vérifications sans dépendance
 donnees/                Sauvegardes par défaut
.interface.json          Paramètres du bureau, créé au premier lancement du serveur depuis l’application
```

Le jeu n’appelle aucun modèle d’IA : tout le calcul est local et déterministe, sauf le tirage du choc et la distribution des rôles. En mode local, aucune connexion Internet n’est nécessaire pendant la partie. En mode tunnel, le PC et les téléphones doivent pouvoir accéder à Internet.
