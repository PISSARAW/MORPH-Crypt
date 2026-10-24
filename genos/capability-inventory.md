# Inventaire des capacités GenOS épinglées

Révision examinée : `3ec15efb9a5e21d2e1f3bc9d939ebc2391f36eb8` (`v3`).

Cet inventaire décrit les interfaces présentes dans le code source à cette
révision. Il ne prouve ni que le service est déployé, ni qu'une instance est
qualifiée pour une tâche cryptographique. Aucun adaptateur MORPH-Crypt n'est
encore connecté.

| Capacité | Source à la révision épinglée | Constat | Statut pour MORPH-Crypt |
| --- | --- | --- | --- |
| Topology Runtime Port | [`topologyRuntimePort.js`](https://github.com/PISSARAW/GenOS/blob/3ec15efb9a5e21d2e1f3bc9d939ebc2391f36eb8/backend/src/services/morphogenesis/runtime/topologyRuntimePort.js) | Contrat `1.1.0`; cycle de vie `observe`, `adapt`, `quiesce`, `snapshot`, `restore`, `finalize`. États `verified`, `declared`, `unknown`, `unsupported`. L'invocation morphogenétique exige l'état `verified` et une fonction de cycle de vie présente. | Contrat source inspecté; aucune topologie testée ni aucun adaptateur intégré. |
| Ontogenesis Project CLI | [`genos-ontogenesis.cjs`](https://github.com/PISSARAW/GenOS/blob/3ec15efb9a5e21d2e1f3bc9d939ebc2391f36eb8/backend/bin/genos-ontogenesis.cjs) | La commande `init` accepte un workspace `--root`, une branche, un objectif et un identifiant de projet; le CLI expose aussi tâches, état et budgets. | Interface source inspectée; MORPH-Crypt n'est pas encore enregistré dans l'instance GenOS. |
| GVX, AEIS et moteurs formels | Aucun contrat client stable qualifié pour ce dépôt n'a été établi dans cette étape. | Une présence dans le dépôt GenOS ne suffit pas à déterminer le protocole d'appel, les prérequis ou les garanties. | Non intégré; à inventorier avant de dépendre de ces capacités. |

## Conditions d'intégration

- Épingler la révision GenOS et vérifier toute mise à jour contre les contrats
  utilisés.
- Distinguer capacités déclarées et vérifiées; refuser une opération dont le
  contrat ne porte pas l'état `verified`.
- Traiter GenOS comme un plan de recherche facultatif : son indisponibilité ne
  doit pas bloquer le chiffrement ou le déchiffrement.
- N'envoyer à GenOS ni clés ni texte clair; ne lui transmettre que des
  métadonnées non secrètes nécessaires à l'expérience.
- Soumettre les changements de sécurité à une revue humaine avant leur
  promotion.

## Étape restante

L'enregistrement du projet via `genos-ontogenesis.cjs init` n'a pas été
exécuté. Il écrit dans l'état de l'instance GenOS locale; il faut le lancer
depuis une installation GenOS correspondant à la révision épinglée, avec le
workspace MORPH-Crypt et la branche souhaitée.
