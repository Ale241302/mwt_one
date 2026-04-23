# Sync mwt-knowledge-hub -> pgvector (S28-GH-SYNC)

Automatiza la ingesta del repo privado [`sjoalfaro/mwt-knowledge-hub`](https://github.com/sjoalfaro/mwt-knowledge-hub) hacia el índice vectorial (`knowledge_chunks`) cada vez que hay un push a `main`.

## Arquitectura

```
GitHub push -> webhook (HMAC SHA-256) -> Nginx
                                          |
                                          v
                          /api/knowledge-webhook/github
                                          |
                                          v
                        mwt-knowledge:8001/webhook/github
                                          |
                                          v
               git fetch+reset  ->  diff vs last_sha  ->  index_files()
                                          |
                                          v
                      pgvector (knowledge_chunks + kb_sync_state)
```

GitHub es la única fuente de verdad: si borras un `.md` del repo, sus chunks se borran del índice.

## 1. Crear un Personal Access Token (PAT)

Como el repo es privado, `mwt-knowledge` necesita un PAT con permiso de lectura para clonar:

1. GitHub -> Settings -> Developer settings -> Personal access tokens -> **Fine-grained tokens** -> *Generate new token*.
2. Resource owner: `sjoalfaro`. Repository access: *Only select repositories* -> `mwt-knowledge-hub`.
3. Permissions -> Repository permissions -> **Contents: Read-only**.
4. Copia el token (empieza con `github_pat_...`) y pégalo en `.env`:

```dotenv
GITHUB_TOKEN=github_pat_xxxxxxxxxxxxxxxxxxxxxxxxx
```

## 2. Generar el secreto del webhook

```bash
openssl rand -hex 32
```

Pégalo en `.env`:

```dotenv
GITHUB_WEBHOOK_SECRET=<hex de 64 chars>
```

## 3. Levantar/actualizar los containers

```bash
docker compose build mwt-knowledge nginx
docker compose up -d mwt-knowledge nginx
```

La primera vez que arranque, `init_db()` crea la tabla `kb_sync_state` (singleton, id=1).

## 4. Primer sync (bootstrap)

Dispara manualmente el primer sync para poblar el índice:

```bash
curl -X POST https://consola.mwt.one/api/knowledge/internal/sync/ \
  -H "X-Internal-Token: $KNOWLEDGE_INTERNAL_TOKEN"
```

La respuesta contiene el SHA descargado y el número de archivos indexados. Lo guardamos en `kb_sync_state.last_sha`.

> Nota: `/internal/sync/` pasa por Django (porque `/api/knowledge/` está proxeado así), no por el webhook público. Es para uso interno.

## 5. Configurar el webhook en GitHub

En `https://github.com/sjoalfaro/mwt-knowledge-hub/settings/hooks`:

| Campo | Valor |
|---|---|
| Payload URL | `https://consola.mwt.one/api/knowledge-webhook/github` |
| Content type | `application/json` |
| Secret | el mismo que pusiste en `GITHUB_WEBHOOK_SECRET` |
| SSL verification | Enable |
| Which events | *Just the push event* |
| Active | ON |

GitHub enviará un `ping` inmediatamente. En la pestaña *Recent Deliveries* debes ver `200 OK` con body `{"ok":true,"pong":true}`.

## 6. Probar end-to-end

1. Haz un cambio en un `.md` dentro de `docs/` en el repo y commitéalo a `main`.
2. En GitHub *Recent Deliveries* verás un push con respuesta:

```json
{
  "ok": true,
  "sha": "abcdef...",
  "diff": {"added": [], "modified": ["docs/foo.md"], "deleted": []},
  "reindex": {"files_indexed": 1, "chunks_inserted": 12, "files_deleted": 0, "chunks_deleted": 0}
}
```

3. Verifica en Postgres:

```sql
SELECT last_sha, last_synced_at, last_status FROM kb_sync_state;
SELECT file_path, COUNT(*) FROM knowledge_chunks GROUP BY file_path ORDER BY 1;
```

## 7. Troubleshooting

**Signature inválida (401)**
El `GITHUB_WEBHOOK_SECRET` del `.env` no coincide con el del webhook. Regéneralo y actualiza ambos lados.

**`fatal: Authentication failed`** al clonar
El `GITHUB_TOKEN` expiró o no tiene permiso sobre el repo. Genera uno nuevo con *Contents: Read-only*.

**`event=push` ignorado con `ref=refs/heads/feature-x`**
El webhook solo procesa pushes a la rama configurada en `KB_REPO_BRANCH` (default `main`). Cambia la variable si usas otra rama principal.

**Embeddings no se actualizan**
Forza un full reindex:
```bash
curl -X POST https://consola.mwt.one/api/knowledge/internal/index/ \
  -H "X-Internal-Token: $KNOWLEDGE_INTERNAL_TOKEN"
```

## Variables de entorno relevantes

| Variable | Default | Descripción |
|---|---|---|
| `KB_PATH` | `/kb` | Root del KB dentro del container |
| `KB_REPO_URL` | `https://github.com/sjoalfaro/mwt-knowledge-hub` | URL HTTPS del repo |
| `KB_REPO_BRANCH` | `main` | Rama a seguir |
| `KB_REPO_SUBDIR` | `docs` | Carpeta del repo que se indexa |
| `GITHUB_TOKEN` | — | PAT con Contents: Read-only |
| `GITHUB_WEBHOOK_SECRET` | — | Secret del webhook (HMAC SHA-256) |
| `KNOWLEDGE_INTERNAL_TOKEN` | — | Token para `/internal/*` desde Django |
| `OPENAI_API_KEY` | — | Embeddings `text-embedding-3-small` |
| `ANTHROPIC_API_KEY` | — | Claude Haiku para `/internal/ask/` |
