# ADR 0003 : client opérateur GCI Linked

- Statut : accepté pour le pilote de test
- Date : 2026-10-24

## Contexte

MORPH-Crypt est un workspace crypto autonome; GenOS ne doit ni devenir une
dépendance du runtime ni recevoir de matériau secret cryptographique. Le pilote
GCI disponible expose `PROMOTION_GATE@1.0.0` en mode Linked. Cette tranche
requiert `workspace:write` et une preuve d'approbation humaine signée.

## Décision

Ajouter un client opérateur Python basé sur la bibliothèque standard, séparé
des crates Rust. Il épingle le commit et le digest GCI vérifiés, utilise un
projet/environnement de test, et suit la séquence découverte, inspection,
résolution, liaison, adoption, vérification d'installation puis invocation via
l'API GCI. Cette API vérifie l'installation Linked, l'autorité IAM par capacité
et la révocation, appelle le handler publié, puis retourne un reçu GCI. Le client
n'appelle pas directement la route métier.

La commande d'inspection ne modifie pas l'état. La séquence complète requiert
explicitement `--apply`, un run synthétique déjà créé et un fichier de preuve
humaine déjà signé. Le client ne crée pas de run, ne signe pas de preuve et ne
fabrique pas de reçu de réussite. Une clé temporaire à permissions limitées et
une appartenance en écriture au seul projet de test sont requises; elles sont
révoquées après validation.

Le client ne reçoit que les identifiants de tenant/projet, le jeton GCI et la
preuve d'approbation. Il ne reçoit jamais de clé crypto, de nonce, de texte
clair ou de matériau de chiffrement. L'indisponibilité de GenOS ne bloque pas
le runtime MORPH-Crypt.

## Conséquences

- La validation peut établir le parcours Linked de cette route dans un projet
  de test; elle ne certifie ni la sécurité cryptographique MORPH-Crypt ni la
  vérification indépendante de GenOS.
- Le descripteur et le digest épinglés doivent être réévalués à chaque mise à
  jour de la source GenOS.
- Les modes Embedded/Managed et l'évolution des exports restent hors de ce
  pilote.

## Alternatives examinées

- Importer un SDK GenOS dans le runtime Rust : rejeté pour conserver
  l'autonomie du chemin cryptographique.
- Fournir `workspace:write` à la clé persistante de GenOSWork : rejeté; le test
  utilise une clé temporaire et un projet isolé.
- Générer automatiquement la signature ou le reçu humain : rejeté, car cela
  annulerait la séparation entre demandeur et décideur.
