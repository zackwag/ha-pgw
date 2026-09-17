# AGENTS.md

## Project overview

Home Assistant custom integration (HACS) for Philadelphia Gas Works (PGW). Python, wraps the `pgw-api` client library as HA entities.

## Setup

```sh
pip install .[test]
```

## Build / Run

N/A — this is a Home Assistant custom component, not a standalone app. It's installed into a running Home Assistant instance (via HACS or by copying `custom_components/pgw/` into HA's config directory).

## Test

```sh
pytest
```

Config: `pyproject.toml` (`asyncio_mode = "auto"`). Uses `pytest-homeassistant-custom-component` to simulate a Home Assistant environment. Requires Python >= 3.12.

## Repository structure

- `custom_components/pgw/` — the integration itself
- `tests/` — pytest suite
- `hacs.json` — HACS metadata
- `pyproject.toml` — dependency on `pgw-api` (the standalone API client, published separately at zackwag/pgw-api)

## Commit and PR conventions

- Commit messages and PR titles must follow [Conventional Commits](https://www.conventionalcommits.org/) (`feat:`, `fix:`, `docs:`, `chore:`, `refactor:`, `test:`, `ci:`, `build:`, `perf:`, `style:`, `revert:`), optionally with a scope, e.g. `fix(api): handle null response`.
- This repo squash-merges pull requests only; the PR title becomes the final commit message on `main`.
- A "Conventional Commits" CI check enforces this on both PR titles and direct-push commit messages.
- Branch protection on `main`: no force-pushes, no branch deletion, required status checks must pass.
