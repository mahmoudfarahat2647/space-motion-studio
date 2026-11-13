import { z } from "zod";

export const ThemeSchema = z
  .object({
    bgPrimary: z.string(),
    accentPrimary: z.string(),
    accentSecondary: z.string(),
    textPrimary: z.string(),
  })
  .strict();

export const SceneSchema = z
  .object({
    id: z.string(),
    narration: z.string(),
    onScreenTitle: z.string(),
    visualIntent: z.string(),
    template: z.string(),
    templateParameters: z.record(z.string(), z.any()).default({}),
    animationPreset: z.string(),
    soundEffect: z.string(),
    illustration: z.string().nullable().optional(),
    narrationAudio: z.string().nullable().optional(),
  })
  .strict();

export const StoryboardSchema = z
  .object({
    schemaVersion: z.literal("1.0.0"),
    topic: z.string(),
    projectTitle: z.string(),
    locale: z.string(),
    durationTarget: z.number().positive(),
    theme: ThemeSchema,
    scenes: z.array(SceneSchema).nonempty(),
  })
  .strict();

export const PreparedSceneSchema = z
  .object({
    id: z.string(),
    narration: z.string(),
    onScreenTitle: z.string(),
    template: z.string(),
    templateParameters: z.record(z.string(), z.any()).default({}),
    animationPreset: z.string(),
    soundEffect: z.string(),
    audioFile: z.string(),
    audioDigest: z.string(),
    measuredAudioDuration: z.number().nonnegative(),
    startFrame: z.number().int().nonnegative(),
    audioFrameCount: z.number().int().positive(),
    sceneFrameCount: z.number().int().positive(),
    trailingPauseFrames: z.number().int().nonnegative(),
    illustrationFile: z.string().nullable().optional(),
    illustrationDigest: z.string().nullable().optional(),
  })
  .strict();

export const AssetRecordSchema = z
  .object({
    path: z.string(),
    digest: z.string(),
    mediaType: z.string(),
    provenance: z.string(),
    attribution: z.string(),
  })
  .strict();

export const RenderManifestSchema = z
  .object({
    schemaVersion: z.literal("1.0.0"),
    runId: z.string(),
    inputDigest: z.string(),
    templateVersion: z.string(),
    renderSeed: z.number().int(),
    fps: z.number().int().positive(),
    totalFrameCount: z.number().int().positive(),
    scenes: z.array(PreparedSceneSchema).nonempty(),
    assets: z.array(AssetRecordSchema).default([]),
    theme: ThemeSchema,
  })
  .strict();

export type Theme = z.infer<typeof ThemeSchema>;
export type Scene = z.infer<typeof SceneSchema>;
export type Storyboard = z.infer<typeof StoryboardSchema>;
export type PreparedScene = z.infer<typeof PreparedSceneSchema>;
export type AssetRecord = z.infer<typeof AssetRecordSchema>;
export type RenderManifest = z.infer<typeof RenderManifestSchema>;
