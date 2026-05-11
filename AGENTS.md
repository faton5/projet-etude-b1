# Repository Guidelines

## Project Structure & Module Organization

This repository currently contains the project specification and placeholder app directories:

- `README.md` - short project identifier.
- `CDC.md` - technical specification for the V0 EHPAD tomato garden app.
- `backend/` - intended FastAPI service, prediction logic, SQLite access, and model code.
- `frontend/` - intended Next.js dashboard and user-facing pages.

Keep API code, data preparation, and model loading under `backend/`. Keep routes, components, and Tailwind styling under `frontend/`. Add tests near the code they validate, for example `backend/tests/` and `frontend/__tests__/`.

## Build, Test, and Development Commands

No package manifests or Docker files are present yet. When adding them, document commands in `README.md`.

Expected commands for this stack:

- `docker compose up --build` - build and run the full local application once Compose is added.
- `cd backend && uvicorn app.main:app --reload` - run the FastAPI API during backend development.
- `cd frontend && npm run dev` - run the Next.js dashboard locally.
- `cd backend && pytest` - run backend tests.
- `cd frontend && npm test` - run frontend tests.

Do not commit virtual environments, local databases, or build folders.

## Coding Style & Naming Conventions

Use domain names from the specification: `prediction`, `weather`, `soil`, `recommendation`, and `history`. Prefer small modules.

For Python, use 4-space indentation, type hints for public functions, and snake_case. For React/Next.js, use PascalCase for components, camelCase for variables, and route conventions for page paths. Keep UI text simple for non-technical EHPAD staff.

## Testing Guidelines

Backend tests should cover input validation, recommendation mapping (`viable`, `attendre`, `non_viable`), weather handling, and SQLite history persistence. Frontend tests should cover core flows: dashboard, prediction launch, and history.

Name tests descriptively, such as `test_prediction_returns_attendre_when_frost_risk.py` or `PredictionForm.test.tsx`. Add regression tests when changing model thresholds, API responses, or stored history format.

## Commit & Pull Request Guidelines

The current history uses short initial messages (`Initial commit`, `first commit`). Going forward, use concise imperative commits, for example `Add FastAPI prediction endpoint` or `Create dashboard layout`.

Pull requests should include a short summary, test results, linked issue or task reference when available, and screenshots for frontend changes. Mention configuration changes, new environment variables, or migrations.

## Security & Configuration Tips

Keep API keys, local `.env` files, SQLite runtime databases, and trained model artifacts out of Git unless they are intentionally small sample fixtures. Document required environment variables in an example file such as `.env.example`.
