# Moxfield Scraping API

This project exposes a small FastAPI server that forwards requests to the public endpoints used by [moxfield.com](https://moxfield.com). It uses `cloudscraper` to bypass Cloudflare's JavaScript challenge and returns a consolidated view of a user's public decks together with every card in the deck.

## Getting started

```bash
make install
```

Launch the API server locally:

```bash
make run
```

The primary endpoint returns the target user, every public deck, and each deck's full card list:

```
GET http://localhost:8000/users/{username}/decks
```

Example request using `curl`:

```bash
curl http://localhost:8000/users/BimboLegrand/decks | jq
```

A lighter-weight variant returns only the deck metadata without individual card lists:

```
GET http://localhost:8000/users/{username}/deck-summaries
```

A simple health check is available at `GET /health`.

## Testing

Unit tests stub out network traffic and can be executed with:

```bash
make test
```

## OpenAPI / Swagger

The repository includes an `openapi.json` file generated from the FastAPI app. Regenerate it after making API changes:

```bash
make openapi
```

Open the interactive Swagger UI when the server is running at: <http://localhost:8000/docs>.

## Notes

- Only public decks are returned. Private decks remain inaccessible without authentication.
- Responses include the raw Moxfield card payload for each card so your frontend can decide how much detail to surface.
- The client purposefully fetches decks sequentially to avoid overwhelming Moxfield with parallel requests. Adjusting this behaviour is as simple as updating `MoxfieldClient.collect_user_decks_with_details`.
