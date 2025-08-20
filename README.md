# Feature: Anki data read (Chat)

## Goal & scope
Enable the assistant to browse Anki decks and cards via tool-calls inside a chat.

## Intents
- list_decks(limit≤10)
- list_cards(deck, limit≤10)

## Inputs/Outputs
- GET /decks (see openapi.yaml#ListDecksRequest / ListDecksResponse)

## Invariants
See `invariants.yaml`.

## Contracts
- Tool schemas: `tools.yaml` (see repo).
- Reply schemas: `reply_contracts.yaml`.

## Tests
- Golden conversation snapshots under `tests/golden/`.

## Implementation
- `implementation.yaml`
- `src/`
