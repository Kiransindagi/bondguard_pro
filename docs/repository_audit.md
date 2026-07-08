# Repository Audit

## Files Removed
- `backend/.ruff_cache/`: Removed generated Ruff cache.
- `backend/.pytest_cache/`: Removed generated pytest cache.
- (Any other generated artifacts dynamically ignored and pruned like `__pycache__` and `dist` that are safely tracked out of Git)

## Files Moved
- `backend/verify_5_1.py` -> `backend/scripts/verify_stress_testing.py`: Retained and reorganized one-off script for stress testing verification.
- `backend/check_coverage.py` -> `backend/scripts/verify_historical_coverage.py`: Retained and reorganized script for checking dataset history coverage.
- Frontend `.test.tsx` components were successfully reorganized to match domain context closely. Test entry points like `setupTests.ts` moved to `src/test/setupTests.ts`.

## Files Retained Intentionally
- `backend/ingest.py`: Kept in `backend/` root as an operational pipeline script explicitly requested.
- `backend/seed_portfolio.py`, `backend/seed_stress_scenarios.py`: Kept in root as explicit database seeder entry points.
- Core business tests spanning Sprints 0-5.1.
- All 80 backend tests kept safely.

## Files Ignored By Git
- Added explicit root `.gitignore` to mask:
  - `__pycache__/`, `*.pyc`
  - `.pytest_cache/`, `.ruff_cache/`, `.mypy_cache/`
  - `.coverage`, `htmlcov/`
  - `venv/`, `.venv/`
  - `.env`, `.env.*` (but preserving `.env.example`)
  - `node_modules/`, `dist/`, `.vite/`, `coverage/`
  - IDE specific folders (`.idea/`, `.vscode/`)
  - `*.log`

## Architectural Decisions
- Centralized validation scripts under `backend/scripts/` to declutter the root of the backend folder.
- Kept UI test definitions colocated where practical, but established `src/test/` for global testing setup to separate config from UI.
- Upgraded testing practices via formatting and TS configuration, rather than discarding existing structure.
- Resolved and cleaned the Python environment through `ruff check --fix` ensuring zero unused imports in `__init__` bundles without sacrificing existing modularity.
