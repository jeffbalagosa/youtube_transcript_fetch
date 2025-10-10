## Relevant Files

- `main.py` - CLI entry point; now exposes `parse_args` for CLI flag handling.
- `tests/test_main_cli.py` - Unittest module covering flag parsing and warning behavior.
- `README.md` - Update usage docs to describe the `--verbose` option with example output.

### Notes

- Follow TDD: add or extend tests before implementing each functional change.
- Use `python -m pytest` (create if needed) to run the new tests once the testing scaffold is in place.
- Current code does not invoke `warnings` or logging directly; transcript flow uses `print`, while dependency warnings likely surface via their own logging.
- Expected warning scenarios for tests: (a) simulated internal warnings via `warnings.warn`, (b) `yt_dlp` style logger warnings emitted to `stderr`, and (c) `youtube_transcript_api` raising warnings (simulate through mocked logger/print).
- TDD plan: (1) failing test for default run suppressing mocked warnings, (2) failing test for `--verbose` surfacing those warnings, (3) failing test ensuring JSON output remains clean while warnings go to `stderr`, (4) test verifying transcript output unaffected in both modes.
- Use `python -m unittest` to execute the CLI-focused tests added in `tests/test_main_cli.py`.
- Additional CLI tests cover missing URL and unknown flag errors to ensure argparse behavior is enforced.
- Warning behavior tests simulate manual and yt-dlp flows with mocked warnings to validate suppression vs. verbose output.
- `configure_runtime` in `main.py` now toggles Python `warnings` and logging levels based on `--verbose`.
- Tests assert both internal `warnings.warn` and mocked dependency warnings to ensure coverage.
- Added JSON-mode tests confirming stdout remains valid JSON while warnings route to stderr.
- Implementation maintains clean stdout in JSON mode by relying on `configure_runtime` and avoiding writes to stdout for warnings.
- `python -m unittest tests.test_main_cli` runs the full suite since autodiscovery currently skips tests.
- README usage section now documents `--verbose` behavior with sample commands.
- Documentation includes before/after snippets showing verbose output in both plain text and JSON modes.
- README checked for clarity; notional issues with quoted characters remain but instructions align with implementation and tests.
- Custom yt-dlp logger ensures warnings stay silent unless `--verbose` is set; manual CLI run should now be quiet by default.
- Added regression tests around `get_meta_and_info` to ensure yt-dlp warnings are suppressed/restored correctly via a custom logger.

## Tasks

- [x] 1.0 Assess current warning emission paths in `main.py` and dependencies  
  - [x] 1.1 Review existing uses of Python `warnings`, `print`, and dependency loggers to understand current outputs.  
  - [x] 1.2 Document expected warning scenarios to cover in tests (e.g., fallback failures, dependency warnings).  
  - [x] 1.3 Sketch TDD plan mapping each scenario to a specific test case.
- [x] 2.0 Extend CLI argument handling to add `--verbose` without breaking existing flags  
  - [x] 2.1 Write a failing test ensuring `--verbose` is recognized alongside existing positional args and `--json`.  
  - [x] 2.2 Implement or refactor argument parsing so the new test passes (consider adopting `argparse`).  
  - [x] 2.3 Run tests to confirm parsing behavior and adjust for edge cases (duplicate flags, unknown flags).
- [x] 3.0 Suppress warnings by default and restore current behavior when `--verbose` is set  
  - [x] 3.1 Add failing tests asserting no warnings are emitted without `--verbose`, and warnings appear when it is passed.  
  - [x] 3.2 Implement suppression logic (e.g., configure `warnings`, logger levels, and dependency options) to satisfy tests.  
  - [x] 3.3 Validate test coverage includes both tool-generated and dependency-generated warnings.
- [x] 4.0 Verify warning behavior in both standard and `--json` outputs  
  - [x] 4.1 Write failing tests demonstrating that transcripts render correctly and warnings route to their stream for both default and JSON modes.  
  - [x] 4.2 Adjust implementation to ensure warnings coexist with JSON output without corrupting `stdout`.  
  - [x] 4.3 Run the full suite to confirm no regression in text/JSON formatting.
- [x] 5.0 Document the `--verbose` option in `README.md`, including usage example  
  - [x] 5.1 Draft README updates summarizing default/suppressed behavior and the verbose flag.  
  - [x] 5.2 Include a before/after example illustrating transcript output with and without `--verbose`.  
  - [x] 5.3 Proofread documentation for clarity and alignment with implementation.
