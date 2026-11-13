# Space Motion Studio — Topic to YouTube Video

## Problem Statement

A creator wants to turn science and space ideas into Egyptian Arabic videos for YouTube. Producing each video currently requires separate work on the script, narration, illustrations, animation, timing, and export. Repeating that work makes a regular publishing workflow difficult.

The creator needs an affordable local tool that accepts a topic, automates production, and leaves the results editable. It must explain failures, preserve completed work, and produce a usable video in landscape or vertical format. A creator who supplies their own storyboard and recordings must also be able to use it.

The repository has no implementation, commits, test suite, domain glossary, or ADRs as of November 13, 2026. This specification synthesizes the original proposal, its two review comments, the repository's supplied architecture rules, and the conversation. The first release targets video creation through local export. [Original plan and discussion](https://github.com/mahmoudfarahat2647/space-motion-studio/issues/1)

## Solution

Build a local command-line production pipeline with Python for orchestration and preparation, and Remotion for animation and rendering. Its default content style is a short Egyptian Arabic science explainer with a hook, a sequence of explanatory scenes, and a closing takeaway.

Provide three explicit entry modes. Topic mode uses configured Gemini access to draft a storyboard. Storyboard mode accepts an existing editable storyboard. Demo mode uses a bundled, clearly identified Black Hole example with recorded narration and local assets. A topic request without configured generation access returns an actionable configuration error and explains the available input modes.

The default operation runs unattended from valid input to completed local exports. An optional prepare operation stops after producing an editable storyboard. The creator can change it and continue through the same production pipeline. Preview uses Remotion Studio and the selected run's prepared assets.

Each run owns its input snapshot, storyboard, assets, measured audio, render manifest, status, and exports. Rendering either or both orientations reuses prepared content. Completed runs provide MP4 video, a narration transcript, scene-timed SRT subtitles, and a run report identifying outputs, warnings, and asset credits. The creator uploads the video through their existing YouTube workflow.

Initial defaults are Egyptian Arabic, Shakir narration, 30 fps, a 60-second drafting target, landscape export, a dark space theme, and background music disabled. All defaults are implementation choices for this specification. The first acceptance example is a 20–30-second Black Hole video exported in both orientations.

## User Stories

1. As a creator, I want to provide a science or space topic, so that I can start a video without writing every scene myself.
2. As a creator, I want Egyptian Arabic narration, so that the video matches my intended audience.
3. As a creator, I want a duration target, so that the generated script suits the length I have in mind.
4. As a creator, I want a clear hook and a coherent explanation, so that the video has a useful narrative structure.
5. As a creator, I want to supply my own storyboard, so that I can use scripts I have already written or generated elsewhere.
6. As a new user, I want a complete demo with local media, so that I can verify my installation without API credentials.
7. As a creator, I want an explicit explanation when topic generation is unavailable, so that I can choose another input mode.
8. As a creator, I want to run the whole pipeline with one command, so that routine production requires little manual coordination.
9. As a creator, I want to stop after script preparation when I choose, so that I can revise wording and scientific claims before producing media.
10. As a creator, I want to edit narration, titles, scene order, and visual choices, so that I retain creative control.
11. As a creator, I want to choose the Egyptian male or female voice, so that narration fits my channel.
12. As a creator, I want to supply a recording for a scene, so that I can use my own voice or replace a pronunciation.
13. As a creator, I want to preview prepared scenes, so that I can inspect the result before a full render.
14. As a creator, I want narration to finish before the next scene begins, so that viewers hear each explanation completely.
15. As a creator, I want transitions and sound effects to preserve narration clarity, so that visual polish supports understanding.
16. As a creator, I want correctly joined Arabic text and mixed Arabic/English labels, so that titles remain readable.
17. As a mobile viewer, I want important titles inside a suitable viewing area, so that the vertical video remains legible on my phone.
18. As a creator, I want visual templates that illustrate a concept, so that motion contributes to the explanation.
19. As a creator, I want consistent colors, fonts, and illustration style, so that successive videos feel like the same channel.
20. As a creator, I want local illustrations when online lookup fails, so that optional asset retrieval does not prevent production.
21. As a creator, I want to replace an illustration with my own asset, so that I can correct an unsuitable visual.
22. As a creator, I want optional background music with configurable gain, so that I can control the mood without obscuring speech.
23. As a creator, I want landscape and vertical exports from the same prepared content, so that I can reuse a video across YouTube formats.
24. As a creator, I want each requested orientation recorded separately, so that I can see which exports succeeded.
25. As a creator, I want a transcript and timed subtitles, so that I can inspect the narration and add captions during publishing.
26. As a creator, I want every run to retain its own files, so that one video cannot overwrite another video's work.
27. As a creator, I want completed narration and downloaded assets reused, so that retries avoid unnecessary service calls.
28. As a creator, I want resume after an interruption, so that I can continue from valid completed stages.
29. As a creator, I want edits to invalidate the outputs they affect, so that a revised script cannot accidentally use stale audio.
30. As a creator, I want progress and actionable errors, so that I understand what is happening and how to recover.
31. As a creator, I want prepared runs to render without network access, so that an external outage does not block an existing video.
32. As a creator, I want a clear report of actual duration and fallback visuals, so that I can assess the result before publishing.
33. As a creator, I want asset credits preserved with the export, so that I can include attribution when needed.
34. As a Windows user, I want setup and commands to support Arabic text and paths containing spaces, so that I can use the tool on my current machine.
35. As a maintainer, I want replaceable script, voice, storage, and rendering adapters, so that provider changes have a limited impact.
36. As a maintainer, I want reliable tests through the public workflow, so that I can change internals while preserving creator-visible behavior.

## Implementation Decisions

1. **Release boundary and workflow.** Deliver a CLI and Remotion Studio preview. Support topic, storyboard, and demo inputs, plus prepare, produce, resume, and render-existing operations. Expose format, voice, speaking rate, and duration target as documented options. Input modes are mutually exclusive. Valid produce operations run through export without a mandatory approval prompt. A prepare-only result reports that the storyboard is ready and identifies how to continue.

2. **Initial content scope.** Build short science and space explainers. The duration target guides script generation and the report shows the measured result and difference from the target. Preserve complete narration. Hook, body, closing takeaway, and any creator-supplied intro or outro use the same scene representation. Automatic branded intros and subscription requests are disabled by default.

3. **Domain and application boundaries.** Domain concepts are Storyboard, Scene, Narration, VisualIntent, RenderRequest, and RunStatus. Inner code uses plain values, dataclasses, and narrowly scoped application-owned interfaces. Pydantic, Zod, HTTP clients, filesystem operations, provider SDKs, and Remotion belong to adapters. Adapters translate inputs into application-owned DTOs and translate output DTOs into their external formats. Domain entities stay inside their owning boundary. Dependencies form an acyclic graph directed toward policy.

4. **Modules and composition.** Create storyboard preparation, media preparation, timeline compilation, run coordination, and export use cases. Script generation, voice synthesis, asset resolution, media inspection, run storage, and video rendering have separate adapter responsibilities. The executable composition root supplies concrete adapters. Provider-specific calls and exception handling live with their adapters. A replacement provider must satisfy the same result and failure contracts.

5. **Explicit interchange contracts.** Define a versioned camelCase JSON contract for an editable storyboard and a separate prepared render manifest. Keep a canonical contract definition with shared valid and invalid fixtures. Pydantic validates Python input and output DTOs using explicit alias configuration. Zod validates TypeScript inputs. Both reject unknown properties and unsupported versions with a field location and useful error. Encoding is UTF-8 throughout. [Pydantic alias documentation](https://docs.pydantic.dev/latest/concepts/alias/)

6. **Storyboard contents.** Record schema version, topic, project title, locale, duration target, theme, and a nonempty ordered scene list. Each scene has a unique stable ID, narration, on-screen title, visual intent, an allowlisted template, template-specific parameters, an animation preset, and a sound-effect choice. Optional local illustration and narration references are explicit inputs. Template parameters are discriminated by template type. Validate strings, finite numbers, supported presets, colors, IDs, and references. Authoring data expresses content and intent. Output orientation and measured timing belong to subsequent preparation.

7. **Prepared render manifest.** Record schema version, run ID, input digest, template version, render seed, fps, total frame count, and ordered prepared scenes. Each prepared scene includes local media references, media digests, measured audio duration, start frame, audio frame count, scene frame count, display content, and resolved visual parameters. Record provenance and attribution for external assets. Validate that referenced media exist, match their digests, and belong to the selected run's asset set before rendering. Keep source content snapshots alongside the manifest.

8. **Gemini adapter.** Use an explicitly configured model and credential with schema-constrained output. Supply Egyptian Arabic style instructions, requested topic and length, available templates, and English search keywords. Validate the returned storyboard before any media generation. Allow one corrective generation attempt for invalid structured output, then report the validation errors. Use bounded network retries for transient errors. Save the accepted generated storyboard so resume reuses it. Model choice and prompt version are recorded. The official API supports schema-constrained responses. [Gemini structured output](https://ai.google.dev/gemini-api/docs/structured-output)

9. **Content review.** Generated narration is editable and identified as generated content. Preserve creator-supplied reference links as editorial context. Prepare mode lets the creator correct scientific claims and pronunciations. Rendering success certifies artifact completion. Scientific accuracy remains an editorial review responsibility. Automatic web research and fact verification are future work.

10. **Narration adapter.** Use edge-tts initially, defaulting to ar-EG-ShakirNeural with ar-EG-SalmaNeural selectable. Validate the selected voice when synthesis is requested and surface provider unavailability. Existing supplied recordings take precedence for their scenes. Inspect each finalized audio file in Python before accepting it. Cache by exact narration, provider, voice, locale, rate, pitch, output settings, and adapter version. A cache hit requires a complete, decodable file with the expected digest. edge-tts uses an online speech service. [edge-tts documentation](https://github.com/rany2/edge-tts)

11. **One timeline authority.** Python media inspection supplies measured audio durations. A pure application timeline compiler converts each duration into audio frames by rounding upward at the selected fps, then adds a default 0.4-second trailing pause rounded upward to frames. It computes cumulative scene starts and the exact total once and writes them to the prepared manifest. Narration starts at the scene start. Remotion uses those frame positions and exposes the manifest duration through calculateMetadata. TypeScript validates timing invariants and consumes the prepared schedule. Changing audio or fps regenerates the schedule. [Remotion calculateMetadata](https://www.remotion.dev/docs/calculate-metadata)

12. **Transitions.** The first release uses scene-local entrance and exit animations with sequential scenes. Exit animations occur during trailing padding and the next scene begins at its prepared start. A scene can fade toward the background between cuts. True overlapping crossfades are deferred because they change the timeline and require an explicit narration-overlap policy. Remotion documents that overlapping transitions shorten the total duration. [Remotion transition duration](https://www.remotion.dev/docs/transitions/transitionseries#duration-of-a-transitionseries)

13. **Visual vocabulary.** Supply three reusable template families for a title with illustration, a labeled comparison, and a parameterized space diagram. Include a Black Hole diagram for the acceptance example. Mark schematic or non-scale visuals where that affects interpretation. Theme colors and a curated icon collection provide a consistent style. Template mappings are allowlisted and model-generated text is rendered as text. Keep starfield motion deterministic using a recorded seed. Animations derive from the current frame.

14. **Asset resolution.** Prefer creator-selected assets, then bundled curated assets, then optional Iconify lookup constrained to the configured collection. Resolve each result to an explicit icon identity, store its origin and license metadata, and cache the accepted content. An empty search or exhausted network retry selects a bundled fallback and records a warning. External SVGs are sanitized at ingestion to remove active content and external references. Imported recordings and images are copied into the run so later changes to the original files cannot silently alter an export.

15. **Arabic layout.** Bundle a licensed Arabic-capable font with its license and wait for it to load before rendering. Use RTL layout with deliberate bidirectional handling for numbers and English terms. Animate whole words or complete text blocks. Fit titles within measured bounds and fail with the affected scene ID when readable layout cannot be achieved. Keep essential text inside configurable safe regions. Initial vertical defaults reserve 8% at the top, 20% at the bottom, 15% at the right, and 7% at the left, subject to visual acceptance on a phone. These are product layout defaults.

16. **Export formats.** Offer landscape at 1920 by 1080, vertical at 1080 by 1920, or both, using 30 fps initially. The RenderRequest selects the orientation and components derive layout from actual composition dimensions. Export H.264 progressive video in MP4 with yuv420p pixels and AAC audio at 48 kHz. Verify the finished media with a media inspection adapter. These encoding choices align with YouTube's published upload recommendations. [YouTube encoding guidance](https://support.google.com/youtube/answer/1722171?hl=en)

17. **Runtime render inputs.** Pass the prepared manifest through Remotion input props and select the run's local assets through the public-directory option. Remotion Studio receives bundled demo defaults on a fresh checkout and can preview a selected prepared run. Package local fonts and all render-time media before declaring a run prepared. Rendering a prepared run makes no provider requests. Remotion supports a JSON props file and a configurable public directory. [Remotion CLI](https://www.remotion.dev/docs/cli/render)

18. **Audio mix and subtitles.** Provide deterministic whoosh, pop, and ding effects with conservative configurable gains. Background music is optional creator-supplied local audio with recorded credits, trimmed or looped to the final timeline, faded at boundaries, and ducked during narration. Use one documented normalization and peak-control policy for the final mix. Export the exact narration transcript and one SRT cue per scene's spoken interval, excluding trailing padding. Scene-level subtitles are the initial granularity. Preserve Arabic text and ordering in the subtitle output.

19. **Run identity and persistence.** Assign a unique run ID before writing generated artifacts. Persist a run report with operation, input fingerprint, stage states, timestamps, warnings, provider identifiers, and per-format output records. Stages move through pending, running, completed, and failed states. Interrupted running stages become retryable on resume. Record overall results as prepared, completed, failed, or interrupted according to the operation. A full production run reaches completed only after all requested exports and supporting artifacts pass validation.

20. **Atomic completion and concurrency.** Write temporary artifacts, validate them, then atomically promote them before updating completion records. Partial files cannot satisfy a stage cache hit. Acquire an exclusive per-run lock, reject simultaneous writers to the same run, and allow different run IDs independently. Persist lock ownership and define recovery after a process exits. Shared cache entries use content-addressed immutable artifacts and atomic publication. Each export has a distinct target, so finishing one orientation cannot overwrite another.

21. **Resume and edits.** Revalidate input fingerprints and artifact digests on resume. Voice or narration changes invalidate affected audio and all dependent timing and exports. Visual edits invalidate affected visuals and exports. Orientation changes reuse valid audio and visual assets. Failed rendering preserves prepared inputs and already validated format outputs. Editing a completed run produces a new run referencing reusable cached assets. Resume continues an incomplete run with the same validated input snapshot.

22. **Errors and resource controls.** Report the failing stage, affected scene or export, concise cause, and recovery action. Production failure returns a nonzero exit code. Successful preparation identifies prepared artifacts. Retry transient timeouts, rate limits, and service errors up to three total attempts per request with bounded backoff and provider retry guidance. Authentication and input errors fail immediately. Keep media preparation serial initially and render concurrency configurable. Cancellation terminates child processes and records interrupted status without claiming completion. Secrets are excluded from logs and artifacts.

23. **Windows setup and dependencies.** Use pnpm for all Node package operations and tool invocation. Resolve the actual executable on Windows and invoke child processes with safely separated arguments and an explicit working directory. Python stage modules have importable names and execute through the package entry point. Check Python, Node, pnpm, media tools, browser availability, and selected provider configuration during preflight. Pin matching exact Remotion package versions and compatible validation-library versions. Commit dependency locks or equivalent reproducible pins. Verify the supported Python version against the actual voice dependency installation before documenting it. Provision browser and font dependencies during setup so the bundled demo can render offline afterward.

24. **Output report.** Report each artifact's location, media duration, resolution, fps, source input mode, voice, template version, warnings, and asset credits. Generate transcript and subtitles from the accepted narration and canonical timeline. Every successful requested format must have a verified playable export. A partial run identifies successful outputs and the failed stage, allowing the creator to resume it.

## Testing Decisions

The user confirmed the proposed test boundary in this conversation. The primary seam is the public pipeline command, exercised from input through externally visible artifacts and status. Replace external generation and synthesis services with deterministic adapters for repeatable acceptance tests, and execute the real renderer on small fixtures. The focused additional seam is the Python-to-TypeScript interchange contract.

Good tests assert observable results, validation errors, recovery behavior, and artifact correctness. They avoid coupling assertions to private helper methods, folder layouts, internal call order, or the exact wording produced by a live model. There are no existing tests or test seams to reuse. The original issue's validation checklist provides scenario ideas. [Original verification proposal](https://github.com/mahmoudfarahat2647/space-motion-studio/issues/1)

| Acceptance scenario | Required evidence |
| --- | --- |
| Fresh installation and demo | After documented dependency setup, demo preview opens and production completes with credentials absent and network disabled. |
| Topic production | A deterministic script provider receives the requested topic and produces the corresponding accepted narration, prepared assets, and requested exports. Missing credentials in real topic mode yield an actionable error. |
| Editorial preparation | Prepare produces an editable storyboard. Rendering an edited storyboard uses the revised narration and titles. |
| Cross-language contract | Serialize actual Python DTOs and validate them with the production TypeScript parser. Cover round trips, Unicode, aliases, unknown fields, unsupported versions, duplicate IDs, empty scenes, invalid template parameters, and invalid timing. |
| Actual video export | A short fixture renders through real Remotion in both formats. Inspect streams, dimensions, fps, codecs, and frame count. Video-frame duration equals the canonical schedule. Tolerate documented audio codec padding separately. |
| Full demo acceptance | The 20–30-second Egyptian Arabic Black Hole example renders at 1080p in both orientations with complete narration, readable titles, explanatory visuals, and a valid output report. |
| Audio boundaries | Fixtures with fractional-frame audio lengths verify no narration truncation or unintended overlap. Subtitle cues use spoken intervals and remain inside the final timeline. |
| Isolation and locking | Two different runs retain distinct narration and outputs. A second writer to the same run receives a clear conflict. Recovery after a dead writer preserves valid artifacts. |
| Partial failure and resume | Fail synthesis after one completed scene and interrupt a render. Resume completes successfully using valid earlier artifacts. Incomplete and corrupt files are rejected as cache hits. |
| Content changes | Changing narration, voice, visual parameters, and orientation regenerates the affected artifacts. A completed prior run remains reproducible from its saved snapshot. |
| Provider failure | Exercise transient retries, exhausted retries, invalid structured output, authentication failure, and empty icon results. Confirm finite attempts, actionable exit status, and recorded visual fallbacks. |
| Windows behavior | Run public commands with Unicode topics and paths containing spaces. Verify executable resolution, UTF-8 artifacts, child-process cancellation, and error propagation. |
| Subtitles and export report | Parse generated SRT and verify ordering, text, bounds, and timestamps. Every reported successful media output exists and decodes. |
| Optional music | Verify music respects the final duration, speech ducking, and the documented peak limit on representative audio fixtures. |

Use manual playback and representative frame inspection for Arabic shaping, mixed-direction text, font loading, pronunciation, mobile readability, visual meaning, transitions, and audio balance. Automated schema validation cannot establish these perceptual qualities. Include long titles and both orientations in visual acceptance.

Before first-release acceptance, perform a controlled live Gemini generation and an edge-tts synthesis with the configured Egyptian voices. Record environment and provider configuration, and verify that their results pass the same contracts. Keep these smoke checks explicitly invoked because they depend on credentials, connectivity, and service availability. Standard acceptance tests run without live provider access.

Check the dependency direction through import restrictions or an equivalent static check, and run the application acceptance workflow with substituted adapters to establish that policy can execute independently of external services. Type checking, successful composition discovery, and a real render are required build checks.

## Out of Scope

- YouTube OAuth integration, automatic upload, scheduled publication, channel management, and analytics.
- A web dashboard, collaborative editing, hosted accounts, or a cloud rendering service.
- Batch scheduling across many topics and distributed worker queues.
- Automatic research, scientific fact verification, and source discovery.
- Arbitrary model-generated React, executable code, or custom rendering templates at runtime.
- Generative video models, photorealistic 3D simulation, voice cloning, and local LLM/TTS installation.
- Word-aligned karaoke captions, automatic thumbnail generation, and automatic marketing metadata generation.
- Overlapping cross-scene transitions and automatic condensation of a long landscape script into a separate Shorts narrative.
- Guaranteed exact target duration, fixed rendering-time promises, or permanently unlimited free provider access.

## Further Notes

The first implementation milestone is a complete local demo through the public command and real renderer, including the contract, isolated run, canonical timing, and both orientations. The next milestone adds editable storyboard production, live narration, and recovery. The final first-release milestone adds topic generation, curated asset lookup, optional music, and the complete acceptance checks. All milestones contribute to this specification's release scope.

The review comments correctly identified naming mismatches, missing timing fields, fragile startup data, Arabic font requirements, version alignment, and Windows execution concerns. This specification resolves those concerns through explicit contracts and a verified production workflow. It also assigns timing to one compiler and treats transitions according to their actual effect on duration. [First review](https://github.com/mahmoudfarahat2647/space-motion-studio/issues/1#issuecomment-6855716271) · [Second review](https://github.com/mahmoudfarahat2647/space-motion-studio/issues/1#issuecomment-6855941986)

Decisions made during synthesis include a CLI-first release, optional editorial preparation, a bundled offline demo after setup, scene-level subtitle export, manual YouTube publication, three initial visual template families, and sequential scene timing. These are specification defaults open to later revision. The original plan supplies the Python/Remotion stack, Egyptian Arabic audience, free-tier goal, and two output orientations.

The cost objective is operation with local rendering and available free service access. Gemini availability and quotas depend on the configured service and model. Remotion's published pricing currently offers a free license to individuals and companies of up to three people, including commercial use under its terms. Record asset licenses and applicable runtime terms during implementation. [Gemini pricing](https://ai.google.dev/gemini-api/docs/pricing) · [Remotion pricing](https://www.remotion.dev/pricing)

This is an implementation specification. Its acceptance checks describe evidence the future implementation must produce. Runtime functionality and video quality remain unverified until that implementation exists.
