# Interview Practice App — agent instructions

Python packages are deep modules. Read
[`src/interview_practice/README.md`](src/interview_practice/README.md) before
adding or importing one.

- Import a subpackage's entry point; never import its `_lib`.
- Keep tests under the package `tests/` tree; tests import the entry point.
- Run `./scripts/check.sh` after changes; it includes `lint-imports`.
- Do not create `src/packages/`; this project uses `src/interview_practice/`.
- Do not push the `course` remote; the owner deferred that action.
- User-facing behaviour is documented in [`USER_MANUAL.md`](USER_MANUAL.md).
