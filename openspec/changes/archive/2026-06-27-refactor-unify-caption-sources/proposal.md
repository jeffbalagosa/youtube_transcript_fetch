## Why
The three caption sources (`scrape_manual`, `dlp_captions`, `api_captions`) take incompatible inputs — video id vs. url vs. both plus `info`/`verbose`. `main()` papers over this by wrapping each in a lambda to fake a shared call shape. There is no named seam, so the fallback order, the per-source arguments, and the retry logic are all entangled inside `main()`, and adding or reordering a source means editing the loop in place.

## What Changes
- Introduce a single caption-source interface: each source accepts one normalized fetch request and returns transcript segments, raising on failure.
- Carry per-source inputs (`url`, `video_id`, player `info`, `verbose`, `lang`) in a small fetch-request object instead of bespoke positional arguments.
- Replace the lambda list in `main()` with an ordered list of caption sources iterated against the shared interface; fallback sequencing and exhaustion behavior are unchanged.
- Keep the existing segment shape (list of `{"start", "text"}` dicts) — segment typing is deferred to a separate change.
- No user-visible behavior change: output, fallback order, and error exit stay identical.

## Impact
- Affected specs: `caption-fetching` (new capability spec formalizing fallback sequencing and the source interface)
- Affected code: `main.py` (`scrape_manual`, `dlp_captions`, `api_captions`, `main`), `tests/test_main_cli.py` (the `dlp_success`/`manual_fail` mocks adopt the new request shape)
