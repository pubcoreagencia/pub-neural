# PUB Neural API - Railway Deployment Guide

This document describes the configuration and deployment of the **PUB Neural Console API** on Railway.

## Architecture

```text
Browser / Client
      │
      ▼ HTTPS
Cloudflare Pages (PUB Neural Command Center)
      │
      ▼ HTTPS REST
Railway Container (PUB Neural Console Backend)
      │
      ▼ PostgreSQL Wire Protocol (SSL)
Supabase (PUB Neural)
```

## Runtime Specifications

- **Container Base**: `python:3.11-slim`
- **Entrypoint**: `python3 -m console.backend.server`
- **Port**: Configured automatically via standard `PORT` environment variable (defaults to `8080`, binds to `0.0.0.0`).
- **Dependencies**: `psycopg2-binary>=2.9.9` (HTTP routing uses standard library `http.server`).
- **Healthcheck Path**: `/health` (unauthenticated, returns HTTP 200 `{"status": "UP"}`).
- **Deep Status Path**: `/api/v1/status` (database connectivity check).

## Environment Variables on Railway

Configure the following variables in the Railway project dashboard:

| Variable | Required | Description | Example |
| :--- | :---: | :--- | :--- |
| `PUB_NEURAL_DB_URL` | **Yes** | Supabase connection string (kept strictly in Railway secrets, never committed) | `postgresql://postgres.[ref]:[pass]@aws-0-[region].pooler.supabase.com:6543/postgres` |
| `CONSOLE_CORS_ORIGINS` | **Yes** | Allowed CORS origins for browser requests from Cloudflare Pages | `https://pub-neural.pages.dev,https://preview.pub-neural.pages.dev` |
| `PORT` | Auto | Railway injects this variable automatically. Server listens on `0.0.0.0:${PORT}` | `8080` |
| `EMBEDDING_PROVIDER` | No | Vector embedding provider for search (`real`, `mock`, or `external`) | `real` (default) |

## Security Guarantees

1. **No Frontend Leaks**: `PUB_NEURAL_DB_URL` is never exposed to the frontend or git repository.
2. **Read-Only Transaction Enforcement**: All database transactions are executed in PostgreSQL `READ ONLY` mode.
3. **Session Authentication**: All protected API endpoints require `Authorization: Bearer <token>`, which is bound to Supabase RLS policies via `pub_neural.attach_session()`.
