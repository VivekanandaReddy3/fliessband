import { ImageResponse } from "next/og";
import { loadGoogleFont } from "@/lib/og-fonts";

export const alt = "Fließband — a data pipeline that monitors itself";
export const size = { width: 1200, height: 630 };
export const contentType = "image/png";

const SANS = "Fließband a data pipeline that monitors itself.";
const MONO =
  "FB DATEN-PIPELINE · STATUS GitHub Actions → Python → SQLite in git → JSON → status page vivekreddy.de OPERATIONAL";

export default async function Image() {
  const [sans, mono] = await Promise.all([
    loadGoogleFont("IBM+Plex+Sans:wght@700", SANS),
    loadGoogleFont("IBM+Plex+Mono:wght@500", MONO),
  ]);

  const stripes: React.ReactNode[] = [];
  for (let i = 0; i < 60; i++) {
    stripes.push(
      <div
        key={i}
        style={{
          width: 14,
          height: 20,
          background: i % 2 === 0 ? "#1a7f37" : "#14632b",
          transform: "skewX(-30deg)",
        }}
      />
    );
  }

  return new ImageResponse(
    (
      <div
        style={{
          width: "100%",
          height: "100%",
          display: "flex",
          flexDirection: "column",
          justifyContent: "space-between",
          background: "#eef0f2",
          color: "#171b1f",
        }}
      >
        <div style={{ display: "flex", overflow: "hidden" }}>{stripes}</div>

        <div
          style={{
            display: "flex",
            flexDirection: "column",
            padding: "0 72px",
            gap: 20,
          }}
        >
          <div style={{ display: "flex", alignItems: "center", gap: 18 }}>
            <div
              style={{
                background: "#ff5c00",
                color: "#fff",
                fontFamily: "Mono",
                fontSize: 30,
                padding: "8px 16px",
              }}
            >
              FB
            </div>
            <div
              style={{
                fontFamily: "Mono",
                fontSize: 20,
                letterSpacing: 5,
                color: "#6a737d",
              }}
            >
              DATEN-PIPELINE · STATUS
            </div>
          </div>
          <div
            style={{
              fontFamily: "Sans",
              fontSize: 88,
              fontWeight: 700,
              lineHeight: 1.02,
              letterSpacing: -2,
            }}
          >
            Fließband
          </div>
          <div
            style={{
              fontFamily: "Sans",
              fontSize: 36,
              color: "#6a737d",
            }}
          >
            a data pipeline that monitors itself.
          </div>
          <div
            style={{
              fontFamily: "Mono",
              fontSize: 22,
              color: "#171b1f",
              background: "#ffffff",
              border: "1px solid #d5dae0",
              borderRadius: 8,
              padding: "14px 20px",
              alignSelf: "flex-start",
            }}
          >
            GitHub Actions → Python → SQLite in git → JSON → status page
          </div>
        </div>

        <div
          style={{
            display: "flex",
            justifyContent: "space-between",
            padding: "0 72px 40px",
            fontFamily: "Mono",
            fontSize: 20,
            color: "#6a737d",
          }}
        >
          <div style={{ display: "flex", alignItems: "center", gap: 10, color: "#1a7f37" }}>
            <div
              style={{
                width: 12,
                height: 12,
                borderRadius: 9999,
                background: "#1a7f37",
              }}
            />
            OPERATIONAL
          </div>
          <div>vivekreddy.de</div>
        </div>
      </div>
    ),
    {
      ...size,
      fonts: [
        { name: "Sans", data: sans, weight: 700, style: "normal" },
        { name: "Mono", data: mono, weight: 500, style: "normal" },
      ],
    }
  );
}
