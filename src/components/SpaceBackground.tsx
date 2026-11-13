import React, { useMemo } from "react";
import { useCurrentFrame } from "remotion";

interface SpaceBackgroundProps {
  bgPrimary: string;
  seed: number;
}

// Pseudo-random number generator for deterministic star positioning
function pseudoRandom(seed: number) {
  const x = Math.sin(seed++) * 10000;
  return x - Math.floor(x);
}

export const SpaceBackground: React.FC<SpaceBackgroundProps> = ({
  bgPrimary,
  seed,
}) => {
  const frame = useCurrentFrame();

  const stars = useMemo(() => {
    const list: Array<{ x: number; y: number; size: number; opacity: number; speed: number }> = [];
    let currentSeed = seed;
    for (let i = 0; i < 90; i++) {
      const x = pseudoRandom(currentSeed++) * 100;
      const y = pseudoRandom(currentSeed++) * 100;
      const size = 1 + pseudoRandom(currentSeed++) * 2.5;
      const opacity = 0.3 + pseudoRandom(currentSeed++) * 0.7;
      const speed = 0.05 + pseudoRandom(currentSeed++) * 0.15;
      list.push({ x, y, size, opacity, speed });
    }
    return list;
  }, [seed]);

  return (
    <div
      style={{
        position: "absolute",
        width: "100%",
        height: "100%",
        backgroundColor: bgPrimary,
        overflow: "hidden",
      }}
    >
      {stars.map((star, i) => {
        // Deterministic slow drift
        const currentY = (star.y + frame * star.speed) % 100;
        return (
          <div
            key={i}
            style={{
              position: "absolute",
              left: `${star.x}%`,
              top: `${currentY}%`,
              width: `${star.size}px`,
              height: `${star.size}px`,
              borderRadius: "50%",
              backgroundColor: "#ffffff",
              opacity: star.opacity,
              boxShadow: star.size > 2 ? "0 0 6px #38bdf8" : "none",
            }}
          />
        );
      })}
    </div>
  );
};
