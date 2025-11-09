## Why
Users need a way to send transcripts into downstream summarizers without manually typing a prompt each time. A dedicated CLI flag removes that friction and keeps the workflow copy-paste friendly.

## What Changes
- Add a `--summarize` boolean flag to the CLI argument parser
- Prepend a fixed summarization prompt to stdout when the flag is supplied across text and JSON modes
- Extend documentation and automated tests to cover the new flag and its interactions with existing options

## Impact
- Affected specs: cli-summarize-prompt (new)
- Affected code: main.py, tests/test_main_cli.py, README.md
