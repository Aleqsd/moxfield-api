# Agent Playbook

This repository powers a small FastAPI proxy over Moxfield's public API. When working as an automation agent keep the following in mind:

- Use the existing `.venv` virtual environment (or create it via `make install`) before running commands.
- Never commit credentials or attempt to hit private Moxfield endpoints; only the documented public routes are supported.
- Prefer the `Makefile` targets for common tasks (`make run`, `make test`, `make openapi`).
- Tests should mock network access by overriding `get_moxfield_client` rather than performing live HTTP requests.
- Keep docs (`README.md`, `openapi.json`) in sync whenever the API surface changes by running `make openapi`.
