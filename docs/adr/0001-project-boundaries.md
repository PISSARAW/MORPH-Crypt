# ADR 0001 : frontières du projet MORPH-Crypt

- Statut : accepté
- Date : 2026-10-24

## Contexte

MORPH-Crypt est un projet de recherche cryptographique qui souhaite utiliser
GenOS pour coordonner les expériences et conserver leur provenance. Une
dépendance directe du moteur cryptographique sur le runtime de recherche
couplerait la disponibilité et le niveau de confiance du chiffrement à un
orchestrateur qui évolue indépendamment.

## Décision

MORPH-Crypt est un dépôt autonome et un workspace Rust. Le code crypto est
séparé des politiques, de la lignée des clés, des transitions et des
vérificateurs. GenOS est relié par un manifeste versionné et des adaptateurs
explicites. La recherche ne peut pas modifier ou promouvoir automatiquement le
code de sécurité. Le runtime doit continuer à fonctionner lorsque GenOS est
indisponible.

## Conséquences

- Les dépendances GenOS sont épinglées par commit et tout changement de révision
  exige une nouvelle vérification de compatibilité.
- Les candidats crypto sont évalués avec des preuves indépendantes et une
  validation humaine avant promotion.
- Le dépôt ne prétend pas encore implémenter un chiffrement utilisable.

## Alternatives examinées

- Copier ou forker GenOS : rejeté, car cela dupliquerait le plan de contrôle et
  lierait inutilement les deux cycles de publication.
- Exécuter MORPH-Crypt uniquement comme projet GenOS : rejeté, car l'exécution
  cryptographique doit rester disponible indépendamment de GenOS.
