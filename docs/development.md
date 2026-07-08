# Development Guide

## Code Quality
- Backend is linted using Ruff. Run `ruff check .`
- Frontend is linted using ESLint. Run `npm run lint`

## Testing
- Backend uses `pytest`. Run `python -m pytest` in the backend directory.
- Frontend uses `vitest` and `@testing-library/react`. Run `npm run test` in the frontend directory.

## Migrations
To create a new migration:
`alembic revision --autogenerate -m "description"`
To apply migrations:
`alembic upgrade head`
