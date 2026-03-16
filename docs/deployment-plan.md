# Minimal deployment plan

## Recommended target
- Deploy to a **single Linux VM (Ubuntu 24.04 LTS or similar)** that runs Docker Engine + Compose. Use the existing `docker-compose.yml` to start the API and dashboard together behind a simple firewall.

## Why this target
- The repository already provides an end-to-end deterministic slice (API, dashboard, Compose, CI), so a single VM leverages what exists without introducing extra orchestration.
- Docker Compose keeps the deployment explicit: no new runtime code, no new orchestration layers, and both services share the same network artifact.
- A single VM is cheap, easy to provision, and fits the small-scope “first deployment” goal while remaining production-like (network isolation, persistent volumes).

## Required changes before deploy
1. **Environment files:** publish `config/env/vm.env.sample` as the production template, still using `.env.example` for the local workflow, and document copying it to `.env.production` while keeping secrets outside the repo.
2. **Persistence documentation:** outline VM steps that create the `data/` folders, link a persistent `/srv/f1-intel/data` mount into `./data`, and explain the backup cadence so Compose volumes do not vanish when containers restart.
3. **Prove Compose stack:** run `docker compose config` plus the smoke test (`docker compose up --build`, `curl http://localhost:8000/health`, `docker compose down`) locally and save any quirks so VM provisioning can reproduce them.
4. **Guide reference:** store the minimal VM workflow (env file, data mount, Compose validation) in `docs/vm-deployment-readme.md` for rapid onboarding.

## Deployment sequence
1. Provision the VM (Ubuntu 24.04), install Docker & Compose, and harden SSH/firewall (allow ports 22, 8000, 8501, and restrict others).
2. Pull the repository (or image) onto the VM, copy `.env.production`, and prepare persistent `data/` folders (with `chown` if necessary).
3. Run `docker compose pull`/`docker compose build` to ensure images are ready, then `docker compose up -d` using the documented env.
4. Verify:`curl http://localhost:8000/health` and `curl http://localhost:8000/pipeline` once the services are up; also check dashboard on port 8501 (or other API base URL) from a browser if allowed.
5. Schedule a lightweight monitoring: e.g., a cron job that ensures Compose services stay running or a script that reruns the smoke test daily.

## Rollback/basic recovery notes
- Keep the last working Compose artifact/tag available on the VM (e.g., `docker compose pull` can be rerun with the previous commit SHA if images are tagged). If a deployment fails, run `docker compose down`, roll back to the prior env file, and rerun `docker compose up -d`.
- Back up the `data/` directories nightly (tarball or rsync) so ingestion results survive a rollback.
- Document a simple “redeploy” script (`docker compose down && docker compose pull && docker compose up -d`) that operators can run safely.

## Out of scope
- No automated CI/CD pipeline or GitHub Actions deployment yet; deployments are manual for this milestone.
- No advanced monitoring/alerting (metrics, tracing, dashboards) beyond the basic health checks described above.
- No multi-host clustering, load balancers, or managed Kubernetes platforms.
