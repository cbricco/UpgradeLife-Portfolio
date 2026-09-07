# Voice Pipeline

## Purpose

This document records the established Upgrade Life voice architecture.

## Preferred Stack

The established voice stack is:

- SoX for audio capture
- the existing wake-word listener and OpenWakeWord model
- whisper.cpp for transcription
- shared deterministic Python routing
- local model fallback where allowed
- Piper for spoken responses
- `audio_manager.py` for shared audio behavior

The approved voice should not be replaced with a generic speech system
merely for convenience.

## Current Runtime Path

The current supported desktop path is:

```text
wake-word listener
    -> conversation controller
    -> transcription
    -> deterministic read-only router
    -> permitted local fallback
    -> Piper response
    -> return to wake listening
```

The obsolete `upgrade_life.py` and `scripts/talk.sh` path has been
retired from the working tree.

## Shared Voice Rule

Future demos, browser features, and companion applications should reuse
the established voice and shared Python audio behavior where practical.

Permanent text-to-speech, recording, transcription, confirmation, or
routing logic must not be duplicated inside unrelated interfaces.

## Authorization Boundary

Wake detection, transcription confidence, spoken confirmation, session
identifiers, voice characteristics, and model output are not by
themselves authorization.
