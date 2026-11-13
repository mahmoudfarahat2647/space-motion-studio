import React from "react";
import { interpolate, spring, useCurrentFrame, useVideoConfig } from "remotion";

interface ArabicTitleProps {
  title: string;
  accentColor: string;
  textColor: string;
}

export const ArabicTitle: React.FC<ArabicTitleProps> = ({
  title,
  accentColor,
  textColor,
}) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();

  // Entrance spring animation
  const entrance = spring({
    frame,
    fps,
    config: {
      damping: 14,
      stiffness: 100,
      mass: 0.8,
    },
  });

  const translateY = interpolate(entrance, [0, 1], [-40, 0]);
  const opacity = interpolate(entrance, [0, 1], [0, 1]);

  return (
    <div
      dir="rtl"
      style={{
        display: "flex",
        flexDirection: "column",
        alignItems: "center",
        justifyContent: "center",
        textAlign: "center",
        transform: `translateY(${translateY}px)`,
        opacity,
        zIndex: 10,
        padding: "0 40px",
      }}
    >
      <h1
        style={{
          fontFamily: "'Cairo', 'Segoe UI', Tahoma, sans-serif",
          fontSize: "64px",
          fontWeight: 800,
          color: textColor,
          margin: 0,
          lineHeight: 1.3,
          textShadow: "0 4px 20px rgba(0, 0, 0, 0.8)",
          direction: "rtl",
        }}
      >
        {title}
      </h1>
      <div
        style={{
          width: interpolate(entrance, [0, 1], [0, 180]),
          height: "4px",
          backgroundColor: accentColor,
          borderRadius: "2px",
          marginTop: "16px",
          boxShadow: `0 0 12px ${accentColor}`,
        }}
      />
    </div>
  );
};
