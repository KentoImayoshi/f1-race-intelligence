# Single-VM deployment prep

This repository already contains the Docker Compose stack that runs the API and Streamlit dashboard together. The following steps capture the smallest realistic path to host that stack on a fresh Ubuntu VM while keeping local workflows intact.

## Environment
1. Copy `config/env/vm.env.sample` to `.env.production` (the `.env.*` pattern is ignored) and adjust any secrets or host-specific values.
2. On the VM, either use `docker compose --env-file .env.production` or symlink `.env.production` to `.env` before starting the stack so Compose picks up the production variables.
3. Any secret (API keys, credentials) should be injected via the VM's secret store or exported in the shell before `docker compose` runs.

## Data persistence
- All data layers live under `data/`. On the VM, create these directories and give them the service user (`ubuntu` or similar) ownership:
  ```bash
  mkdir -p /srv/f1-intel/data/{raw,processed,features,models,insights,llm}
  chown -R ubuntu:ubuntu /srv/f1-intel/data
  ```
- Mount `/srv/f1-intel/data` into the stack by running Compose from the repo root and ensuring `./data` is a symlink to the persistent directory. Example:
  ```bash
  ln -s /srv/f1-intel/data ./data
  ```
- Back up these directories (tarball, rsync) before rolling forward; the files contain the deterministic ingestion outputs and insights.

## Compose workflow
1. From the repo root: `cp config/env/vm.env.sample .env.production` (or edit the file in place) and install Docker & Compose on Ubuntu.
2. Run `docker compose config` to validate the stack.
3. Build/pull images with `docker compose --env-file .env.production build`.
4. Start the stack: `docker compose --env-file .env.production up -d`.
5. Run the health check: `curl http://localhost:8000/health` and open `http://<vm-ip>:8501` to confirm the dashboard.

## Verification and rollback
- To check parity after future updates, rerun the smoke test: `docker compose --env-file .env.production up --build --no-start && docker compose --env-file .env.production start && curl http://localhost:8000/health`.
- Rollback simply reverts `.env.production` or the data mount, then `docker compose --env-file .env.production down && docker compose --env-file .env.production up -d`.

## Out of scope for this milestone
- No load balancers, TLS, or external reverse proxies are configured yet.
- No CI/CD deployment step; releases remain manual until the first VM proves stable.
