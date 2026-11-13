import React from "react";
import {
  Audio,
  Img,
  interpolate,
  spring,
  staticFile,
  useCurrentFrame,
  useVideoConfig,
} from "remotion";
import { PreparedScene, Theme } from "../types/contracts";
import { ArabicTitle } from "./ArabicTitle";
import { SpaceBackground } from "./SpaceBackground";

interface SceneRendererProps {
  scene: PreparedScene;
  theme: Theme;
  seed: number;
}

export const SceneRenderer: React.FC<SceneRendererProps> = ({
  scene,
  theme,
  seed,
}) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();

  // Scale animation for illustration (zoom-in)
  const scaleProgress = spring({
    frame,
    fps,
    config: {
      damping: 12,
      stiffness: 90,
      mass: 0.9,
    },
  });

  const illustrationScale = interpolate(scaleProgress, [0, 1], [0.6, 1.0]);
  const illustrationOpacity = interpolate(scaleProgress, [0, 1], [0, 1]);

  // Subtle floating motion after entrance
  const floatY = Math.sin((frame / fps) * 2) * 10;

  return (
    <div
      style={{
        position: "relative",
        width: "100%",
        height: "100%",
        display: "flex",
        flexDirection: "column",
        alignItems: "center",
        justifyContent: "space-between",
        padding: "80px 100px",
        boxSizing: "border-box",
        overflow: "hidden",
      }}
    >
      {/* Background */}
      <SpaceBackground bgPrimary={theme.bgPrimary} seed={seed} />

      {/* Top Title */}
      <div style={{ marginTop: "20px", zIndex: 10 }}>
        <ArabicTitle
          title={scene.onScreenTitle}
          accentColor={theme.accentPrimary}
          textColor={theme.textPrimary}
        />
      </div>

      {/* Center Illustration */}
      {scene.illustrationFile && (
        <div
          style={{
            zIndex: 5,
            display: "flex",
            alignItems: "center",
            justifyContent: "center",
            transform: `scale(${illustrationScale}) translateY(${floatY}px)`,
            opacity: illustrationOpacity,
            flex: 1,
            maxHeight: "560px",
          }}
        >
          <Img
            src={staticFile(scene.illustrationFile)}
            style={{
              maxHeight: "520px",
              maxWidth: "520px",
              objectFit: "contain",
              filter: "drop-shadow(0 15px 35px rgba(0, 0, 0, 0.9))",
            }}
          />
        </div>
      )}

      {/* Audio Voiceover */}
      {scene.audioFile && (
        <Audio src={staticFile(scene.audioFile)} />
      )}
    </div>
  );
};
