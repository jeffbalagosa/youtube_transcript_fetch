## Context
`main()` currently drives the fallback with three lambdas that normalize three incompatible signatures:

```python
for step in (
    lambda: scrape_manual(vid_id),
    lambda: dlp_captions(url, info=info, verbose=verbose),
    lambda: api_captions(vid_id),
):
```

The lambdas exist only to hide the signature mismatch. Deleting them does not remove complexity — it reappears at every call site. That is the signal of a real seam that has not been named. This change names it.

## Goals / Non-Goals
- Goals:
  - One interface every caption source satisfies.
  - Fallback order expressed as data (an ordered list), not control flow.
  - Behavior-preserving: identical output, order, and error exit.
- Non-Goals:
  - Typing the transcript segment (deferred — separate change).
  - Collapsing the duplicated yt-dlp construction into a player-info module (deferred).
  - Changing CLI flags, output format, or summarize behavior.

## Decisions
- **Decision: caption sources share the interface `(request: FetchRequest) -> list[dict]`, raising on failure.**
  A source returns segments on success and raises any exception when it cannot produce captions. `main()` catches and advances to the next source, preserving today's `try/except: continue` semantics.
- **Decision: `FetchRequest` is a small dataclass carrying `url`, `video_id`, `info`, `verbose`, `lang`.**
  Each source reads only the fields it needs. This removes the per-source positional-argument knowledge from `main()`.
  - Alternatives considered: a plain dict (rejected — no field discipline, reintroduces the untyped-shape problem this skill is trying to reduce); keyword-only `**kwargs` on each function (rejected — keeps three signatures, just hidden).
- **Decision: the existing functions become adapters to the interface.**
  Each is wrapped (or has its signature adapted) so it accepts a `FetchRequest`. Internal logic is unchanged. `main()` holds `SOURCES = [manual, dlp, api]` and iterates.
  - Alternatives considered: a `CaptionSource` ABC with subclasses (rejected — heavier than three module-level callables warrant; the interface is one method).

## Risks / Trade-offs
- Risk: adapting signatures could change which exceptions surface. → Mitigation: keep each source's body untouched; only the parameter shape changes. Existing warning/fallback tests guard the sequencing.
- Trade-off: a dataclass is marginally more code than passing positional args. → Accepted: it concentrates per-source inputs in one place (locality) and lets a fourth source be added without touching the loop (leverage).

## Migration Plan
1. Add `FetchRequest`.
2. Adapt the three sources to accept it.
3. Replace the lambda list with `SOURCES` and iterate.
4. Update the test mocks (`manual_fail`, `dlp_success`) to the request shape.
5. Run `python -m unittest discover tests` and `ruff check .` — green before done.

## Open Questions
- None blocking. Segment typing and the player-info consolidation are tracked as separate deepenings from the architecture review.
