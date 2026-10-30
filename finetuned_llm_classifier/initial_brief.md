# Brief Projet : Fine-Tuning d'un Modèle de Classification de Requêtes Client (Néobanque B2B)

## 1. Contexte et Objectif
Ce projet s'inscrit dans la mise en place d'un copilote d'assistance aux agents de support pour une néobanque B2B (visant à réduire le temps de traitement des tickets de 10,5 min à 2 min). 
L'objectif est de réaliser un **fine-tuning** d'un petit LLM (via Vertex AI) pour automatiser la première étape du pipeline : la classification structurée et l'extraction d'intentions à partir des messages clients bruts (e-mails, tickets).

## 2. Le Rôle du LLM Fine-Tuné dans le Flow (Avant / Après)

Le modèle fine-tuné n'écrit pas de texte libre : il agit comme un extracteur de données déterministe qui prend une entrée brute et renvoie **toujours un objet JSON strict** basé sur une taxonomie fermée.

### Le Pipeline Complet :
1. **Avant (Entrée) :** Réception d'un message client brut (ex: réclamation sur un virement, bug technique API, contestation de frais, ou message ambigu/hors-périmètre).
2. **Le LLM Fine-Tuné (Classification & Extraction) :** Le modèle analyse le message et produit un JSON standardisé avec des clés fixes (`intent`, `sub_intent`, `transaction_id`, `amount`, `currency`, `urgency`, `sentiment`).
3. **Le Filet de Sécurité (Standardisation de l'ambiguïté) :** 
   * Pour toute catégorie ou champ textuel indéterminable ou ambigu, le modèle est entraîné à répondre explicitement **`"UNDEFINED"`**.
   * Pour les champs numériques ou optionnels absents, le modèle renvoie systématiquement **`null`**.
4. **Après (Routage via Arbre de Décision) :** 
   * Si le JSON est valide et pleinement qualifié : le système automatise le matching avec le Core Banking ou l'application des règles de conformité.
   * Si le JSON contient des `"UNDEFINED"` ou des champs de repli : un arbre de décision logique dans le code détecte l'ambiguïté et route immédiatement la requête vers une file d'attente pour une qualification manuelle par un agent humain.


## 3. Exemples d'Entrées / Sorties (Dataset d'Entraînement)

### Exemple 1 : Réclamation sur un virement SEPA
* **Input (Message client) :**
  > « Bonjour, le virement SEPA de 12 500 € initié lundi dernier (ref: TX-994821) n'est toujours pas crédité sur le compte de notre fournisseur. C'est urgent, notre chaîne logistique est bloquée. »

* **Output (JSON strict attendu) :**
```json
  {
    "intent": "echec_virement_sepa",
    "sub_intent": "retard_credit",
    "transaction_id": "TX-994821",
    "amount": "12500.00",
    "currency": "EUR",
    "urgency": "haute",
    "sentiment": "irrite"
  }

```

### Exemple 2 : Problème technique d'API / Webhook

* **Input (Message client) :**
> « Salut team technique, nos webhooks de notification de paiement ne répondent plus depuis ce matin 9h. On reçoit des erreurs 502 Gateway Timeout sur notre endpoint `/v1/webhooks`. Pouvez-vous jeter un œil ? »


* **Output (JSON strict attendu) :**
```json
{
  "intent": "erreur_technique_api",
  "sub_intent": "webhook_down",
  "transaction_id": null,
  "amount": null,
  "currency": null,
  "urgency": "haute",
  "sentiment": "neutre"
}

```

### Exemple 3 : Contestation de frais / Fraude

* **Input (Message client) :**
> « Bonjour, nous constatons des frais de prélèvement de 45 € sur notre relevé du 14 octobre que nous n'avons jamais autorisés. Nous demandons l'annulation immédiate de ces frais. »


* **Output (JSON strict attendu) :**
```json
{
  "intent": "contestation_frais",
  "sub_intent": "frais_non_autorises",
  "transaction_id": null,
  "amount": "45.00",
  "currency": "EUR",
  "urgency": "moyenne",
  "sentiment": "negatif"
}

```

### Exemple 4 : Message ambigu ou non classifiable (Cas de repli / Fallback)

* **Input (Message client) :**
> « Coucou c'est pour savoir si vous gérez les cryptos ou si on peut changer la couleur de l'interface parce que mon stagiaire trouve ça moche. »


* **Output (JSON strict attendu - Standardisation stricte via `"UNDEFINED"` et `null`) :**
```json
{
  "intent": "UNDEFINED",
  "sub_intent": "UNDEFINED",
  "transaction_id": null,
  "amount": null,
  "currency": null,
  "urgency": "basse",
  "sentiment": "UNDEFINED"
}

```