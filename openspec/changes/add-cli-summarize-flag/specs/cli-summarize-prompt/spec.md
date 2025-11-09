## ADDED Requirements
### Requirement: CLI summarize prompt
The CLI SHALL accept a `--summarize` flag that enables summarization mode alongside existing options including `--json` and `--verbose`.
When summarization mode is enabled, the CLI MUST print the following prompt exactly once to stdout before any transcript output, followed by a blank line:
```
Act as an expert summarizer. Analyze the provided transcript and extract the most important key takeaways, focusing on main ideas, insights, and actionable points. Present them as a concise bullet list.

Example Output:
- Key takeaway 1
- Key takeaway 2
- Key takeaway 3

Input:
```
When summarization mode is disabled, transcript output MUST remain identical to the current behavior.
The summarization prompt MUST precede both plain text and JSON transcripts and MUST NOT be embedded inside JSON payloads.
Warnings and verbose diagnostics MUST continue to route to stderr so stdout stays pipeline-safe.

#### Scenario: Default run remains unchanged
- **GIVEN** a user runs `python main.py <url>` without `--summarize`
- **WHEN** the transcript prints
- **THEN** stdout matches the existing non-summarize format with no prepended prompt

#### Scenario: Summarize flag prepends prompt for text output
- **GIVEN** a user runs `python main.py <url> --summarize`
- **WHEN** the transcript prints
- **THEN** stdout begins with the specified prompt followed by a blank line
- **AND** the transcript content follows exactly as in the default mode
- **AND** stderr remains empty aside from any warning output triggered by `--verbose`

#### Scenario: Summarize flag prepends prompt for JSON output
- **GIVEN** a user runs `python main.py <url> --json --summarize`
- **WHEN** the transcript prints
- **THEN** stdout begins with the specified prompt and blank line
- **AND** the JSON payload appears after the prompt without modification
- **AND** warnings still emit on stderr when `--verbose` is supplied
