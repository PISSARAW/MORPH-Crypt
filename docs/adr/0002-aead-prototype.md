# ADR 0002 : primitive du premier prototype AEAD

- Statut : accepté pour expérimentation uniquement
- Date : 2026-10-24

## Contexte

Le premier jalon technique demande un chiffrement authentifié autonome, sans
inventer de primitive cryptographique et sans dépendre de la disponibilité de
GenOS. Le prototype doit aussi éviter que chaque appelant gère directement un
nonce court.

## Décision

Le prototype utilise XChaCha20-Poly1305 de RustCrypto, version exacte 0.11.0,
avec un nonce de 24 octets généré par le CSPRNG du système à chaque chiffrement.
L'enveloppe est `nonce || ciphertext || tag`; les données associées sont
authentifiées mais restent fournies par l'appelant. Les erreurs
d'authentification ne livrent aucun texte clair.

## Conséquences

- Le runtime reste indépendant de GenOS et l'implémentation du primitive vient
  d'une dépendance versionnée.
- Le projet doit définir son format et son cycle de vie des clés séparément.
- Cette décision ne qualifie pas l'implémentation pour un usage réel.

## Alternatives examinées

- Construire un chiffrement propre : rejeté, car le projet ne doit pas
  implémenter ses propres primitives.
- Exposer directement un nonce 96 bits à chaque appelant : rejeté pour le
  premier prototype, car cela reporte la responsabilité d'unicité sur tous les
  appelants.
