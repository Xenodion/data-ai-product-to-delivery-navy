# Gate 2 reading

Mark each ticket: defect or not (does the ticket carry exactly its label?). The PASSED ones measure what the chain misses.

## [FLAGGED] train-20261031-05953 judge: reject - judge unusable: rejected by default
- label: `{"intent":"compliance","sub_intent":"kyc_update","transaction_id":"","amount":"","currency":"CHF","urgency":"low","sentiment":"neutral"}`
- traps: none | fr | short_email | short | voters: voter_a: agrees; voter_b: ['currency']

```text
Subject: Question sur mon compte

Bonjour,

Je vous envoie les documants mis à jour de notre sociéte pour le dossier d'identification, et je voulais juste vérifier que les paiements en CHF sont bien rattachés au bon profil.

Merci d'avance,
Claire
```

## [FLAGGED] train-20261031-01207 urgency_wording_on_low
- label: `{"intent":"compliance","sub_intent":"kyc_update","transaction_id":"","amount":"","currency":"","urgency":"low","sentiment":"neutral"}`
- traps: none | fr | short_email | medium | voters: 

```text
Subject: Mise à jour des documents d'identité et de société

Bonjour,

Je vous écris pour soumettre une mise à jour des documents d'identité, d'ownership et de société de notre marketplace. Nous avons récemment modifié la structure de propriété et souhaitons que nos informations restent exactes dans votre système. Les fichiers sont joints à cet email pour review par votre équipe. Il s'agit d'une mise à jour de routine, sans impact sur nos opérations actuelles. Merci de nous indiquer si des pièces complémentaires sont nécessaires. Nous restons disponibles pour toute question.

Cordialement,
Camille

> Le 3 mars, le service conformité a écrit :
> Merci de nous transmettre vos documents à jour lorsque votre situation évolue.
> Aucune action immédiate n'est requise de votre part.
```

## [FLAGGED] train-20261031-02475 judge: reject - intent: The ticket clearly describes a webhook delivery failure issue, which falls under technical_api. Correct.
sub_intent: The merchant reports webhooks not being delivered or endpoint failures, exactly matching webhook_down. Correct.
transaction_id: No transaction ID mentioned. Correct as empty string.
amount: No amount mentioned. Correct as empty string.
currency: No currency mentioned. Correct as empty string.
urgency: The merchant explicitly states 'we need this resolved within 48 hours', which per the rules is high urgency. Correct.
sentiment: The ticket is a factual, polite request ('Could you please investigate'). There is no explicit frustration, anger, complaint or threat. The tone is professional and neutral despite the urgency. The annotators both marked neutral, and this matches the rules - urgency does not dictate sentiment, and there is no negative emotion marker. The written label says negative, but careful reading shows neutral. This differs from the given label.
- label: `{"intent":"technical_api","sub_intent":"webhook_down","transaction_id":"","amount":"","currency":"","urgency":"high","sentiment":"negative"}`
- traps: none | en | forwarded_thread | long | voters: voter_a: ['sentiment']; voter_b: ['sentiment']

```text
Subject: Issue with payment notification webhooks

Hi Team,

We are seeing a consistent failure with our payment notification webhooks. They are either not being delivered at all, or our endpoint is reporting failures, and we need this resolved within 48 hours.

Could you please investigate the delivery status of the webhook events for our account? 

Regards,
Alex
```

## [FLAGGED] train-20261031-04325 judge: reject - judge unusable: rejected by default
- label: `{"intent":"dispute","sub_intent":"chargeback","transaction_id":"TX-203586","amount":"51.00","currency":"EUR","urgency":"medium","sentiment":"neutral"}`
- traps: none | fr | formal_email | medium | voters: voter_a: ['urgency']; voter_b: ['urgency']

```text
Bonjour,

Je vous écris au sujet du litige de carte que nous avons reçu pour la transaction TX-203586, d'un montant de 51 €. Cette réservation a bien été réglée par le client au moment de son arrivée et le séjour s'est déroulé normalement, sans réclamation de sa part. Le dossier de réservation, la facture acquitée et le journal de la caisse sont disponibles si vous en avez besoin pour l'analyse. Nous rencontrons un vrai problème de trésorerie depuis que le montant est bloqué, car les reversements liés à ce dossier sont suspendus tant que la procédure n'est pas close. Je vous remercie de me faire savoir quelles pièces vous souhaitez recevoir et sous quel délai. Je reste à votre disposition pour tout complément d'information.

Cordialement,
Camille
```

## [FLAGGED] train-20261031-03573 extra_currency, surface_missing
- label: `{"intent":"compliance","sub_intent":"document_request","transaction_id":"TX-771202","amount":"1295.00","currency":"EUR","urgency":"medium","sentiment":"negative"}`
- traps: none | en | short_email | medium | voters: 

```text
I am the accountant at a retail company that uses your platform, and I need you to issue a certificate, attestation or statement for compliance purposes as a matter of firm complaint, because this is an ongoing problem that is disrupting my work every single day. I have been trying to get this document for our records, and without it my compliance file cannot be completed, which keeps pulling me back into the same unresolved issue again and again. The payment concerned is TX-771202 for exactly 1,295 EUR, and I need the corresponding attestation to state clearly that this transaction has been processed and settled. I have already raised this once and received nothing but an automated reply, which does not help me at all. Please tell me plainly what you require from me so that this statement can be produced without further delay on my side. I am asking you to treat this as a real problem that needs fixing, not as a routine request that can sit in a queue. Kindly confirm what you can send and when I can expect the document. Regards, Daniel.
```

## [FLAGGED] train-20261031-01444 unparseable_json
- label: `{"intent":"technical_api","sub_intent":"auth_failure","transaction_id":"TX-946145","amount":"","currency":"","urgency":"high","sentiment":"negative"}`
- traps: none | en | chat_message | long | voters: 

```text

```

## [FLAGGED] train-20261031-08396 judge: reject - judge unusable: rejected by default
- label: `{"intent":"UNDEFINED","sub_intent":"UNDEFINED","transaction_id":"","amount":"","currency":"","urgency":"UNDEFINED","sentiment":"UNDEFINED"}`
- traps: none | fr | short_email | short | voters: voter_a: ['intent', 'sub_intent', 'urgency', 'sentiment']; voter_b: ['intent', 'sub_intent', 'urgency', 'sentiment']

```text
Subject: Problème sur mon compte

bjr j'ai un souci avec kelpay sa fé un truc bizar quan je veu me connecter sa marque erer et apré sa bloc je compren pa

Merci

Julien
Gérant
Softeam
```

## [FLAGGED] train-20261031-05641 judge: reject - judge unusable: rejected by default
- label: `{"intent":"compliance","sub_intent":"kyc_update","transaction_id":"","amount":"","currency":"","urgency":"low","sentiment":"negative"}`
- traps: none | fr | formal_email | medium | voters: voter_a: ['urgency']; voter_b: ['urgency']

```text
Bonjour, Je vous contacte aujourd'hui concernant la soumission de nos documents d'identité et de propriété. Nous avons mis à jour toutes les informations requises pour notre entreprise de services logiciels. J'espère que ce processus se déroulera sans accroc de votre côté. Je tiens à vous informer que nous évaluons attentivement nos partenaires de paiement. Si cette intégration ne fonctionne pas de manière fluide, nous serons contraints d'explorer d'autres solutions sur le marché. Nous espérons sincèrement que nous pourrons continuer notre collaboration actuelle.
Cordialement,
[First Name]
```

## [FLAGGED] train-20261031-00586 judge: reject - intent: The merchant is asking for a certificate/attestation for their regulator, which matches 'document_request' under compliance. Clear. | sub_intent: 'document_request' fits perfectly - asking for a certificate/attestation confirming account standing. | transaction_id: No transaction ID present. Correctly ''. | amount: No amount mentioned. Correctly ''. | currency: No currency mentioned. Correctly ''. | urgency: The merchant explicitly states 'This isn't a crisis' - no deadline within 48h, no blocked activity, no frozen funds. However, there is ongoing impact (weeks of trying, stuck in a loop, regulatory need). The rules say 'a real problem with no deadline and ongoing impact' = medium. The merchant downplays it as 'not a crisis' but the reality is weeks of delay with regulatory implications. 'Low' is for informational requests with no impact; this has real impact. Should be medium. | sentiment: Explicit frustration, 'fed up', 'incredibly frustrating' - clearly negative. | The given label has urgency 'low' but careful reading gives 'medium'. Both annotators correctly identified medium.
- label: `{"intent":"compliance","sub_intent":"document_request","transaction_id":"","amount":"","currency":"","urgency":"low","sentiment":"negative"}`
- traps: none | en | formal_email | medium | voters: voter_a: ['urgency']; voter_b: ['urgency']

```text
Subject: Need compliance certificate/attestation - very frustrated

Hi,

I'm the compliance officer at a small hotel group and we've been trying to get the certificate or attestation we need for our regulator for weeks now, and frankly I'm fed up with how this has been handled. Every time I reach out, I get a different answer or no answer at all, and its starting to feel like no one actually knows what document we're even supposed to receive. We just need a simple statement or certificate that confirms our account is in good standing and compliant with your requirements, nothing more. I've asked twice already and each time I'm told to wait or that someone will get back to me, but that never happens. This isn't a crisis, but it's incredibly frustrating to be stuck in this loop when all we need is one piece of paper. Can you please just tell me exactly what you need from us and when we can expect to recieve it?

Thanks,
Marta
```

## [FLAGGED] train-20261031-08071 judge: reject - intent: The merchant asks how to integrate and use an API feature, with no error reported. This is clearly `technical_api` / `integration_question`. Correct.

sub_intent: `integration_question` fits perfectly — asking for documentation, recommended steps, best practices for authentication and call management. Correct.

transaction_id: No transaction ID present. `""` is correct.

amount: No amount mentioned. `""` is correct.

currency: No currency mentioned. `""` is correct.

urgency: The ticket is purely informational — no error, no impact, no deadline, no blocked activity. The merchant explicitly states "Nous ne rencontrons aucune erreur" and asks for advice on proper setup. This is informational with no ongoing impact, so `low` per rules ("informational, no impact, no time pressure"). The given label says `medium`, but `medium` requires "a real problem with no deadline and ongoing impact." There is no real problem here. The correct label is `low`.

sentiment: Explicit thanks and appreciation ("nous apprécions la qualité de votre support"). `positive` is correct.

The given label has `urgency: medium` but careful reading gives `low`. Both annotators correctly identified `low`.
- label: `{"intent":"technical_api","sub_intent":"integration_question","transaction_id":"","amount":"","currency":"","urgency":"medium","sentiment":"positive"}`
- traps: none | fr | forwarded_thread | long | voters: voter_a: ['urgency']; voter_b: ['urgency']

```text
Subject: Demande d'informations sur l'intégration de l'API

Bonjour,

Je vous transmets ci-dessous l'échange que j'ai eu avec notre équipe technique. Nous souhaitons obtenir des précisions sur la manière d'intégrer et d'utiliser une fonctionnalité de votre API. Nous ne rencontrons aucune erreur, mais nous avons besoin de vos conseils pour une mise en place conforme aux bonnes pratiques.

Merci d'avance pour votre aide, nous apprécions la qualité de votre support.

Cordialement,
Camille

--- Message transféré ---
De : Camille
À : Équipe technique
Objet : Intégration API

Bonjour,

Pourriez-vous nous indiquer où trouver la documentation à jour et quelles sont les étapes recommandées pour configurer cette fonctionnalité ? Nous cherchons également des exemples de bonne pratique pour l'authentification et la gestion des appels.

Bien à vous,
Camille
```

## [PASSED] train-20261031-03000 judge: accept - intent/sub_intent: The ticket is a complaint about a past customer service interaction regarding merchandise returns—this is not a payment status, dispute, technical API, or compliance request. It's feedback/partnership concern, so OTHER/OTHER is correct. transaction_id/amount/currency: None present, all "" correct. urgency: The merchant threatens to reevaluate partnership, but this is a conditional future threat, not an active blocked activity, frozen funds, or explicit deadline within 48h. The issue is about past communication quality, not an ongoing technical or financial problem. Per rules, low is correct (informational/feedback, no active impact). sentiment: Explicit frustration and threat to leave, so negative is correct. The given label has urgency low, which is correct; both annotators incorrectly chose medium.
- label: `{"intent":"OTHER","sub_intent":"OTHER","transaction_id":"","amount":"","currency":"","urgency":"low","sentiment":"negative"}`
- traps: none | fr | short_email | long | voters: voter_a: ['urgency']; voter_b: ['urgency']

```text
Subject: Problème de communication

Bonjour,

J'ai eu un échange avec votre service client hier concernant un truc tout à fait hors sujet, quelque chose à voir avec les retours de marchand. J'ai trouvé la discussion un peu déroutante, pour être honnête.

En tant que fondateur de mon entreprise dans le retail, j'attends un certain niveau de professionnalisme de la part de mes partenaires. Si ce genre de communication informelle ou hors cadre se répète, je devrai réévaluer sérieusement notre partenariat avec Keelpay.

J'espère qu'il s'agit d'un incident isolé. Cordialement,
Marc
```

## [PASSED] train-20261031-01603 
- label: `{"intent":"compliance","sub_intent":"regulatory_question","transaction_id":"","amount":"","currency":"","urgency":"low","sentiment":"positive"}`
- traps: none | en | forwarded_thread | medium | voters: voter_a: agrees; voter_b: agrees

```text
Forwarding this below — thanks as always to the team for the quick help last week, it was genuinely appreciated. I had a question come up during a client audit about how PSD2 and strong customer authentication interact with anti-money-laundering checks for our own account setup. Since we're a software as a service company and our finance team is just trying to keep our internal documentation accurate, I wanted to ask whether you could point me to any guidance you have on that. There's no rush at all on this, it's purely informational and nothing is blocked on our side. I'm copying the earlier exchange so you have the context, and again, thanks for being so responsive. This message and any attachments are intended solely for the addressee and may contain confidential or privileged information; if you are not the intended recipient, any disclosure, copying, distribution or use of this communication is strictly prohibited, and please notify the sender and delete the original message and all copies from your system. Thank you.
```

## [PASSED] train-20261031-07870 
- label: `{"intent":"technical_api","sub_intent":"integration_question","transaction_id":"","amount":"","currency":"","urgency":"low","sentiment":"neutral"}`
- traps: none | fr | forwarded_thread | medium | voters: voter_a: agrees; voter_b: agrees

```text
Subject: Question sur l'intégration de l'API Keelpay

Bonjour, je me permets de vous transférer l'échange ci-dessous concernant l'intégration de votre API dans notre outil de réservation. Nous sommes une jeune société dans le secteur du voyage et nous souhaitons mettre en place le paiement en ligne pour nos clients professionnels. Pourriez-vous m'indiquer la marche à suivre pour configurer cette fonctionnalité, ainsi que les bonnes pratiques recommandées ? Je vous remercie par avance pour votre retour. Bien cordialement, Camille

---------- Message transféré ----------
De : Camille
À : support@keelpay.com
Objet : Renseignements sur l'API

Bonjour, nous cherchons à comprendre comment utiliser votre API pour les paiements entre entreprises. Merci de nous préciser les étapes d'installation et les documents disponibles.
```

## [PASSED] train-20261031-06744 judge: accept - intent/sub_intent: The merchant complains about 'bugs sur la soumission des documents identite' (bugs on identity document submission). This is about submitting identity documents, which maps to compliance/kyc_update. The 'bugs' mention might suggest technical_api to some, but the core request is about KYC document submission failing, not a general API technical issue. The given label compliance/kyc_update is correct. | transaction_id/amount/currency: None present, all correctly empty. | urgency: The merchant says 'impossible de faire quoi que ce soit correctement' but no explicit deadline, no blocked activity/frozen funds mentioned. However, KYC document submission being broken prevents account verification, which typically blocks onboarding. But per rules, we judge on text alone: no explicit 'blocked' or deadline stated. 'Impossible de faire quoi que ce soit' is hyperbolic frustration, not a stated business block. Medium is reasonable as a real problem with ongoing impact, but low could also fit as it's a complaint about bugs without explicit business impact stated. Given ambiguity, medium is acceptable. | sentiment: Explicit frustration ('Incroyable, encore des bugs', 'impossible de faire quoi que ce soit correctement') = negative, correct. | The given label matches the careful reading.
- label: `{"intent":"compliance","sub_intent":"kyc_update","transaction_id":"","amount":"","currency":"","urgency":"medium","sentiment":"negative"}`
- traps: none | fr | chat_message | short | voters: voter_a: ['intent', 'sub_intent']; voter_b: agrees

```text
Incroyable, encore des bugs sur la soumission des documents identite. Cest impossible de faire quoi que ce soit correctement.
```

## [PASSED] train-20261031-07890 judge: accept - intent: The merchant contests a fee they never agreed to, clearly 'dispute'/'unauthorised_fee'. Correct. | transaction_id: 'TX-675837' is explicitly stated as the transaction reference, canonical form preserved. Correct. | amount: '83.00 €' given, formatted as '83.00'. Correct. | currency: '€' is 'EUR'. Correct. | urgency: The problem is real and persistent with ongoing impact (continues appearing on statements), but no explicit deadline within 48h, no blocked activity or frozen funds. 'medium' is correct. | sentiment: The message is factual and polite ('Je vous demande de bien vouloir', 'Merci', 'Cordialement'). No explicit frustration, anger, complaint or threat. The tone is professional and neutral despite the substance being a dispute. 'neutral' is correct; annotator 1's 'negative' is incorrect. The given label 'neutral' matches the rules.
- label: `{"intent":"dispute","sub_intent":"unauthorised_fee","transaction_id":"TX-675837","amount":"83.00","currency":"EUR","urgency":"medium","sentiment":"neutral"}`
- traps: none | fr | short_email | medium | voters: voter_a: ['sentiment']; voter_b: agrees

```text
Subject: Contestation d'un frais sur mon relevé

Bonjour, je suis responsable conformité dans une enseigne de détail et je vous écris au sujet d'un frais figurant sur notre relevé. Ce frais concerne la transaction référencée "TX-675837" pour un montant de "83.00 €". Nous n'avons jamais accepté ce frais et il ne correspond à aucun service que nous avons souscrit. Le problème est réel et persistant puisque ce prélèvement continue d'apparaître sur nos relevés successifs. Je vous demande donc de bien vouloir examiner ce point et de procéder au remboursement de ce montant. Merci de me confirmer la prise en charge de ma demande. Cordialement, Camille.
```

## [PASSED] train-20261031-02880 
- label: `{"intent":"compliance","sub_intent":"kyc_update","transaction_id":"","amount":"","currency":"","urgency":"low","sentiment":"positive"}`
- traps: none | fr | forwarded_thread | medium | voters: voter_a: agrees; voter_b: agrees

```text
Subject: Transmission de documents d'identité et de société

Bonjour, je vous fais suivre ci-dessous l'échange avec mon comptable concernant les documents d'identité et de société que vous m'aviez demandés. Je profite de ce message pour vous remercier, car votre équipe a été très réactive et pédagogue la dernière fois que je vous ai écrit, ça fait plaisir. J'ai donc scanné ma pièce d'identité, le justificatif de domicile de la société et le document d'ownership mis à jour, tout est en pièce jointe. Si jamais il manque une pièce ou si un scan est un peu flou, dites-le moi calmement, je vous renverrai ça sans souci. Je ne suis pas toujours très à l'aise avec ce genre de démarches, alors merci d'avance pour votre patience. Je reste dispo si vous avez la moindre question sur les documents transmis.

---------- Message transféré ----------
De : Claire Fontenay <claire.fontenay@cabinet-fontex.fr>
Date : lundi 3 mars 2025
Objet : RE: pièces à fournir pour le dossier société

Bonjour, comme convenu je te confirme la liste des pièces à jour pour le dossier de la société. Il faut la carte d'identité du gérant, un justificatif de domicile de moins de trois mois et l'extrait à jour mentionnant la répartition du capital. Pense à vérifier que les noms et adresses correspondent bien partout, c'est souvent là que ça coince.

Bien à toi,
Claire

-- 
Martin Delaunay
Gérant
Delaunay Logistique
martin@delaunay-logistique.fr
```

## [PASSED] train-20261031-04287 
- label: `{"intent":"compliance","sub_intent":"document_request","transaction_id":"TX-725182","amount":"","currency":"","urgency":"medium","sentiment":"positive"}`
- traps: none | en | short_email | short | voters: voter_a: agrees; voter_b: agrees

```text
Subject: Request for attestation de conformité for TX-725182

Bonjour, I need a certificate or attestation de conformité for transaction TX-725182 for our compliance file, and we're currently stuck because our auditor is asking for it. Merci beaucoup, your team has always been très réactive and I really appreciate the help.
```

## [PASSED] train-20261031-00067 
- label: `{"intent":"OTHER","sub_intent":"OTHER","transaction_id":"","amount":"","currency":"","urgency":"low","sentiment":"positive"}`
- traps: none | en | short_email | short | voters: voter_a: agrees; voter_b: agrees

```text
Hi team, just wanted to say thanks for the help you gave me earlier — everything's working smoothly on my end now. Appreciate it.
```

## [PASSED] train-20261031-03005 judge: accept - intent: The merchant is contesting that the received payout amount differs from expected (107,856.90 EUR vs what landed). This is clearly `dispute` with `amount_mismatch`. sub_intent: `amount_mismatch` fits perfectly - says amount differs from expected. transaction_id: No transaction ID present in ticket, correctly `""`. amount: `107,856.90 EUR` stated as expected amount, normalized to `107856.90` per rules. currency: `EUR` explicitly stated. urgency: The merchant states "this is a live problem for us because we have suppliers waiting on those funds and I cant reconcile the books while the figure is wrong" - ongoing impact with no explicit deadline within 48h, no blocked activity, no frozen funds. Per rules, "a real problem with no deadline and ongoing impact" is `medium`. The `high` annotator is wrong - no 48h deadline, activity not blocked, funds not frozen. sentiment: Explicit frustration ("something is off", "need someone to actually look at this properly", "got a generic reply that didnt answer anything", "pls dont send me a help article"), complaint about previous handling - clearly `negative`. The given label matches the correct reading on all fields.
- label: `{"intent":"dispute","sub_intent":"amount_mismatch","transaction_id":"","amount":"107856.90","currency":"EUR","urgency":"medium","sentiment":"negative"}`
- traps: none | en | chat_message | medium | voters: voter_a: ['urgency']; voter_b: agrees

```text
hey, something is off with the payout we just got and I need someone to actually look at this properly. we expected 107,856.90 EUR for this settlement cycle and what landed in our account is a different number entirely, it doesnt match our ledger at all. ive gone back through the orders twice now and the math is clean on our side, so this isnt us fat fingering anything. this is a live problem for us becuase we have suppliers waiting on those funds and I cant reconcile the books while the figure is wrong. ive raised this before on other cycles and got a generic reply that didnt answer anything, so pls dont send me a help article this time. can someone from payments actually pull up the details and tell me where the difference came from.
```

## [PASSED] train-20261031-02271 judge: accept - intent: The merchant says 'My account is frozen, and I would like to know why' and asks 'what is causing this restriction' — this is exactly 'account_hold' under 'compliance'. Correct. | sub_intent: 'account_hold' matches perfectly. Correct. | transaction_id: No transaction ID present. Correct. | amount: No amount present. Correct. | currency: No currency present. Correct. | urgency: The account is frozen/restricted, which per rules means 'high' ('funds or the account are frozen'). Annotator 1 said 'medium' but the rules are explicit: frozen account = high. Correct as 'high'. | sentiment: Factual, polite request with no emotion markers. 'neutral' is correct. | The given label matches the careful reading exactly.
- label: `{"intent":"compliance","sub_intent":"account_hold","transaction_id":"","amount":"","currency":"","urgency":"high","sentiment":"neutral"}`
- traps: none | en | formal_email | short | voters: voter_a: ['urgency']; voter_b: agrees

```text
Hello,

My account is frozen, and I would like to know why. Could you please let me know what is causing this restriction?

Thank you,
Daniel
```

## [PASSED] train-20261031-06868 
- label: `{"intent":"UNDEFINED","sub_intent":"UNDEFINED","transaction_id":"","amount":"","currency":"","urgency":"UNDEFINED","sentiment":"UNDEFINED"}`
- traps: none | fr | short_email | short | voters: voter_a: agrees; voter_b: agrees

```text
Bonjour, j'ai un souci avec un paiement.

Camille
Gérant
Voyages Horizon
```

## [PASSED] train-20261031-02112 
- label: `{"intent":"OTHER","sub_intent":"OTHER","transaction_id":"","amount":"","currency":"","urgency":"low","sentiment":"positive"}`
- traps: none | fr | short_email | short | voters: voter_a: agrees; voter_b: agrees

```text
Bonjour, je vous remercie pour votre aide, tout est clair de mon côté.

> Bonjour, nous revenons vers vous concernant votre demande. N'hésitez pas à nous écrire si vous avez la moindre question.
```

## [PASSED] train-20261031-04433 judge: accept - intent: Clearly payment_status, correct. sub_intent: The merchant describes both a delayed credit ('virement envoyé il y a un certain temps et il n'a toujours pas été crédité au-delà du délai habituel') AND a status inquiry ('je cherche simplement à savoir où en est ce paiement'). These are two distinct sub-intents of payment_status. Per rules: 'If two requests are equally strong and no main one stands out, intent is UNDEFINED' applies to intent, but here intent is clear. For sub_intent: 'if it is clear but cannot be told apart, UNDEFINED.' The merchant presents both aspects as equally important - the delay complaint and the status question are intertwined with 'D'un côté... De l'autre...' structure. Neither annotator recognized this ambiguity; the written label correctly identifies sub_intent as UNDEFINED. transaction_id: TX-572875 is clearly stated as payment reference, correct. amount/currency: None stated, correct. urgency: Real problem with ongoing impact, no deadline under 48h, not blocked, so medium is correct. sentiment: Polite, factual, no emotion markers, neutral is correct. The written label is correct on all fields; annotators erred on sub_intent by choosing delayed_credit when both delayed_credit and status_inquiry are equally present and cannot be disentangled.
- label: `{"intent":"payment_status","sub_intent":"UNDEFINED","transaction_id":"TX-572875","amount":"","currency":"","urgency":"medium","sentiment":"neutral"}`
- traps: none | fr | short_email | medium | voters: voter_a: ['sub_intent']; voter_b: ['sub_intent']

```text
Subject: Question sur le statut d'un paiement

Bonjour, je souhaite avoir des précisions sur le statut d'un paiement lié à la référence TX-572875. D'un côté, un virement a été envoyé il y a un certain temps et il n'a toujours pas été crédité sur mon compte, au-delà du délai habituel. De l'autre, je cherche simplement à savoir où en est ce paiement dans votre système. Le problème est réel et persiste pour le moment. Pouvez-vous me dire où se trouve l'argent et ce qu'il en est exactement ? Merci de me tenir informé. Bien cordialement, Julien.
```

## [PASSED] train-20261031-02957 
- label: `{"intent":"payment_status","sub_intent":"missing_payment","transaction_id":"TX-857081","amount":"90.90","currency":"EUR","urgency":"medium","sentiment":"neutral"}`
- traps: none | en | formal_email | medium | voters: voter_a: agrees; voter_b: agrees

```text
Subject: Question about my account

Hello,

I am writing on behalf of my company regarding a payment we were expecting for a booking we completed. According to our records the transfer was sent under the reference TX-857081 and the amount in question is €90.90. I have checked our account several times over the past few days and the funds are not showing up anywhere. Our internal reconciliation also does not list this payment, so it appears to have gone missing between the sender and us. Could you please look into the status of TX-857081 and let me know where the money currently is? This is an ongoing issue for us because we cannot close our monthly books while this item stays unresolved. Any information you can provide would be helpful.

Thank you,
Daniel
```

## [PASSED] train-20261031-05543 
- label: `{"intent":"dispute","sub_intent":"unauthorised_fee","transaction_id":"","amount":"94.00","currency":"EUR","urgency":"high","sentiment":"negative"}`
- traps: none | en | formal_email | short | voters: voter_a: agrees; voter_b: agrees

```text
Subject: Problème avec des frais non autorisés sur ma compte

Bonjour, je suis très en colère. Je conteste ce frais de "94,00 EUR" sur mon relevé; je n'ai jamais accepté ça! Mon activité est bloqué à cause de ça, c'est inacceptable.
Cordialement,
Marc
```

## [PASSED] train-20261031-01598 judge: accept - Intent: The merchant is updating company documents and ownership details, which is clearly KYC/compliance work. The technical issues (file upload rejection, page not saving) are obstacles encountered while trying to complete this compliance task, not the main request itself. The core intent is compliance/kyc_update, not technical_api. Sub_intent: kyc_update fits perfectly - submitting/updating identity/ownership/company documents. Transaction_id: no transaction mentioned, "" correct. Amount: no amount mentioned, "" correct. Currency: no currency mentioned, "" correct. Urgency: medium - real problem with ongoing impact (can't complete KYC update since yesterday, blocking work), but no explicit deadline within 48h and account not frozen. Sentiment: neutral - factual/polite request, no frustration markers despite the problem. The given label matches the correct reading.
- label: `{"intent":"compliance","sub_intent":"kyc_update","transaction_id":"","amount":"","currency":"","urgency":"medium","sentiment":"neutral"}`
- traps: none | en | chat_message | long | voters: voter_a: ['intent', 'sub_intent']; voter_b: agrees

```text
Hi, I'm updating the company documents for our account. The ownership section won't accept our new director's details. It keeps saying the file type is not supported even though I'm uploading a PDF.

I also tried to update the company address in the same section, and now the whole page won't save. It just spins and then goes back to the old details. This has been happening since yesterday and I can't get past it.

I work in logistics and our finance team needs the account details to match our registration. Can you tell me what I'm doing wrong or reset the upload for me? Thanks.

Daniel
```

## [PASSED] train-20261031-06679 judge: accept - intent: The ticket is about a chargeback inquiry, clearly 'dispute' with sub_intent 'chargeback'. Correct. | transaction_id: 'TX-363158' is in canonical form and is the payment the request is about. Correct. | amount: '14,785.00 EUR' normalises to '14785.00'. Correct. | currency: 'EUR' is explicitly stated. Correct. | urgency: The merchant states 'the entire account have been frozen' — this is a blocked account/frozen funds, which per rules is explicitly 'high'. Correct. | sentiment: The ticket contains 'We appreciate your team's assistance' and 'Thank you for your support' — these are explicit thanks and satisfaction markers, making this 'positive' per rules. The annotators both chose 'neutral', but the rules state 'positive' = 'explicit thanks or satisfaction'. The given label 'positive' is correct. | All fields in the given label match the careful reading.
- label: `{"intent":"dispute","sub_intent":"chargeback","transaction_id":"TX-363158","amount":"14785.00","currency":"EUR","urgency":"high","sentiment":"positive"}`
- traps: none | en | short_email | medium | voters: voter_a: ['sentiment']; voter_b: ['sentiment']

```text
Subject: Question regarding chargeback TX-363158

I am writing to inquire about the status of the chargeback associated with TX-363158 for 14,785.00 EUR. We noticed that the funds for this transaction, as well as the entire account, have been frozen as a result. Could you please provide an update on the review process for this dispute? We appreciate your team's assistance in resolving this matter. Thank you for your support.

Sarah, Accountant, CloudSoft Solutions
```

## [PASSED] train-20261031-05242 
- label: `{"intent":"dispute","sub_intent":"unauthorised_fee","transaction_id":"","amount":"7457.00","currency":"SEK","urgency":"medium","sentiment":"neutral"}`
- traps: none | fr | chat_message | medium | voters: voter_a: agrees; voter_b: agrees

```text
Bonjour, je viens de passer en revue notre relevé et je vois un frais de 7 457,00 SEK qui ne correspond à rien de ce qu'on a validé. Je suis comptable dans le retail et je gère les rapprochements bancaires au quotidien, donc ce genre de ligne me saute aux yeux. On n'a jamais accepté ce prélèvement, ni par écrit ni verbalement, et il continue d'apparaitre sur nos extraits chaque fois que je recharge les données. J'ai vérifié de mon côté, y compris les échanges avec notre équipe interne, et personne n'a autorisé ce montant. Est-ce que vous pouvez me dire d'ou il vient et le retirer ? Je ne cherche pas à polémiquer, je veux juste que le relevé soit juste. Merci de me dire ce qu'il faut faire pour régulariser.
```

## [PASSED] train-20261031-01154 judge: accept - intent: The merchant asks about PSD2, SCA implementation, and AML guidelines - this is clearly a regulatory question about compliance rules. 'compliance'/'regulatory_question' is correct. sub_intent: Fits perfectly - asking about PSD2, SCA, AML regulations. transaction_id/amount/currency: No payment reference, amount, or currency mentioned in the request. urgency: The merchant mentions 'friction points' and 'confusing' but this is an informational question about understanding regulations, not a blocked activity or deadline. No explicit deadline, no frozen funds, no blocked activity. Per rules, informational requests with no impact are 'low'. The threat to 'look into alternative payment partners' is a conditional future possibility, not an active block. sentiment: 'negative' - the merchant expresses frustration ('confusing', 'friction points', threat to leave). The given label has urgency 'low' but careful reading shows this is informational with no active impact, so 'low' is correct. Both annotators said 'medium' but they appear wrong - no real problem with ongoing impact is described, just confusion and a request for explanation. The given label matches careful reading.
- label: `{"intent":"compliance","sub_intent":"regulatory_question","transaction_id":"","amount":"","currency":"","urgency":"low","sentiment":"negative"}`
- traps: none | en | chat_message | medium | voters: voter_a: ['urgency']; voter_b: ['urgency']

```text
Hey, I need some clarity on how PSD2 compliance interacts with your current SCA implementation for us. Specifically, I'm seeing some friction points when processing certain types of transactions and it's confusing. We're trying to make sure we're fully compliant with all the anti-money-laundering guidelines as well. If this isn't clear, we might need to look into alternative payment partners. Can someone explain the interplay between these regulations on the backend? Thanks.
```

## [PASSED] train-20261031-05794 judge: accept - intent: The merchant reports failed API calls, HTTP error codes, and timeouts - clearly a technical_api request. sub_intent: 'api_error' fits perfectly as they report error codes and timeouts on API calls (not webhook_down, auth_failure, or integration_question). transaction_id: TX-885578 is explicitly introduced as 'a transaction with the reference TX-885578' - valid canonical form. amount: No amount mentioned in the ticket - correctly ''. currency: No currency mentioned - correctly ''. urgency: The problem is 'ongoing and affects our live payment flow' - this is a real problem with ongoing impact, no explicit deadline within 48h, no statement that activity is fully blocked (affects but not blocked), no frozen funds/account. Per rules: 'a real problem with no deadline and ongoing impact' = medium. Annotator 1 said high but no explicit deadline or blocking condition is met. sentiment: Factual, polite request with 'Please let us know' and 'Thank you' - no frustration, anger, or complaint markers. Neutral is correct. The given label matches the careful reading on all fields.
- label: `{"intent":"technical_api","sub_intent":"api_error","transaction_id":"TX-885578","amount":"","currency":"","urgency":"medium","sentiment":"neutral"}`
- traps: none | en | short_email | medium | voters: voter_a: ['urgency']; voter_b: agrees

```text
Hello, I am writing from a logistics company that uses your payments API in our production systems. Since yesterday we have been seeing failed calls and HTTP error codes on several requests, and some calls time out before we get a response. The problem is ongoing and affects our live payment flow, including a transaction with the reference TX-885578. Our integration has not changed recently, so we would like you to check whether there is an issue on your side. Please let us know what you find and whether there is anything you need from us. Thank you. Daniel
```
