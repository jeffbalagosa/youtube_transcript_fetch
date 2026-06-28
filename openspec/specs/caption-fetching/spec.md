# caption-fetching Specification

## Purpose
Define how transcript caption sources are invoked and sequenced.

## Requirements

### Requirement: Uniform caption source interface
Every caption source SHALL satisfy a single interface: it accepts one normalized fetch request carrying the video URL, video id, player info, verbosity, and language, and returns a list of transcript segments. A source MUST raise an exception when it cannot produce captions rather than returning an empty or sentinel result.

#### Scenario: A source produces segments from the request
- **WHEN** a caption source is invoked with a fetch request for a video that has captions
- **THEN** it returns a non-empty list of transcript segments
- **AND** it reads only the request fields it needs (e.g. video id, or url plus player info)

#### Scenario: A source signals failure by raising
- **WHEN** a caption source cannot produce captions for the request
- **THEN** it raises an exception
- **AND** it does not return an empty list as a success value

#### Scenario: Adding a source requires no change to the fallback loop
- **WHEN** a new caption source that satisfies the interface is registered in the ordered source list
- **THEN** it participates in fallback sequencing without any edit to the iteration logic

### Requirement: Resilient fallback sequencing
The system SHALL attempt caption sources in a fixed order — manual timedtext scrape, then yt-dlp extraction, then youtube-transcript-api — returning the transcript from the first source that succeeds. If every source raises, the system MUST exit with a non-zero status and an error message indicating no captions could be fetched.

#### Scenario: First source succeeds
- **WHEN** the manual timedtext source returns segments
- **THEN** that transcript is emitted
- **AND** no later source is invoked

#### Scenario: Earlier sources fail, a later one succeeds
- **WHEN** the manual source raises and the yt-dlp source returns segments
- **THEN** the yt-dlp transcript is emitted
- **AND** the youtube-transcript-api source is not invoked

#### Scenario: All sources fail
- **WHEN** every caption source raises
- **THEN** the system exits non-zero with a message that captions could not be fetched

#### Scenario: Output behavior is unchanged by the interface refactor
- **WHEN** a transcript is fetched through the uniform interface
- **THEN** stdout, fallback order, metadata headers, and the error exit match the pre-refactor behavior exactly
