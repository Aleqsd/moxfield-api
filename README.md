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

## MongoDB persistence

The API now stores fetched decks and summaries in MongoDB so repeated requests can build on previously synced data.

1. Copy the sample environment file and adjust the connection string if needed:

   ```bash
   cp .env.example .env
   ```

2. Start a local MongoDB instance with Docker:

   ```bash
   make mongo-up
   ```

   This uses the provided `docker-compose.yml` file and exposes MongoDB on `mongodb://localhost:27017`.

3. Export the variables defined in `.env` (for example, `export $(grep -v '^#' .env | xargs)` in bash) before launching the API server. Each call to `/users/{username}/decks` or `/users/{username}/deck-summaries` upserts the user and their deck data into MongoDB.

Stop the database when you're done:

```bash
make mongo-down
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
