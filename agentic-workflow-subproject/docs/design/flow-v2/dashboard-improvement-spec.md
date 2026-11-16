# Amélioration du dashboard et du flow interactif

## Intention et périmètre

Faire évoluer le front Keelpay existant, sans le reconstruire : un outil de travail sobre, actuel et dense mais lisible, inspiré de la clarté de GCP, Gmail et Databricks. Le dashboard est la première page de l'agent : en quelques secondes il doit comprendre ce qui circule, ce qui attend une personne, ce qui est urgent ou en erreur, puis ouvrir la bonne file. La carte du flow est la partie expressive et animée de l'interface ; le reste demeure calme.

Cette spécification est un plan d'action, pas une implémentation. Préserver les fonctionnalités, routes et données existantes, ainsi que les modifications présentes dans le dépôt. Les exemples de textes sont à adapter à la langue actuelle de l'interface ; conserver une langue cohérente dans toute l'application.

## État actuel constaté dans le code

- `frontend/src/App.tsx` contient le shell, le dashboard, les métriques, les files et l'injection de tickets. Le dashboard interroge l'overview toutes les 8 secondes.
- `frontend/src/FlowGraph.tsx` dessine le flow en SVG (viewBox 1980 × 700). Les nœuds re-routing, validation et erreurs sont déjà des liens vers leurs files. Deux points suivent actuellement un seul chemin lorsque `processing > 0`.
- `frontend/src/styles.css` impose au graphe une largeur minimale de 1260 px ; le conteneur peut donc défiler horizontalement. Les nœuds SVG ont actuellement un rayon de 3 unités ; l'ensemble et les cartes inférieures occupent une hauteur importante.
- `OverviewData` fournit notamment les volumes par statut et file, le total, l'âge du plus ancien ticket ouvert et les envois simulés. `TicketSnapshot` expose une priorité et un nœud courant, mais l'overview ne donne ni décompte des urgences par file ni positions individuelles dans le flow. Les files sont paginées : compter seulement la première page serait trompeur.
- Ces observations sont issues du code, sans audit visuel du rendu ni garantie que toutes les données soient disponibles en temps réel.

## Résultat attendu sur un écran standard

Cible initiale vérifiable : viewport navigateur **1366 × 768 CSS px**, zoom 100 %, navigation ouverte et formulaire de démonstration fermé. Le dashboard complet par défaut — titre compact, indicateurs prioritaires, flow lisible, accès aux files et informations essentielles — tient dans le viewport **sans défilement vertical de page ni défilement horizontal du flow**. Valider aussi à 1440 × 900 et 1920 × 1080. Le viewport CSS est la zone disponible dans le navigateur, pas la résolution physique de l'écran.

Ne pas atteindre cet objectif en réduisant tout le SVG à une taille illisible ou en masquant des informations importantes. Viser du texte courant autour de 13–14 px, ne pas descendre sous 12 px pour les informations utiles, et maintenir des cibles interactives confortables. Si la place manque, simplifier la représentation par défaut : regrouper les détails techniques dans des sections développables, garder les points de décision humains visibles, et réorganiser le graphe. Une vue détaillée optionnelle peut exposer toutes les étapes et défiler ; elle ne doit pas être nécessaire pour comprendre la situation et agir.

À plus petite largeur ou hauteur, à fort zoom ou avec de longs libellés, autoriser une mise en page adaptative et le défilement plutôt que couper le contenu. Les menus et panneaux volontairement ouverts peuvent dépasser le viewport et défiler. Ne pas bloquer le scroll global par un `overflow: hidden` qui rendrait du contenu inaccessible.

## Organisation proposée

1. **En-tête et navigation** : conserver le shell et les deux destinations existantes. Réduire les hauteurs et marges excessives ; état de connexion discret mais identifiable.
2. **Bandeau de synthèse** : garder les informations directement utiles : reçus, en traitement, en attente d'un agent, plus ancienne attente, erreurs et envois simulés selon l'espace disponible. Éviter de multiplier les grandes cartes ; regrouper les chiffres secondaires dans une ligne compacte. Utiliser les libellés précis : l'âge actuel est calculé depuis la création, pas nécessairement depuis l'entrée dans la file.
3. **Flow principal** : centre visuel de la page, organisé de gauche à droite autour de la réception, qualification/routage, préparation, contrôle humain et issue. Montrer clairement les branches humaines et erreurs, et la direction. Garder les étapes techniques existantes accessibles via détails ou regroupements si nécessaire, sans suggérer qu'elles ont disparu du processus. La carte peut être redessinée dans les mêmes composants et non remplacée par un nouveau produit.
4. **Accès aux actions** : présenter sur les nœuds humains leur nombre et un libellé explicite (« Ouvrir la file » / équivalent). Les erreurs ont également un accès direct. Une courte synthèse des files peut accompagner le graphe si elle tient sans dupliquer inutilement les informations.
5. **Informations secondaires** : distribution par statut, ratio humain et formulaire d'injection restent disponibles dans des sections compactes repliées ou un panneau secondaire. Garder visible l'essentiel sans ouverture. Ne pas supprimer ces fonctionnalités. Le footer ne doit pas imposer un scroll au dashboard à la taille cible.

## Direction visuelle

- Fonds clairs légèrement différenciés, texte foncé, bordures fines et ombres rares. Éviter les grands dégradés, effets lumineux permanents, cartes flottantes excessives et animations décoratives sur toute la page.
- Rayons modérés et cohérents : point de départ 6–8 px pour cartes et nœuds, 4–6 px pour contrôles ; ajuster à l'échelle réelle du SVG. Hiérarchie fondée sur le contenu, l'alignement et l'espacement plutôt que sur de gros encadrements.
- Bleu discret pour l'activité et les liens ; ambre pour une intervention humaine ou une attente ; rouge pour erreur et urgence avérée ; vert sobre pour une issue réussie ou simulée. Une file non vide n'est pas automatiquement une erreur. Toujours compléter la couleur par du texte ou une icône.
- Distinguer clairement les éléments cliquables : curseur, survol, focus clavier visible et libellé d'action ; aucun faux bouton. États vides calmes et explicites.

## Animation du flow

Donner l'impression de tickets qui circulent : petits marqueurs lisibles, évoquant des tickets plutôt que de simples points, qui suivent les connexions et franchissent les étapes dans le bon sens. Animations fluides, espacées, de vitesse modérée, sans flash ni clignotement. Les branches et étapes humaines peuvent montrer une accumulation visuelle discrète lorsqu'une file contient du travail ; le compteur chiffré reste la source de vérité. L'animation ne doit jamais masquer un libellé ni gêner les clics.

**Fidélité des données :** l'overview actuel ne fournit qu'un nombre global `processing`, pas le parcours ni la position en direct de chaque ticket. Dans une première version, animer une activité représentative uniquement lorsque l'activité correspondante est connue ; annoncer discrètement qu'il s'agit d'une visualisation indicative. Ne pas attribuer d'identifiant, de priorité, de trajet individuel ou de nombre de marqueurs précis à des tickets réels sans données correspondantes. À zéro activité, arrêter la circulation et afficher un état calme. En cas de données périmées ou d'API indisponible, ne pas continuer à présenter une activité comme actuelle.

Une animation réellement synchronisée ticket par ticket est une évolution séparée, dépendante d'un contrat d'événements ou d'états par étape, avec ordre, horodatage, reprise et traitement des événements manquants ; ne pas la simuler comme si elle existait.

Respecter `prefers-reduced-motion` : arrêter les déplacements et pulsations, conserver les compteurs, couleurs, libellés et accès. Ne pas communiquer une urgence uniquement par une animation.

## Files, urgences et navigation

- Re-routing → `#workspace/re-routing`, validation → `#workspace/review`, erreurs → `#workspace/errors`. Conserver les liens existants et vérifier leur destination, y compris au clavier.
- Sur chaque nœud, afficher le nombre exact disponible, son état vide ou occupé et l'action. Une file qui grossit ne peut être qualifiée de « s'empile » que si une tendance ou un seuil fiable existe ; sinon afficher simplement son volume.
- Si une priorité urgente existe dans une file, afficher un badge et une incitation d'action clairs, par exemple « 3 en attente · 1 urgent ». L'ouverture de la file doit permettre de repérer le ticket urgent ; un tri ou filtre dédié est souhaitable si implémenté et clairement indiqué. Ne pas prétendre qu'un ticket particulier est sélectionné si ce n'est pas le cas.
- L'API overview actuelle ne fournit pas ces décomptes : prévoir un agrégat serveur par file et priorité, calculé sur l'ensemble des tickets concernés, avec définition explicite des valeurs de priorité et des statuts inclus. Définir un contrat compatible avec les clients existants. Tant que l'agrégat est indisponible, ne pas afficher « 0 urgent » ; afficher une information indisponible ou omettre le badge. Ne pas compter une seule page de file.
- Pour les erreurs, afficher le volume connu et un lien d'investigation. Éviter les alertes envahissantes ou répétitives ; distinguer priorité métier, erreur technique et simple attente.

## Chargement, actualisation et robustesse

Garder le rafraîchissement périodique existant comme base ; afficher le moment de la dernière actualisation réussie plutôt que garantir une fraîcheur fictive. Prévoir chargement initial, zéro ticket, absence de priorité, erreur API et données anciennes. En cas d'échec après succès, conserver les dernières valeurs si utile, les marquer comme périmées, arrêter l'animation qui prétend à une activité actuelle et proposer un rafraîchissement. Les erreurs ne doivent pas faire disparaître les accès déjà disponibles. Vérifier que les rafraîchissements ne provoquent pas de sauts de mise en page, de perte de focus ou de clignotement.

## Plan de réalisation

1. **Relevé visuel et données** : lancer la version actuelle, capturer la page aux tailles cibles, relever les débordements, vérifier les valeurs de priorité réellement utilisées et les contrats des files. Confirmer la sémantique des métriques et du flow avec le backend.
2. **Composition compacte** : réduire l'encombrement du shell et des métriques, hiérarchiser les informations, placer les détails secondaires en sections repliables. Adapter le graphe au viewport au lieu de simplement réduire son SVG. Conserver les fonctionnalités et routes.
3. **Raffinement visuel** : ajuster rayons, bordures, couleurs, typographie, espacements, états de survol et focus, de façon cohérente dans les composants existants.
4. **Flow et interactions** : revoir la géométrie et les connexions, rendre les files visibles et clairement cliquables, ajouter l'animation indicative et les états calme/périmé/mouvement réduit. Vérifier les branches et leur sens avec le flow réel.
5. **Urgences fiables** : définir et ajouter l'agrégat serveur, le typer dans `api.ts`, afficher les badges, puis rendre les tickets urgents repérables dans les files. Si le backend n'est pas prêt, livrer le reste sans faux chiffre d'urgence.
6. **Validation** : vérifier les critères ci-dessous, construire le frontend (`npm run build`) et exécuter les contrôles pertinents existants ; ajouter des tests ciblés là où une logique nouvelle de comptage, état ou navigation le justifie.

## Critères d'acceptation

- À 1366 × 768 CSS px et zoom 100 %, navigation ouverte et sections secondaires fermées, le dashboard utile est entièrement visible sans scroll vertical ni horizontal ; le flow et ses libellés restent lisibles. Vérification visuelle aussi à 1440 × 900 et 1920 × 1080.
- À plus petite taille ou zoom élevé, aucun contenu ni action n'est inaccessible ; le défilement est autorisé.
- Les files humaines et erreurs affichent leurs comptes connus et ouvrent la bonne page au clic et au clavier. Focus visible, noms accessibles et ordre de navigation logique.
- Un cas vide, un cas en traitement, une file humaine occupée, une erreur et une urgence réelle sont distinguables par texte et couleur. Les données manquantes ne sont pas présentées comme des zéros.
- Les marqueurs ne suggèrent pas une localisation ou un nombre de tickets réels sans source de données ; l'animation s'arrête en absence d'activité connue, en état périmé et en mode mouvement réduit.
- Les métriques conservent leur sens réel, les envois restent explicitement simulés et les détails secondaires ainsi que l'injection restent accessibles.
- Pas de régression des parcours de traitement existants ; construction et contrôles pertinents réussis. Vérifier également contraste, clavier, état hors ligne, actualisation et stabilité visuelle.
