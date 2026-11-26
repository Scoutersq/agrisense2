# AgriSense AI — Architecture

## Request flow

```text
React frontend -> FastAPI routes -> schemas/services -> MongoDB or ML inference
```

## ML boundary

Model artifacts are isolated in `ml/saved_models`. API routes must call versioned inference services rather than embedding model logic or predictions in route handlers.

## Security

- JWT secrets are environment variables.
- Passwords must use Argon2 or bcrypt.
- MongoDB credentials must never be committed.
- Production CORS origins must be explicitly configured.

## Model status

No trained model is claimed or bundled in the current foundation phase. Health reporting explicitly identifies this state.

## Authentication status

- Registration and login are Mongo-backed.
- Passwords use bcrypt.
- JWT access tokens are issued for authenticated profile requests.
- `/api/auth/me` and `/api/users/profile` require a bearer token.
