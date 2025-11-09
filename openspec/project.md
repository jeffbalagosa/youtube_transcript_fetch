# Project Context

## Purpose
Provide a resilient, zero-credential CLI for collecting YouTube video transcripts.
The tool should succeed even when individual caption sources fail, and emit
transcripts that are easy to pipe into downstream summarizers or editors.

## Tech Stack
- Python 3.8+ (targeted at 3.10 in tooling configs)
- requests for HTTP calls to YouTube endpoints
- yt-dlp for extracting caption tracks from player metadata
- youtube-transcript-api as the final fallback
- argparse, logging, warnings, and unittest from the Python standard library

## Project Conventions

### Code Style
- Ruff enforces linting with 88 character line length and CPython 3.10 targets.
- Prefer explicit helper functions with type hints for reusable logic.
- Keep output-producing code concentrated in `main.main` so CLI behavior remains
	easy to reason about.
- Suppress warnings by default; only surface them when `--verbose` is supplied.

### Architecture Patterns
- Single-module CLI orchestrating three fallback stages: manual timedtext
	scrape, yt-dlp caption download, then youtube-transcript-api.
- Lightweight service functions (`scrape_manual`, `dlp_captions`,
	`api_captions`) contain the network logic so they can be mocked in tests.
- `configure_runtime` centralizes logging and warning behavior to keep stdout
	deterministic for pipelines.

### Testing Strategy
- Standard `unittest` suite in `tests/` with heavy use of mocking to isolate
	network behavior and CLI parsing.
- Run locally with `python -m unittest discover tests` before opening a PR.
- Focus tests on CLI ergonomics, warning routing, and fallback sequencing.

### Git Workflow
- Default branch is `main`; develop features in topic branches and open PRs
	back to `main`.
- Use descriptive commit messages (e.g., `feat: add clipboard helper`) and
	squash on merge when practical.
- Run the unit test suite and linting (`ruff check .`) prior to pushing.

## Domain Context
- Intended for creators and researchers who need fast transcript access without
	API keys.
- Output must stay single-line and timestamped (`[MM:SS] ...`) so piping into
	other tools remains trivial.
- Verbose mode is strictly opt-in to keep stdout clean for machine consumers;
	all diagnostic output must go to stderr.

## Important Constraints
- Must operate without Google API credentials; only publicly reachable
	endpoints are allowed.
- Network requests use a 10 second timeout to avoid hanging pipelines.
- Tool should remain cross-platform (Windows, macOS, Linux) and avoid
	shell-specific dependencies.
- Preserve Unicode characters in transcript output by printing with
	`ensure_ascii=False` when emitting JSON.

## External Dependencies
- YouTube timedtext XML endpoint (`https://video.google.com/timedtext`).
- YouTube player metadata fetched via yt-dlp (requires yt-dlp binary/library).
- `youtube-transcript-api` library hitting YouTube's public transcript service.
- Python ecosystem packages listed in `requirements.txt` (requests, yt-dlp,
	youtube-transcript-api, urllib3 family).
