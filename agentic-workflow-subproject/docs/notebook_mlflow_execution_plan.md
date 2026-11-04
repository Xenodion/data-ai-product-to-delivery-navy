# Plan d'exécution — notebooks, B3 et traçabilité ML

**Nature :** plan de travail du sous-projet Qualifier. Les règles produit restent dans `specs/004-routing-node/` et la gouvernance dans `governance.md`. Ce plan ne réinterprète pas les seuils historiques.

## Résultat attendu

Les cinq notebooks doivent raconter l'expérience dans l'ordre où elle a eu lieu : constitution des données → baselines → fine-tuning → quantification et coût → lecture finale du test. Chaque graphique est généré par une cellule de code du notebook, à partir d'un fichier ou d'un run identifié. Le titre nomme seulement l'objet et le split ; axes, unités, effectifs et légende suffisent à lire la figure. L'interprétation et le verdict sont dans une cellule Markdown **après** la figure. Pas d'image insérée comme substitut à une cellule exécutée.

La comparaison finale doit rendre visible le résultat remarquable **avec ses limites exactes** : D-q4 est un fichier GGUF d'environ **1,93 Go**, avec une **RAM d'inférence rapportée d'environ 2,4 Go** sur CPU. « Moins de 2 Go de RAM » n'est pas établi par les mesures conservées. Le benchmark actuel indique environ 6,4 s/ticket sur CPU en validation, mais le matériel et le split doivent toujours accompagner la valeur. Le modèle bat nettement B2 sur les erreurs silencieuses du test naturel (4/610 contre environ 207/610) ; il échoue encore au garde-fou modèle seul des urgents mal routés (1/167). Les coûts mensuels sont des scénarios, pas une facture de production.

## Ordre et figures par notebook

| Notebook | Question et progression | Figures indispensables |
|---|---|---|
| `01_dataset_build` | Quelles données ont été acceptées, et les tests représentent-ils la même population ? | Entonnoir génération→acceptation par split ; distribution des intents **en effectifs et en proportions** par split ; effectifs des familles de pièges, avec repère à 20. |
| `02_scoring_and_baselines` | Que mesure le protocole, et quel niveau les méthodes simples atteignent-elles avant D ? | B0/B1/B2 sur validation puis test naturel ; erreurs silencieuses avec intervalles ; urgents au mauvais desk en **comptes / 167** dans un panneau séparé ; couverture versus erreurs ; B3 uniquement sur `val` tant que ses sorties test ne sont pas vérifiées. |
| `03_finetuning_vertex` | Comment l'apprentissage s'est-il déroulé, puis que gagne D sur validation ? | Loss train et validation par step, checkpoint choisi ; score D versus B2/B3 sur les **mêmes 293 tickets** ; ventilation des erreurs par champ (intent, référence, urgence), avec sorties invalides explicites. Ne pas utiliser la loss comme verdict de sélection. |
| `04_compact_variants` | Que coûtent les variantes et que perd-on en comprimant ? | D/D-q8/D-q4/B2 sur validation : qualité, couverture et urgences ; latence médiane/p95 par matériel ; taille du fichier et RAM d'inférence sur axes distincts ; qualité versus coût mensuel estimé, provenance de l'hypothèse visible. |
| `05_final_evaluation` | Le choix tient-il sur les tests gelés ? | Comparaison de tous les modèles **ayant une sortie vérifiée pour ce split** ; erreurs silencieuses et urgents mal routés dans deux panneaux ; matrice d'action Router en comptes et par ligne ; urgences manquées ; pièges en comptes ; qualité test versus latence/coût avec mesures et estimations distinguées. |

Pour chaque figure : code reproductible, source/sha256 du split, nom du système, dénominateur, unité, matériel si pertinent et figure exportable en SVG/PNG vers MLflow. Éviter les longs commentaires dans la figure, les conclusions dans les titres, les étiquettes collées aux barres et les pourcentages sans effectif. Une matrice ne remplace pas les erreurs par références ; une sortie invalide et un Re-router doivent rester identifiables.

## Séquence de livraison

1. **Stabiliser les données et le rendu.** Vérifier les dépendances Python du projet, exécuter les notebooks de haut en bas dans un environnement propre, retirer les sorties historiques périmées, puis rendre et inspecter chaque figure. Conserver les anciens résultats dans leurs artefacts ; ne pas réentraîner pour refaire des images.
2. **Préserver le scoring historique.** Garder `src/scoring.py` et `docs/scoring_protocol.md` comme référence de la comparaison Qualifier. Ajouter la lecture Router comme vue dérivée des mêmes prédictions, avec métriques `router.*` séparées. Les scores de qualité post-déploiement exigent des labels revus ; les logs d'inférence seuls donnent des volumes, latences, échecs et corrections.
3. **Récupérer B3 sur Vertex Pipelines.** Inventorier en lecture seule les jobs, tâches, paramètres, sorties et checksums. `base_val_predictions.csv` existe déjà. Si les sorties `test_natural`/`test_traps` existent et que leur split/provenance sont vérifiables, les récupérer puis les scorer une seule fois. Sinon, refaire uniquement l'inférence B3 sur les splits manquants avec nouvelle identité de run et budget/teardown documentés. Ne jamais placer B3 sur un graphique test avec une valeur absente ou inférée.
4. **Consolider MLflow.** Importer les runs historiques comme `historical_import`, avec source et champs inconnus explicites ; logguer la loss train/val par step à partir du JSON conservé, les métriques du scorer et Router, les matrices, graphiques, prédictions assainies et manifestes. Un run d'évaluation est immuable et identifié par système + split + hash des prédictions + scorer/policy version ; un nouvel artefact ou une nouvelle définition exige une nouvelle révision traçable.
5. **Relier les outils.** Créer un manifeste de correspondance par version : `system_id`, révision du modèle et du prompt, hash dataset/split, hash scorer, run MLflow, ressource job Vertex Pipeline, exécution/tâche KFP, URI + génération/checksum des artefacts, ressource/version Vertex Model Registry quand elle existe. MLflow héberge les métriques et artefacts riches ; Vertex/KFP garde la lignée d'exécution ; le Registry référence la version déployable et des labels courts. Synchroniser de manière idempotente, puis relire chaque lien dans les deux sens. Un alias `champion` est un état mutable : enregistrer à chaque décision la version immuable visée.
6. **Rejouer la présentation finale.** Rafraîchir les cinq notebooks dans l'ordre, vérifier tableaux, figures et légendes, publier les figures comme artefacts des bons runs MLflow, et produire un tableau de couverture B0–B3/D/D-q8/D-q4 × split où chaque cellule indique `mesuré`, `absent` ou `historique à vérifier`.

## Critères de fin

- Les cinq notebooks s'exécutent de haut en bas et montrent leurs figures **dans leurs cellules**, sans image Markdown utilisée comme cache visuel.
- La narration respecte la chronologie : validation pour les choix, test gelé pour le constat ; aucun réglage après lecture du test.
- B3 est présent uniquement là où une sortie vérifiée existe ; une nouvelle inférence est clairement datée et identifiée.
- Les affirmations de taille, RAM, latence et coût correspondent à leur mesure ou portent explicitement la mention d'estimation.
- Chaque graphique final est relié au split et au run MLflow source ; chaque version enregistrée dans Vertex possède un lien vérifiable vers le run MLflow et le job Vertex/KFP ou un état `unknown` explicite.
- Aucun taux de précision/rappel production n'est dérivé des seules prédictions, et le seuil proposé de 0,1 % d'erreurs graves après le flux n'est pas appliqué aux 0,7 % d'erreurs silencieuses du modèle seul.

## État au moment de ce plan

Le code de tracking, les exports D, la loss historique, des figures SVG/PNG et le B3 validation existent. Les notebooks ont des cellules et des sorties hétérogènes ; les nouveaux graphiques ajoutés récemment ne sont pas tous rendus. L'inspection Vertex de B3 test, la synchronisation réelle des versions jusqu'au Registry et un rendu complet des notebooks restent à faire. La présence d'une fonction de synchronisation locale ne prouve pas qu'un run cloud ou un Registry a été mis à jour.
