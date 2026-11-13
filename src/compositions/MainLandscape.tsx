import React, { useEffect, useState } from "react";
import {
  continueRender,
  delayRender,
  Sequence,
  staticFile,
} from "remotion";
import { SceneRenderer } from "../components/SceneRenderer";
import { RenderManifest } from "../types/contracts";

export const MainLandscape: React.FC<RenderManifest> = (manifest) => {
  const [fontLoaded, setFontLoaded] = useState(false);

  useEffect(() => {
    const handle = delayRender("Loading Cairo font");
    try {
      const fontUrl = staticFile("assets/fonts/Cairo.ttf");
      const font = new FontFace("Cairo", `url('${fontUrl}')`, {
        weight: "100 900",
        style: "normal",
      });

      font
        .load()
        .then((loadedFont) => {
          document.fonts.add(loadedFont);
          setFontLoaded(true);
          continueRender(handle);
        })
        .catch((err) => {
          console.warn("Failed to load local Cairo font, proceeding with fallback:", err);
          setFontLoaded(true);
          continueRender(handle);
        });
    } catch (e) {
      console.warn("FontFace API error, proceeding:", e);
      setFontLoaded(true);
      continueRender(handle);
    }
  }, []);

  return (
    <div
      style={{
        width: 1920,
        height: 1080,
        position: "relative",
        backgroundColor: manifest.theme.bgPrimary,
      }}
    >
      {manifest.scenes.map((scene, idx) => (
        <Sequence
          key={scene.id}
          from={scene.startFrame}
          durationInFrames={scene.sceneFrameCount}
          name={`Scene ${idx + 1}: ${scene.id}`}
        >
          <SceneRenderer
            scene={scene}
            theme={manifest.theme}
            seed={manifest.renderSeed + idx * 100}
          />
        </Sequence>
      ))}
    </div>
  );
};
