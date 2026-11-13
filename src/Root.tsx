import React from "react";
import { Composition } from "remotion";
import { MainLandscape } from "./compositions/MainLandscape";
import { RenderManifest } from "./types/contracts";

const defaultDemoManifest: RenderManifest = {
  schemaVersion: "1.0.0",
  runId: "bundled-demo-preview",
  inputDigest: "sha256:bundled",
  templateVersion: "1.0.0",
  renderSeed: 42,
  fps: 30,
  totalFrameCount: 214,
  theme: {
    bgPrimary: "#050713",
    accentPrimary: "#38bdf8",
    accentSecondary: "#f59e0b",
    textPrimary: "#ffffff",
  },
  scenes: [
    {
      id: "scene-01",
      narration: "الثقب الأسود هو مكان في الفضاء جاذبيته قوية لدرجة إن حتى الضوء مبيعرفش يهرب منه.",
      onScreenTitle: "ما هو الثقب الأسود؟",
      template: "title-illustration",
      templateParameters: {
        titlePosition: "top",
        scale: 1.0,
      },
      animationPreset: "zoom-in",
      soundEffect: "whoosh",
      audioFile: "assets/audio/scene-01.mp3",
      audioDigest: "sha256:bundled",
      measuredAudioDuration: 6.72,
      startFrame: 0,
      audioFrameCount: 202,
      sceneFrameCount: 214,
      trailingPauseFrames: 12,
      illustrationFile: "assets/illustrations/scene-01.svg",
      illustrationDigest: "sha256:bundled",
    },
  ],
  assets: [],
};

export const Root: React.FC = () => {
  return (
    <>
      <Composition
        id="MainLandscape"
        component={MainLandscape}
        durationInFrames={defaultDemoManifest.totalFrameCount}
        fps={defaultDemoManifest.fps}
        width={1920}
        height={1080}
        defaultProps={defaultDemoManifest}
        calculateMetadata={({ props }) => {
          return {
            durationInFrames: props?.totalFrameCount || 214,
            fps: props?.fps || 30,
          };
        }}
      />
    </>
  );
};
