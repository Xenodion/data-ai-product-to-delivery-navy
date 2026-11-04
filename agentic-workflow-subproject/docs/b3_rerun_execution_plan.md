# Plan d'exécution B3 — inférence, scoring, MLflow et notebooks

**Statut :** garde-fous locaux implémentés ; aucune commande Vertex de ce document n'a été exécutée. B3 est le modèle `Qwen/Qwen2.5-3B-Instruct` avec le prompt du projet, **sans LoRA et sans entraînement**. Ne lancer ni `training` ni `sweep` ni `compact` pour ce travail.

**But :** obtenir des prédictions B3 complètes sur `val` (293), `test_natural` (610) et `test_traps` (380), puis les comparer aux systèmes déjà évalués sur les mêmes tickets. `train` n'est pas un split d'évaluation et ne doit pas être inféré. Le `val` local historique existe ; un nouveau `val` est nécessaire si l'on veut une série de trois splits produite avec exactement la même révision et configuration que les nouveaux tests. Garder le `val` historique et le nouveau `val` comme deux runs distincts.

## 0. Règles à ne pas contourner

- Exécuter les commandes depuis `agentic-workflow-subproject/`. `scripts/pipeline_runner.py` exige maintenant un pipeline explicite et `--confirm-billable-run` ; pour cette campagne, toujours écrire explicitement `base`. `--smoke` et `max_rows > 0` ne produisent jamais un score final.
- Le pipeline `base` appelle `inference_component` sur un T4. Le code actuel charge la base en **4 bits NF4**, avec `bnb_4bit_compute_dtype=torch.float32`, `max_new_tokens=160` et `do_sample=False`. Ne pas annoncer B3 comme une inférence fp16. La comparaison historique doit mentionner toute différence de révision/configuration.
- `test_natural` et `test_traps` restent gelés. Fixer prompt, modèle, données, code et règles de scoring **avant** leur exécution. Aucun réglage à partir des erreurs test ; un seul score final par version figée. `test_traps` sert au diagnostic par famille, pas à choisir le champion sur une moyenne globale.
- Ne pas remplacer ni renommer les anciens exports/runs. Identifier les nouveaux résultats comme B3 avec une révision ou un identifiant de campagne distinct, et noter s'ils reproduisent ou non la configuration historique.
- L'inférence Vertex est facturée. Définir un plafond de coût et une condition d'arrêt avant soumission. La présence du fichier local `base_val_predictions.csv` ne prouve pas la disponibilité des sorties test dans GCS.

## 1. Préparation locale — aucune soumission cloud

1. Vérifier que Python 3.11 et `uv` fonctionnent dans l'environnement d'exécution et que `uv sync` installe les dépendances du sous-projet. Ne pas utiliser le Python 3.12 créé par erreur dans le workspace précédent : `pyproject.toml` exige `<3.12`.
2. Vérifier l'authentification Google, `GCP_PROJECT_ID`, `GCP_REGION` (historique : `europe-west2`) et `GCP_BUCKET_NAME=navy-team-llmops-bucket` dans `.env` local. Ne jamais afficher ni committer des secrets.
3. Relever le commit Git, l'état dirty, les hashes SHA-256 de `val.csv`, `test_natural.csv`, `test_traps.csv`, de `src/prompt.py`, du composant d'inférence et du template compilé. Vérifier que les fichiers du bucket `gs://navy-team-llmops-bucket/dataset/` correspondent **octet pour octet** aux splits locaux gelés. Si ce n'est pas démontré, stopper avant le run.
   - Commande locale PowerShell : `Get-FileHash data/dataset/val.csv,data/dataset/test_natural.csv,data/dataset/test_traps.csv -Algorithm SHA256`.
   - Relever les générations des objets GCS et comparer le SHA-256 de copies téléchargées dans un dossier temporaire, sans remplacer les CSV du dépôt. Un CRC32C GCS seul n'est pas un SHA-256 comparable. Le composant `data_transformation` lit aussi `train.csv` pour son contrat KFP, même si B3 ne l'utilise pas pour apprendre : vérifier sa présence et son hash, mais **ne pas lancer d'inférence sur train**.
4. Fixer le modèle et, si possible, sa révision Hugging Face/tokenizer, la version de l'image et des packages, le prompt, `max_rows=0`, `max_new_tokens=160`, génération déterministe, le prix T4 attendu et le plafond de coût. Le code actuel ne verrouille pas toutes ces révisions : ajouter leur capture/versionnement avant d'appeler le résultat « reproductible ». Si la révision historique de B3 reste inconnue, qualifier les nouveaux runs de **B3 nouvelle campagne**, pas de reproduction à l'identique.
5. Écrire une fiche de campagne locale avec les trois splits attendus, leurs effectifs/hashes, les identifiants de configuration et les règles de comparaison du `docs/scoring_protocol.md`. Ne modifier aucun seuil après lecture des tests.
   - Générer le manifeste local non destructif avec `uv run python scripts/prepare_b3_campaign.py b3-<date>-<id>`. Il inclut les hashes locaux et marque explicitement les vérifications GCS et le budget comme non approuvés tant qu'ils ne sont pas renseignés.

**Porte P1 :** données du bucket identiques aux fichiers gelés, configuration et budget consignés. Sinon aucun job.

## 2. Soumission contrôlée

Option : un smoke run sur `val` pour vérifier le pipeline ; le marquer `smoke`, **ne pas le scorer comme 293 tickets**. Ensuite soumettre trois jobs `base` complets, l'un après l'autre. La commande soumet immédiatement un job facturé :

```powershell
# Depuis agentic-workflow-subproject ; seulement après P1.
uv run python scripts/pipeline_runner.py base --test-file val.csv --confirm-billable-run
uv run python scripts/pipeline_runner.py base --test-file test_natural.csv --confirm-billable-run
uv run python scripts/pipeline_runner.py base --test-file test_traps.csv --confirm-billable-run
```

Pour chaque commande, attendre la fin et vérifier le résultat **avant de lancer la suivante**. Le script crée `logs/vertex_submissions/<tracking_id>.json` après soumission. Copier dans la fiche de campagne le `tracking_id`, le nom complet du job, le projet/région, les paramètres, le hash du template et le commit. Si la soumission réussit mais que le reçu local manque, retrouver le job par nom/heure dans Vertex avant toute relance ; ne jamais soumettre deux fois par réflexe.

**Porte P2, par split :** état Vertex `SUCCEEDED`, tâche `inference-component` terminée, `test_file` exact, `max_rows=0`, sortie `predictions` présente, aucun job T4 encore actif ou endpoint créé par erreur. En cas d'échec, garder logs et ID ; diagnostiquer avant une éventuelle relance avec un nouvel ID. Arrêter la campagne si le plafond de coût est atteint.

## 3. Récupération et validation des sorties

1. Depuis **Vertex Pipelines / ML Metadata**, relever l'URI de l'artefact `predictions` de la tâche d'inférence. Le dossier GCS seul ou le Registry ne prouvent pas le contenu. Télécharger uniquement les CSV de prédictions et les reçus/logs nécessaires ; aucun poids de modèle.
2. Stocker les fichiers bruts sous des noms incluant `b3`, split et identifiant de campagne dans `data/runs/`, sans écraser `base_val_predictions.csv`. Pour l'intégration aux cellules de comparaison du notebook 5, publier une copie de travail nommée `docs/results/b3_<split>_predictions.csv` uniquement si elle n'existe pas déjà ; conserver l'original versionné. Conserver URI GCS, génération/checksum objet, SHA-256 local, nombre de lignes et job source dans un manifeste. Les CSV Vertex comportent `user_input`, `reference`, `extracted_response`, `valid_json` ; ne publier que la version assainie dans MLflow.
3. Comparer **toutes** les lignes `user_input`, dans le même ordre, au split local ; exiger respectivement 293, 610, 380 lignes, aucune duplication, aucune troncature. Vérifier le contrat JSON et conserver les sorties invalides comme erreurs/abstentions, sans les corriger manuellement.
4. Exécuter le scorer une seule fois pour chaque export complet. Le scorer refuse maintenant les nombres de lignes incomplets ; `--allow-partial-diagnostic` est limité à un préfixe `val` et ne peut jamais créer un run MLflow. Commande type :

```powershell
uv run python scripts/score_predictions.py docs/results/b3_val_predictions.csv val
uv run python scripts/score_predictions.py docs/results/b3_test_natural_predictions.csv test_natural
uv run python scripts/score_predictions.py docs/results/b3_test_traps_predictions.csv test_traps
```

Le script de scoring accepte actuellement un préfixe de split pour les smoke runs : **la vérification manuelle de l'effectif complet est obligatoire avant le score final**. Un CSV invalide/partiel ne va ni dans le tableau final ni dans MLflow comme run final.

**Porte P3 :** trois exports complets, alignés et hashés ; provenance Vertex cohérente. Sinon afficher `absent` ou `invalide` pour le split concerné et continuer seulement avec les autres.

## 4. MLflow, lignée et Registry

1. Démarrer le serveur MLflow local configuré dans `docs/mlops_tracking.md`. Importer les résultats B3 avec `--mlflow --system-id B3 --model-id <révision vérifiée ou unknown> --tracking-origin vertex`, en conservant le nom du split. Ne pas utiliser `scripts/import_legacy_results.py` pour faire passer la nouvelle campagne pour l'export historique par défaut.
2. Créer/synchroniser un manifeste Vertex par job avec `scripts/sync_vertex_run.py` : job/tâche KFP, paramètres, dataset/prompt/modèle, URI + hash des prédictions, métriques et preuve de coût/latence. **Ajouter et vérifier** le lien explicite du run d'évaluation MLflow vers le job/tâche parent ; le script actuel crée des runs parent/enfant séparés et ne relie pas automatiquement un run créé par `score_predictions.py`. `sync_vertex_run.py` n'interroge pas le cloud et ne remplace pas l'inventaire Vertex.
3. Logger les métriques historiques du Qualifier et les métriques `router.*` sous des noms distincts. Joindre la matrice d'action et les prédictions assainies. Les coûts mesurés Vertex et les scénarios de coût doivent avoir des statuts différents.
4. **Ne pas enregistrer B3 au Vertex Model Registry simplement pour comparer ses prédictions.** Le Registry sert aux versions déployables choisies ; un run B3 rejeté reste traçable dans Pipelines/MLflow. Ne déplacer aucun alias de D-q4 lors de ce rattrapage.

**Porte P4 :** chaque split B3 a un run MLflow identifiable, relié au job et au bon hash ; `unknown` reste explicite lorsque la provenance historique manque. Aucun nouveau modèle Registry revendiqué sans opération de registration distincte.

## 5. Notebooks et décision

- Avant le rendu, figer les run IDs dans un manifeste de comparaison. `notebooks/_tracking.py` choisit actuellement le run le plus récent : adapter le chargement pour choisir explicitement la campagne B3 et ne pas mélanger `val` historique, nouvelle validation et tests nouveaux.
- Notebook 2 : montrer B2/B3/D sur **validation**, avec la validation de la campagne B3 retenue ; les graphiques sont générés par les cellules, avec comptes, dénominateurs et titres descriptifs.
- Notebook 5 : ajouter B3 uniquement si les exports `test_natural` et/ou `test_traps` passent P3. Refaire les graphiques comparatifs sur les mêmes tickets : erreurs silencieuses et intervalle apparié, urgents au mauvais desk en comptes, couverture/Re-router, matrice Router, coût/latence avec provenance. Si B3 manque sur un split, afficher explicitement `absent` sans barre à zéro.
- Garder le verdict D-q4 historique comme constat daté, puis écrire une **nouvelle lecture** après B3. Ne pas retoucher a posteriori les résultats publiés, les seuils ou les poids du score de sévérité.
- Comparer B3 à D selon la règle déjà fixée : erreurs silencieuses, sévérité, urgent mal routé, puis coût/latence. Montrer le nombre brut d'urgents et les limites des petits sous-groupes. Le seuil proposé de 0,1 % d'erreurs graves après flux complet ne s'applique pas aux erreurs du modèle seul.

**Fin :** les trois splits B3 sont tracés et reproductibles ou leur absence est documentée ; notebooks exécutés de haut en bas, figures visibles dans leurs cellules et exportées ; MLflow et Vertex/KFP se recoupent par identifiants immuables ; aucune dépense récurrente ou ressource GPU laissée active.

## État de départ vérifié

Le fichier `data/runs/base_val_predictions.csv` existe déjà (293 lignes validées historiquement). Les exports B3 test et les reçus Vertex ne sont pas dans le checkout. Le préfixe communiqué est `gs://navy-team-llmops-bucket/pipeline_root/158407666882/`. Avant tout nouveau run, regarder si les sorties récentes s'y trouvent ; un job déjà terminé ne doit pas être refait pour recréer des métadonnées. La présente session n'a pas d'accès GCS/Vertex, et le Python 3.11 visible via le launcher Windows ne peut pas démarrer (`Access is denied`) : aucune porte P1–P4 n'est déclarée franchie ici.
