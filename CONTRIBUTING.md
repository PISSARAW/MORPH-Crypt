# Contribuer

MORPH-Crypt reprend les règles de contribution GenOS adaptées à ce dépôt.
Les règles de preuve sont strictes : une exécution réussie n'établit que ce
que son contrôle mesure. Ne présentez pas une hypothèse comme un résultat.

## Architecture et code

- Toute évolution d'architecture doit avoir un ADR dans `docs/adr/`.
- Respecter SOLID, garder la complexité cyclomatique au plus à 10 et limiter
  les fonctions à trois paramètres.
- Les fichiers de code ne dépassent pas 400 lignes.
- Ne pas contourner les contrôles par des annotations ou commentaires.
- Ne pas faire dépendre le runtime crypto de la disponibilité de GenOS.
- Aucun changement crypto ne peut être promu ou fusionné automatiquement.

## Fichiers et secrets

Ne commitez jamais de secrets, fichiers `.env`, bases de données, clés privées,
répertoires de build, sorties de tests ou artefacts générés. Les secrets ne
doivent pas apparaître dans les snapshots, journaux ou rapports d'expérience.

## Format des commits

La première ligne commence par un tag majuscule entre crochets, par exemple
`[FEAT]`, `[FIX]`, `[EVOLUTION]`, `[REFACTOR]`, `[DOC]`, `[TEST]` ou `[CHORE]`.

Les commits `[FEAT]`, `[FIX]`, `[EVOLUTION]` et `[REFACTOR]` incluent un bloc
`Receipt:` à la fin du message. Il liste exactement chaque chemin modifié dans
le diff staged, un par ligne, indenté de quatre espaces. Les hooks vérifient le
tag, les chemins reçus, les fichiers interdits et les espaces du diff.

Activez les hooks du dépôt une fois par clone :

```sh
git config core.hooksPath .githooks
```

## Vérifications

```sh
cargo fmt --all -- --check
cargo check --workspace --locked
cargo test --workspace --locked
```

Les vérifications doivent être exécutées avant de proposer des changements de
code. Les rapports décrivent leur portée et ne constituent pas une certification
cryptographique.
