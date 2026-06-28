## 1. Introduce the fetch request
- [x] 1.1 Add a `FetchRequest` dataclass to `main.py` carrying `url`, `video_id`, `info`, `verbose`, `lang` (default `"en"`)
- [x] 1.2 Build the request once in `main()` after metadata fetch, replacing the loose `vid_id` / `url` / `info` / `verbose` locals passed into sources

## 2. Adapt the sources to the interface
- [x] 2.1 Adapt `scrape_manual` to accept a `FetchRequest` (read `video_id`, `lang`)
- [x] 2.2 Adapt `dlp_captions` to accept a `FetchRequest` (read `url`, `info`, `verbose`, `lang`)
- [x] 2.3 Adapt `api_captions` to accept a `FetchRequest` (read `video_id`)
- [x] 2.4 Confirm each source still raises on failure and returns the existing `{"start", "text"}` segment shape

## 3. Replace the lambda loop
- [x] 3.1 Define an ordered `SOURCES` list (manual, dlp, api) in `main()`
- [x] 3.2 Iterate `SOURCES` against the request with the existing `try/except: continue` semantics and unchanged exhaustion error

## 4. Update tests
- [x] 4.1 Update `manual_fail` / `dlp_success` mocks in `tests/test_main_cli.py` to the `FetchRequest` argument shape
- [x] 4.2 Add a test asserting fallback sequencing through the uniform interface (manual fails → dlp succeeds → api not called)

## 5. Validate
- [x] 5.1 Run `python -m unittest discover tests` — all green
- [x] 5.2 Run `ruff check .` — no new findings
- [x] 5.3 Smoke-test a real URL to confirm output is byte-identical to pre-refactor
