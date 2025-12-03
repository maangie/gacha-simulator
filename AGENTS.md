# Repository Guidelines

## Project Structure & Module Organization
- `main.py`: Dash app entrypoint; contains layout, Japanese UI copy, and `simulate_gacha` / `update_simulation` logic. Add new callbacks here until a refactor splits modules.
- `pyproject.toml` and `uv.lock`: Dependency sources of truth. `requirements.txt` is generated; avoid manual edits.
- `README.md`: User-facing overview and setup notes. Update when behavior, commands, or UI text change.
- Tests are not yet present. If you add them, prefer `tests/` with `pytest` and keep fixtures small and deterministic.

## Build, Test, and Development Commands
- Install deps: `uv sync` (preferred) or `uv pip install -r requirements.txt`.
- Run locally: `uv run main.py` (respects `PORT`, defaults to 8050).
- Prod-like serve: `uv run gunicorn main:app.server --bind 0.0.0.0:8050 --workers 2`.
- Update pinned deps after changes: `uv pip compile pyproject.toml -o requirements.txt`.

## Coding Style & Naming Conventions
- Target Python 3.14; keep the existing 2-space indentation to minimize diffs.
- Use `snake_case` for functions and variables; ユーザー向け文言と貢献者向けの説明は必ず日本語で統一し、既存UIのトーンを維持する（内部メモは出力に混ぜない）。
- Prefer small, pure helpers for probability math; keep Dash callbacks declarative and free of side effects.
- Add concise docstrings for new public functions and validations。

## Testing Guidelines
- Manual smoke for now: `uv run main.py` and verify sliders/inputs update the histogram and stats at `http://127.0.0.1:8050/` without errors.
- Exercise edge cases (very small/large probabilities, invalid inputs) to confirm error handling and clipping logic.
- Future tests: name files `test_*.py`, seed randomness where needed, and avoid network or time-dependent behavior.

## Commit & Pull Request Guidelines
- 作業を始めるときは必ず main から作業ブランチを切る（例: `git checkout -b feature/responsive`）；直接 main にはコミットしない。
- Commit messages: clear, imperative verbs (e.g., `Tighten input validation`); no strict convention detected.
- PRs: include intent, key changes, run steps (`uv run main.py`), and screenshots/gifs for UI tweaks.
- Link related issues and flag risk areas (probability math, layout changes); note follow-ups explicitly.

## Security & Configuration Tips
- The app reads `PORT`; default is 8050. Document any new env vars you introduce.
- Keep secrets out of the repo; configure them via environment variables or deployment tooling.
- After dependency changes, run `uv lock` or `uv sync` to keep `uv.lock` and `requirements.txt` aligned for reproducible deploys.
