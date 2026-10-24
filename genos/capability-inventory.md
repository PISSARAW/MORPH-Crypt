# Inventaire des capacités GenOS épinglées

Révision examinée : `236d9c404cbfcc4f305b1fb573b66ad9dbce144f` (`v3`).

Cet inventaire décrit les interfaces présentes dans le code source à cette
révision. Il ne prouve ni que le service est déployé, ni qu'une instance est
qualifiée pour une tâche cryptographique. Aucun adaptateur MORPH-Crypt n'est
encore connecté.

| Capacité | Source à la révision épinglée | Constat | Statut pour MORPH-Crypt |
| --- | --- | --- | --- |
| Topology Runtime Port | [`topologyRuntimePort.js`](https://github.com/PISSARAW/GenOS/blob/236d9c404cbfcc4f305b1fb573b66ad9dbce144f/backend/src/services/morphogenesis/runtime/topologyRuntimePort.js) | Contrat `1.1.0`; cycle de vie `observe`, `adapt`, `quiesce`, `snapshot`, `restore`, `finalize`. États `verified`, `declared`, `unknown`, `unsupported`. L'invocation morphogenétique exige l'état `verified` et une fonction de cycle de vie présente. | Contrat source inspecté; aucune topologie testée ni aucun adaptateur intégré. |
| Ontogenesis Project CLI | [`genos-ontogenesis.cjs`](https://github.com/PISSARAW/GenOS/blob/236d9c404cbfcc4f305b1fb573b66ad9dbce144f/backend/bin/genos-ontogenesis.cjs) | La commande `init` accepte un workspace `--root`, une branche, un objectif et un identifiant de projet; le CLI expose aussi tâches, état et budgets. | Interface inspectée; MORPH-Crypt n'est pas encore enregistré dans l'instance cible. |
| GCI PROMOTION_GATE Linked | [`promotion-gate-v1.json`](https://github.com/PISSARAW/GenOS/blob/236d9c404cbfcc4f305b1fb573b66ad9dbce144f/spec/gci/exports/promotion-gate-v1.json) | Export `PROMOTION_GATE@1.0.0`, digest `sha256:d4bd558694492718c7a18bcbb0ead36afbde5c09f08006a63b4ce5736c1b94c9`; invoqué par l'API GCI Linked, il exige `workspace:write`, signature récente et reçu humain valide. | Client opérateur isolé ajouté; validation externe de bout en bout en attente. |
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

Le client GCI Linked ne modifie pas le runtime crypto. Le projet de test cible
doit être créé dans l'instance GenOS déployée et limité à un environnement
jetable; ne pas réutiliser un workspace crypto métier. Le précédent statut
Ontogenesis local `gvx-ledger-chain-invalid:control-plane-mac-mismatch` reste
non résolu et ne doit pas être confondu avec une liaison GCI. La qualification
externe reste en attente d'un projet GCI isolé, d'une clé temporaire limitée et
d'un run synthétique muni d'une preuve d'approbation humaine réelle.
