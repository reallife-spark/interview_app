---
title: interview_practice — module boundaries
updated: 2026-11-19
---

# `interview_practice` module boundaries

This repository is one Python application package, not a multi-package
`src/packages/` tree. Keep that convention.

## Entry points and private implementation

```text
interview_practice/
  __init__.py              package version
  engine.py                public root module: InterviewEngine
  usage.py                 public root module: CallUsage
  config.py                public root module: Settings + secret merge
  cost.py                  public root module: model catalog and estimates
  guardrails.py            public root module: GuardrailPipeline
  tailoring.py             public root module: build_tailored_context
  session.py               public root module: SessionState
  evaluation.py            public root module: evaluation runners
  reports.py               public root module: XLSX report builder
  imagegen.py              backend-only image module; no UI action
  messages.py              public root module: ChatMessage
  providers/
    __init__.py            entry point: build_provider + public types
    base.py                public contract: Provider, CompletionRequest, Completion
    _lib/                  private adapters: openrouter, local, demo
    tests/                 black-box provider tests
  retrieval/
    __init__.py            entry point: QuestionMemory + MemoryUnavailable
    _lib/                  private Chroma implementation
    tests/                 black-box Chroma tests (importorskip)
  prompts/
    __init__.py            entry point: PromptLibrary + technique options
    techniques.py          public Technique record
    schemas.py             public QuestionSet/AnswerEvaluation and parsers
    _lib/                  private catalog, templates, defensive prompt, library
    integrity.py           public system-prompt integrity checks
    tests/                 black-box prompt tests
  ui/
    __init__.py            entry point: render_app
    _lib/                  private Streamlit layout
    tests/                 black-box AppTest coverage
```

## Import rules

1. Code outside a subpackage imports only that subpackage's entry point or its
   public root modules; it never imports `_lib`.
2. A subpackage's own files may import its `_lib`.
3. Tests live under the package's `tests/` tree and import only the entry point.
   They never import `_lib`, even their own.
4. No dependency cycles between packages.

`prompts/schemas.py` is deliberately public: `QuestionSet`,
`AnswerEvaluation`, `InterviewRubric` and `JudgeScore` are interface types used
by the engine, session, report and UI. Do not move it into `_lib`.

## No barrel

`prompts/__init__.py` exposes the facade (`PromptLibrary`), technique options
and constants. It does not re-export every schema and helper. Several small
public modules are fine; one giant re-export is not.

## Gate

Run the repository gate:

```bash
./scripts/check.sh
```

It runs:

```bash
./scripts/check.sh
```

`check.sh` selects `.venv/bin/python` when present, then runs pytest, Ruff and
the import gate. The raw commands are:

```bash
.venv/bin/python -m pytest -q
.venv/bin/python -m ruff check .
.venv/bin/lint-imports
```

The import-linter root package is `interview_practice`; `src/packages/` is not
used.

## Proof the gate bites

On 2026-11-16, with 8 contracts:

1. Clean run: `8 kept, 0 broken`.
2. A temporary test import of `interview_practice.ui._lib.layout` failed
   `tests never import implementation`.
3. A temporary sibling package importing `interview_practice.ui._lib.layout`
   failed `ui internals are private`.
4. Two temporary sibling packages importing each other failed
   `no package cycles`.
5. Removing each temporary violation returned `8 kept, 0 broken`.

The gate is not decorative. Keep it wired into the check command.

## Deferred refactors

`SessionState` splitting, an `evaluation` package split, and a private split of
`ui/_lib/layout.py` are deliberate later work. Do not do them just to satisfy a
folder shape.
