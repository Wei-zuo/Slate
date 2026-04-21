---
name: screenplay-development
description: Develop commercial screen stories from sparks, loglines, treatments, scene lists, or draft scripts. Use when Codex needs to turn an idea, image, emotion, one-sentence story, outline, or messy screenplay pages into a sharper, producible short film, feature, episode, or web series, including premise design, story breaking, character arcs, scene design, script doctoring, and market-oriented rewrites.
---

# Screenplay Development

## Overview

Work like a compact development room, not a format converter. Convert weak or partial material into a sharper dramatic engine, then expand only to the depth the user actually needs.
Default to a `一句话故事 / logline` gate before full expansion unless the user explicitly asks to skip straight to outline or pages.

## Routing

Classify the request before writing:

- `spark`: a word, image, mood, setting, or impossible question
- `premise`: a one-line story, logline, short synopsis, or setup with a visible hook
- `draft`: a treatment, beat sheet, scene list, dialogue pages, or a full script that needs fixing
- `industrialize`: a request for something more sellable, more commercial, easier to pitch, cheaper to shoot, or more serializable

If the input is thin, do not jump straight to a full screenplay. First lock the story engine.
If the user provides almost nothing, generate `3` viable seed concepts with clearly different hooks and pick the strongest one to deepen.
If the user is still shopping for the core idea, do not draft scenes yet. Generate `3-5` one-sentence story candidates first.

## Default Workflow

### 0. Lock the one-sentence story

Before beats, write the cleanest possible one-sentence story.

- treat it as a selling handle, not a poem
- make the protagonist, conflict, and desire legible fast
- keep lore and explanation out unless the premise itself is the hook
- if the story cannot survive as one sentence, the engine is usually still soft

Use [references/logline-and-save-the-cat.md](references/logline-and-save-the-cat.md) whenever the user asks for `一句话故事`, `logline`, `救猫咪`, story beats, or a pitchable premise.

### 1. Identify the promise

Name the real promise of the material in plain language:

- what the audience is paying to feel
- what the poster image is
- what the trailer moment is
- what makes this premise legible in one breath

If the promise is weak, say so directly and propose stronger variants.

### 2. Build the story engine

Define the minimum dramatic machine:

- protagonist
- visible goal
- inner lack or wound
- opposing force
- irreversible trigger
- escalating cost
- irony or contradiction that makes the story feel alive

Use [references/development-frameworks.md](references/development-frameworks.md) when the story needs a beat model, scene pressure, or format-specific shaping.
Once the engine is clear, use the Save the Cat beats as a structural stress test rather than as a rigid formula.

### 3. Choose the right output depth

Match the output to the user's stage:

- for `spark`: offer `3-5` one-sentence story directions, then deepen the strongest one
- for `premise`: deliver a sharpened one-sentence story/logline first, then character tension, escalation path, and ending logic
- for `draft`: diagnose what the script promises, where it drifts, and how to rewrite it
- for `industrialize`: add audience targeting, format fit, budget logic, repeatable engine, and clearer saleability

Do not force JSON unless the user explicitly asks for machine-readable structure.

### 4. Write in layers

Expand in this order unless the user requests a specific artifact:

1. core premise
2. character web
3. beat progression
4. scene list
5. selected script pages or full treatment
6. full screenplay

Earn scale. A weak premise becomes a weak screenplay faster when expanded too early.
If the user explicitly wants approval before expansion, stop after the one-sentence story options and wait.

### 5. Keep it filmable

Prefer actions, reversals, and choices over thematic explanation.

- make scenes playable, not essayistic
- let character desire drive exposition
- make the turn of each scene visible
- remove scenes that do not change power, information, risk, or intimacy
- avoid vague "and then things get worse" escalation

### 6. Keep the commercial lens on

When the user wants commercial value, evaluate the material through:

- pitch clarity
- audience specificity
- emotional contract
- budget-to-impact ratio
- title strength
- repeatable engine for series or microdrama forms

Use [references/commercial-evaluation.md](references/commercial-evaluation.md) when the user asks whether a concept can sell, how to industrialize it, or how to reshape it for market fit.
In commercial mode, the one-sentence story should be hooky enough to pitch aloud in under 10 seconds.

## Output Modes

Default to concise Chinese prose with short section headers. Choose the lightest structure that still moves the project forward.

Useful response shapes:

- `one-line pass`: `3-5` one-sentence story candidates with quick notes on the difference in engine
- `concept pass`: premise, hook, conflict, why it lands, three directions
- `development pass`: logline, theme pressure, protagonist arc, beat sheet, ending
- `script doctor pass`: current promise, structural problems, character problems, rewrite plan, sample rewritten scene
- `commercial pass`: audience, comps, format recommendation, budget lane, packaging angle, stronger title candidates

When the user asks for options, provide `2-3` materially different versions, not superficial wording swaps.

## Research

Research before writing when the material depends on current facts, laws, news, subcultures, real places, historical detail, or professional procedures. Distinguish clearly between confirmed fact, plausible inference, and invention.

Do not browse for purely emotional or obviously fictional prompts unless research would materially sharpen the work.

## Style Rules

- Be direct about weak concepts.
- Be generous with strong alternatives.
- Preserve the user's emotional core even when replacing the plot machinery.
- Prefer concrete nouns and playable behavior over abstract theme talk.
- Treat "commercial" as clarity plus desire plus producibility, not vulgarity.
- If the user wants auteur, literary, absurdist, or arthouse treatment, keep the same rigor and change the lens rather than forcing mainstream beats.

## Collaboration Rules

- Ask a narrow follow-up only when a missing answer changes the format, audience, or ending.
- Otherwise make a reasonable assumption and state it.
- If the user brings a finished draft, do not praise it generically; diagnose it.
- If the user brings only a vibe, do not overbuild lore; find conflict.
- If the user is still choosing the core idea, default to one-sentence stories first and do not overdevelop unapproved versions.
- If the user asks for a full screenplay immediately, provide it only after locking premise, character, and escalation in the same response.
