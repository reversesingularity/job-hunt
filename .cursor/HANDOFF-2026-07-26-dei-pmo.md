# Agent handoff — 2026-07-26 (DE&I PMO publish + landing)

Canonical handoff for the DE&I dashboard lives in:

**[`dei-pmo-dashboard/HANDOFF.md`](../dei-pmo-dashboard/HANDOFF.md)**

Landing-site handoff (registry + Railway DNS + ship):

**`F:\Projects-cmodi.000\reversesingularity_landing\docs\SESSION-HANDOFF.md`**

## Live

- App: https://dei-pmo.reversesingularity.com
- Card: https://reversesingularity.com (`dei-pmo`)
- GitHub: https://github.com/reversesingularity/dei-pmo-dashboard

## Parent repo touchpoints updated

- `GOVERNANCE.md` — OIA/Crown Copyright class, DE&I security-vs-copyright section, decision log (includes Railway + landing ship)
- `README.md` — standalone GitHub link + required OIA caption
- `SECURITY.md` — Crown Copyright / emblems
- `CONTRIBUTING.md` — PR checklist for OIA caption + dual-repo sync
- `.cursor/rules/project-context.mdc` — DE&I attribution rules
- `.cursor/plans/architecture.md` — standalone publish notes
- `.gitignore` — exception for `dei-pmo-dashboard/docs/oia-reference/*.pdf` only
- `.cursor/HANDOFF-2026-07-26-dei-pmo.md` — this pointer file

## Standalone app deploy assets (commit if still untracked)

- `Dockerfile`, `railway.toml`, `.dockerignore`

## Incident note

Commit `247c696` briefly pushed personal CV / `output/` PDFs to `job-hunt`. Removed in `d26bcb7`. Tip of `main` only tracks the three OIA reference PDFs. History purge optional if blobs must be erased from GitHub.
