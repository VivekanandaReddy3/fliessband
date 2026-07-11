import { ImageResponse } from "next/og";
import { loadGoogleFont } from "@/lib/og-fonts";

export const size = { width: 32, height: 32 };
export const contentType = "image/png";

export default async function Icon() {
  const mono = await loadGoogleFont("IBM+Plex+Mono:wght@600", "FB");

  return new ImageResponse(
    (
      <div
        style={{
          width: "100%",
          height: "100%",
          display: "flex",
          alignItems: "center",
          justifyContent: "center",
          background: "#ff5c00",
          borderRadius: 6,
          color: "#ffffff",
          fontFamily: "Mono",
          fontSize: 15,
          fontWeight: 600,
        }}
      >
        FB
      </div>
    ),
    {
      ...size,
      fonts: [{ name: "Mono", data: mono, weight: 600, style: "normal" }],
    }
  );
}
