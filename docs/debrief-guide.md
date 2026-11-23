# Lire les données au débrief

Les vues sont dans **Débrief & données**, après la clôture de décembre. Le groupe étudié peut être changé sans perdre la vue sélectionnée. **Mode projection** retire le QR, le chronomètre et les commandes de séance. Un clic ou la touche Entrée sur un point de trajectoire ouvre les faits du territoire et du trimestre correspondant.

## Cinq lectures complémentaires

| Vue | Donnée observée | Discussion possible |
| --- | --- | --- |
| Trajectoires | Valeur collective cumulée, recettes trimestrielles ou résultats cumulés des cinq entreprises | Quand les trajectoires divergent-elles ? Quelle situation héritée ou circonstance précède l'écart ? |
| Création de valeur | Recettes moins installation, adaptations, exploitation et fournisseur extérieur | Des investissements ont-ils permis de créer des recettes ? Les coûts irrécupérables ont-ils limité les réactions possibles ? |
| Entreprises | Recettes de transport, activité extérieure, coûts propres et résultat net | Qui crée et qui capte la valeur ? Une grande part du contrat compense-t-elle les coûts ? Une entreprise peut-elle gagner hors du projet ? |
| Contrats | Parts de recettes des accords effectivement signés, contributions, versions et dates | Qui obtient une concession, après quelle information ? Qui finance une capacité collective ? Un même partage peut-il devenir moins acceptable ? |
| Chocs et réactions | Faits marquants par trimestre, classés par nature et ordonnés par séquence | Le résultat est-il précédé d'un choc, d'un essai, d'un retrait ou d'un nouvel accord ? Quelles complémentarités ont arrêté ou permis le service ? |

Les questions affichées ouvrent une discussion ; elles n'attribuent pas une note théorique ou un diagnostic automatique aux joueurs. La chronologie présente une sélection de faits marquants ; le journal complet contient aussi les profils choisis, propositions et réponses individuelles.

## Les unités et les rapprochements

Les graphiques et leur CSV affichent des **crédits**. Les montants du ZIP métier sont en **centièmes de crédit**. Les parts des contrats sont des pourcentages des recettes réellement facturées, pas des pourcentages de bénéfice.

Les cinq résultats individuels excluent leurs dotations de départ. Un binôme représente une entreprise et un budget unique. Les comptes se rapprochent ainsi :

```text
Valeur collective du transport
  = recettes du transport
    − installation et engagements supplémentaires
    − adaptations et investissements collectifs
    − frais d'exploitation réellement débités
    − rémunération du substitut extérieur

Somme des résultats nets des cinq entreprises
  = valeur collective du transport + revenus extérieurs
```

Le substitut n'est pas une sixième entreprise étudiante. Sa rémunération est un coût pour le territoire, prélevé sur les recettes clients. Les parts distribuées aux cinq entreprises ne sont pas comptées une seconde fois comme coût collectif.

Un territoire sans flotte peut avoir une valeur collective de transport nulle et des résultats individuels positifs grâce aux activités extérieures. Un trimestre sans recettes ne signifie pas forcément un refus : il peut aussi résulter d'essais interrompus, d'un délai, d'un retrait ou d'une indisponibilité. Revenir aux faits avant d'interpréter la courbe.

## Comparer avec prudence

Les groupes peuvent recevoir des circonstances différentes et ne disposent pas nécessairement des mêmes possibilités héritées. Les familles d'événements compatibles et leurs probabilités effectives sont conservées dans le ZIP. La chronologie montre une succession, pas une preuve causale à elle seule. Les vues ne prétendent pas mesurer une résilience générale ou l'effet statistique d'une architecture à partir de quelques groupes.

Si une séance ancienne n'a connu aucun nouveau choc en octobre, le rapport n'en ajoute pas. Si un territoire n'a signé qu'un accord, une seule barre apparaît. Les anciennes sauvegardes narratives restent lisibles.

## Conserver le débrief

- **SVG** : graphique vectoriel autonome, utilisable dans des diapositives, avec fond sombre et titres inclus.
- **CSV de la vue** : chiffres et faits affichés, séparateur point-virgule, encodage UTF-8 compatible Excel.
- **Rapport HTML** : les cinq vues interactives, styles et données sont intégrés ; le fichier s'ouvre hors connexion dans un navigateur. Aucun nom de participant ou jeton n'y est inclus.
- **ZIP** : journal complet pour approfondir l'analyse, rapprocher les transactions et reconstruire les décisions.

Le rapport est un instantané de la séance. Le changement de territoire ou de graphique ne modifie pas la sauvegarde du jeu.
