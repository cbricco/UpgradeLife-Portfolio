# System Boundaries

## Purpose

This document records durable component boundaries for Upgrade Life.
It supplements `AI System.md`; it does not replace `AGENTS.md`.

## Shared Deterministic Core

Upgrade Life uses one shared deterministic Python core.

Desktop voice, the future authenticated API, browser application,
optional Android companion, and later interfaces must reuse the same
household behavior.

Do not create interface-specific copies of:

- task logic
- grocery logic
- note logic
- reminder logic
- memory logic
- storage rules
- lifecycle rules
- authorization rules
- confirmation behavior
- audit behavior

## Interface Boundary

Interfaces collect input and present output.

They do not become independent authorities for household actions.

Browser, mobile, voice, and future interfaces must treat their input as
untrusted and pass proposed actions through shared deterministic Python
validation.

## Model Boundary

A model may interpret language, extract candidate intent, summarize,
classify, or draft.

A model may never authorize an action.

Model-generated text must never be passed directly to unrestricted
shell execution, `eval`, `exec`, destructive file operations,
unrestricted network actions, external accounts, purchases, messages,
or physical devices.

## Executable Skill Boundary

The shared router uses an explicit reviewed registry of executable
Python skills.

The presence of a Python file in a writable directory must never by
itself make that file executable, importable as a skill, or authorized
to participate in routing.

Future plugin or extension support must define and review its own
trusted source, validation, allowlisting, installation, loading, and
permission boundary before executable discovery is permitted.

## Current Desktop Boundary

The supported desktop voice path is intentionally read-only while
trusted provenance and shared deterministic authorization remain
incomplete.

The current supported launch path starts with
`wakeword/wake_listener.py`.

## Phase 1 Boundary

Phase 1 will define the Shared Action Contract and Mutation Boundary.

This document intentionally does not define that contract in advance.
The verified Phase 1 design should receive its own durable
documentation when implemented.
