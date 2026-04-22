---
name: video-agent-orchestration
description: 制片驱动的视频 agent 编排技能。用于把 brief、现成剧本、传说 IP 或改编需求，组织成制片、编剧、美术设计、副导演、生产五角色流程，并产出 `story_package.md`、`art_package.md`、`storyboard.md`、`ad_feedback.md`、`schedule.md`、`production_todo.md`、`production_packet.md`。Use when Codex needs to coordinate `screenplay-development` and `character-prompt-engine` inside a producer-led video production pipeline.
---

# Video Agent Orchestration

## Overview

This skill is for running a producer-led video pipeline, not for writing one isolated artifact in a vacuum.

Treat the work as a five-role chain:

1. producer
2. screenwriter
3. art design
4. assistant director
5. production

Production may come later, but the pipeline should already be shaped for it.

## Read First

Before you structure the work, read:

- [references/pipeline-files.md](references/pipeline-files.md)
- [references/handoff-rules.md](references/handoff-rules.md)

## Routing

Classify the request first:

- `new-brief`: user only has a rough idea or commission
- `existing-script`: user already has a script or treatment
- `adaptation`: user has a story, legend, IP, article, or draft that must be reshaped for video
- `production-rescue`: upstream materials exist but are too loose to hand to production

If the user already has a script, do not restart from zero. Adapt what exists.

## Core Workflow

### 1. Producer freezes the brief

First produce or normalize `brief.md`.

Minimum brief fields:

- project goal
- platform or format
- target duration
- language
- target audience
- required elements
- forbidden drift
- delivery scope for this round

If the brief is vague, tighten it before routing downstream.

### 2. Screenwriter stage

The screenwriter owns story clarity.

Rules:

- Use `$screenplay-development` when the story premise is loose, underdeveloped, or needs adaptation.
- If premise is not locked, use the one-line gate first.
- If the user already supplied a full script, adapt it into a production-friendly `story_package.md` instead of rewriting the project from scratch.
- Keep the output useful for art and storyboard, not just for literary reading.

Required output:

- `story_package.md`

### 3. Art design stage

The art designer turns story intent into stable visual direction.

Rules:

- Use `$character-prompt-engine` when character prompts, consistency passes, prompt-only outputs, or model-specific prompt adaptation are needed.
- Lock visual anchors for main characters, costume architecture, palette, bridge or set structure, and signature props.
- Art package must be reusable by storyboard and production.

Required output:

- `art_package.md`

### 4. Assistant director stage

The assistant director owns executability.

Rules:

- Do not split storyboard before the story and art packages are readable enough to execute.
- Produce `storyboard.md` and `ad_feedback.md`.
- Call out missing structure, unclear action, visual continuity risks, and which shots should be tested first.

Required outputs:

- `storyboard.md`
- `ad_feedback.md`

### 5. Producer integration stage

The producer consolidates all approved upstream material into a production-ready packet.

Required outputs:

- `schedule.md`
- `production_todo.md`
- `production_packet.md`

The producer decides:

- what gets tested first
- what is P0 / P1 / P2
- which constraints must never drift
- whether failures belong to story, art, storyboard, or model execution

### 6. Production handoff

Unless the user explicitly asks for model execution, stop at the packet.

If the user does ask for production, only proceed when the packet is coherent enough that a production agent will not have to guess.

## Output Contract

Default deliverables for a full orchestration run:

1. `brief.md`
2. `story_package.md`
3. `art_package.md`
4. `storyboard.md`
5. `ad_feedback.md`
6. `schedule.md`
7. `production_todo.md`
8. `production_packet.md`

When useful, also include:

- `adaptation_notes.md`
- `producer_log.md`
- `project-state.yaml`

## Guardrails

- Producer is always the entry point and the collection point.
- Do not let production read scattered documents directly.
- Do not let art rewrite story logic.
- Do not let storyboard invent missing worldbuilding just to keep moving.
- Do not treat a model failure as a story failure without diagnosis.
- If the user provides art test images, include them in the example or packet context instead of leaving them detached from the workflow.

## Practical Defaults

- For folklore, myth, and legend adaptation, favor strong image systems and short dialogue.
- For AI-assisted video work, prefer reusable keyframes, prompt anchors, and explicit consistency notes.
- For 2D animation, lock structure drawings and hero frames before trying to fully animate everything.
