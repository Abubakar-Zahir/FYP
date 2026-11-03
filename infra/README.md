# infra

Local Postgres (with pgvector) and Redis for development.

```
cp infra/.env.example infra/.env        # set at least POSTGRES_PASSWORD
docker compose -f infra/docker-compose.yml up -d --wait
docker compose -f infra/docker-compose.yml exec postgres sh -c 'psql -U "$POSTGRES_USER" -d "$POSTGRES_DB" -c "\dx vector"'
docker compose -f infra/docker-compose.yml exec redis redis-cli ping
```

`POSTGRES_USER` and `POSTGRES_DB` default to `fyp` when left empty. With those defaults, the app connects using:

```
DATABASE_URL=postgresql+asyncpg://fyp:<password>@localhost:5432/fyp
REDIS_URL=redis://localhost:6379/0
```

`docker compose -f infra/docker-compose.yml down` stops the stack and keeps the data. Adding `-v` deletes the data.
