# Upgrade Life

Upgrade Life is a personal, AI-assisted software project I am building to
explore what a local-first, voice-oriented personal assistant can become.

The long-term goal is one system that can help organize information, reduce
repetitive work, support reminders and everyday workflows, and eventually be
used through voice, desktop, browser, and mobile interfaces.

This repository is a **sanitized employer-facing code snapshot**, not the
complete Upgrade Life application. The full development repository remains
private because the project is built around personal-life use and contains
development history and machine-specific material that I do not want to
publish.

> **Important authorship disclosure:** AI tools have generated essentially all
> implementation code in the Upgrade Life project. I do not present this
> codebase as code I independently wrote. My role is primarily defining product
> requirements, workflows, desired behavior, approval and safety expectations,
> reviewing verification evidence, deciding whether observed behavior matches
> what I intended, and controlling whether reviewed changes progress.

## Why I Started It

I wanted one assistant that could eventually help connect information across
different parts of everyday life instead of requiring separate disconnected
tools and repeated manual research.

The project also gives me a practical environment for learning more about:

- Python
- Linux
- Git and GitHub workflows
- software testing
- input validation
- failure handling
- deterministic workflow design
- AI-assisted software development

I am still developing my Python knowledge and do not claim to independently
understand or have authored every implementation detail in the full project.

## What Exists Today

The complete private Upgrade Life project is still under active development.

Current work includes a manually launched desktop voice path using local tools,
deterministic Python routing, task and household workflow components, reminder
work, and a growing deterministic approval and authorization foundation.

I have personally observed Upgrade Life perform small bounded coding requests
and some reminder-related functionality.

The current capabilities are much narrower than the long-term vision.

This portfolio snapshot intentionally contains only a small set of reviewed files
chosen to demonstrate software concepts without publishing household data,
machine-specific configuration, development history, large model files, or
active security-development candidates.

## What This Snapshot Demonstrates

### Structured Action Requests

`action_contract.py` shows an example of representing a proposed action with
explicit fields including:

- action name
- record type
- target
- normalized arguments
- risk tier
- session identifier
- interface provenance

The code validates requests against a fixed action registry rather than
treating arbitrary text as authority.

The included example represents both a read-only task action and a grocery
mutation proposal. The mutation-class action deliberately has no execution
adapter in this layer.

### Input Validation and Fail-Closed Behavior

The action-contract example contains checks for malformed values, unexpected
arguments, unknown actions, invalid interfaces, mismatched sessions, changed
targets, changed risk tiers, and unreviewed execution adapters.

The design goal is that uncertain or invalid state is rejected instead of being
silently accepted.

### Deterministic Routing

`command_router.py` shows part of the deterministic routing approach used by
the larger private project.

The router distinguishes read-only operation from actions that could make
changes and routes recognized requests through reviewed Python behavior.

### Testing and Verification

`tests/test_action_contract.py` is included as a representative unit-test file.

It exercises behavior such as:

- immutable request representation
- argument normalization
- malformed-input rejection
- unknown-action rejection
- target and risk-tier tampering
- session mismatch
- interface validation
- refusal to execute a mutation through the read-only execution path
- stable request hashing
- rejection of unreviewed adapters

My development workflow relies heavily on reviewing test and verification
evidence before deciding whether a candidate should progress.

## Interaction Model

The full private project's established desktop voice path is:

```text
wake-word listener
    -> conversation controller
    -> transcription
    -> deterministic read-only router
    -> permitted local model fallback
    -> spoken response
    -> return to wake listening
```

The local voice stack uses technologies including:

- SoX for audio capture
- OpenWakeWord
- whisper.cpp
- Piper
- local model inference through Ollama

The full voice implementation and model files are intentionally not included
in this portfolio snapshot.

## Safety and Approval Philosophy

One of my product requirements is that a language model may help interpret a
request, but model output should not itself authorize consequential actions.

The larger project is therefore being organized around deterministic Python
boundaries that validate proposed actions before execution.

The design direction is:

```text
request
    -> structured proposed action
    -> deterministic validation
    -> policy / approval boundary
    -> allowed action or fail-closed refusal
```

I am not presenting myself as a security engineer or as the independent
designer of the project's low-level security implementation.

## My Role

My role in Upgrade Life is primarily:

- defining what I want the product to do
- defining interaction and workflow behavior
- establishing product requirements
- specifying approval and safety expectations
- deciding what should happen on failure or uncertainty
- reviewing test and verification results
- checking whether observed behavior matches my requirements
- approving or rejecting progression of reviewed changes
- keeping commits, pushes, and promotions under explicit human control

This is a personal project, not paid employment or professional software
development experience.

## AI-Assisted Development

AI is used extensively in this project and has generated essentially all
implementation code.

A simplified version of my development process is:

```text
requirement or problem
    -> AI-assisted analysis
    -> bounded code candidate
    -> tests and verification
    -> review of evidence
    -> human progression decision
```

I keep that distinction explicit because I want the project to demonstrate how
I work with AI tools without overstating my current programming experience.

## Technical Environment

Technologies and tools genuinely used by the larger project include:

- Python
- Linux
- Git and GitHub
- Python unittest
- SoX
- OpenWakeWord
- whisper.cpp
- Piper
- Ollama

This list describes technologies present in the project, not a claim of expert
proficiency in each technology.

## Shared-Core Direction

The long-term design uses one shared deterministic Python core rather than
creating separate business logic for each interface.

Future interfaces are intended to collect input and present output rather than
become independent authorization systems.

## Files Worth Exploring

### action_contract.py

A focused example of structured action representation, validation, risk-tier
metadata, interface provenance, and bounded execution behavior.

### tests/test_action_contract.py

Representative tests for normal behavior, malformed input, tampering,
fail-closed behavior, request identity, and execution-boundary enforcement.

### command_router.py

An example of deterministic routing and explicit read-only behavior.
It depends on additional modules from the private project and is included
for code review rather than as a standalone executable.

### docs/architecture/VOICE_PIPELINE.md

A concise description of the established local voice stack and desktop path.

### docs/architecture/SYSTEM_BOUNDARIES.md

A design-boundary document covering shared-core, interface, model, and
executable-skill principles.

Some phase-status wording in this copied document is historical and should
be read as architecture context rather than current project status.

## Current Limitations

- This repository is a curated snapshot, not the complete application.
- The included Python files have dependencies that are intentionally omitted.
- The snapshot is not intended to be a standalone Upgrade Life install.
- The complete development repository remains private.
- Tier 1 mutation execution remains disabled in the private project.
- Browser and mobile interfaces remain future work.
- There are no production users.
- The project is not commercially deployed.
- I did not independently write the implementation code.
- I am still learning the Python and software-development concepts shown here.

## Long-Term Direction

Planned ideas include:

- a continuously usable desktop assistant
- stronger shared task, grocery, note, reminder, and memory workflows
- a small authenticated API
- a mobile-friendly browser interface
- secure private remote access
- an optional mobile voice companion
- carefully controlled approval workflows for higher-risk actions

These are roadmap goals and should not be interpreted as capabilities that
already exist.

## Running or Demonstrating It Safely

This sanitized repository is intended primarily for code and design review.

It is deliberately incomplete and should not be treated as a standalone
installation package.

A future employer-facing demo may show a small read-only voice or deterministic
workflow using sample data and no private configuration.

## Project Status

Upgrade Life is an active personal learning and product-development project.

This snapshot is intended to demonstrate requirements thinking, disciplined
AI-assisted development, testing and verification habits, growing familiarity
with Python and Linux, deterministic workflow concepts, and explicit human
control over higher-risk changes.

It is not intended to imply professional software-development employment,
independent authorship of the codebase, production deployment, or security
engineering expertise.
