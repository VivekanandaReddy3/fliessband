import type { Metadata, Viewport } from "next";
import { IBM_Plex_Mono, IBM_Plex_Sans } from "next/font/google";
import "./globals.css";

const plexSans = IBM_Plex_Sans({
  display: "swap",
  weight: ["400", "500", "600", "700"],
  subsets: ["latin"],
  variable: "--font-plex-sans",
});

const plexMono = IBM_Plex_Mono({
  display: "swap",
  weight: ["400", "500", "600"],
  subsets: ["latin"],
  variable: "--font-plex-mono",
});

export const metadata: Metadata = {
  metadataBase: new URL("https://fliessband.vivekreddy.de"),
  title: "Fließband — a data pipeline that monitors itself",
  description:
    "Daily German energy and weather data, ingested by a GitHub-Actions pipeline into a git-versioned SQLite database — with public run history, quality checks and a freshness SLO.",
};

export const viewport: Viewport = {
  themeColor: "#eef0f2",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en">
      <body
        className={`${plexSans.variable} ${plexMono.variable} flex min-h-screen flex-col`}
      >
        {children}
      </body>
    </html>
  );
}
