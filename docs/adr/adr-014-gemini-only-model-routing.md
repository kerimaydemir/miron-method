# ADR-014: Gemini-only model routing

- Status: accepted
- Date: 2026-08-22

## Decision

Every non-deterministic language-model route uses Google Gemini. The routing
table separates responsibilities instead of sending every task to one model:

- `gemini-3.5-flash-lite`: high-volume extraction and normalization
- `gemini-3.5-flash`: grounded research, committee synthesis, and Chief outputs
- `gemini-3.6-flash`: independent criticism and adversarial review

The four roles intentionally use three distinct Gemini models. Sharing the
`gemini-3.5-flash` route between research and synthesis keeps a complete run
inside the active project's per-model request limit; prompts and schemas remain
role-specific.

Quant calculations, cutoff enforcement, budgets, state transitions, hashing,
and prediction locking remain deterministic code. No model may bypass the
existing Chief-only prediction authority.

The model registry expires after 31 days so model availability and pricing must
be reverified before continued paid use. Every request is bounded far below the
model context window and the run hard cap remains fail-closed.

## Activation

The checked-in `.env.example` keeps `GEMINI_ENABLED=false` and has no key, so a
fresh clone cannot make accidental paid calls. The local ignored `.env` may set
`GEMINI_ENABLED=true` after the user approves access and supplies a key. Test
containers override the flag to false. Live runs fail closed instead of silently
falling back to a mock forecast when Gemini is unavailable.
