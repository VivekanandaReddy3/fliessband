/** Fetches a subsetted TTF from Google Fonts at build time for satori. */
export async function loadGoogleFont(
  family: string,
  text: string
): Promise<ArrayBuffer> {
  const url = `https://fonts.googleapis.com/css2?family=${family}&text=${encodeURIComponent(text)}`;
  const css = await (await fetch(url)).text();
  const match = css.match(/src: url\((.+?)\) format\('(opentype|truetype)'\)/);

  if (!match) {
    throw new Error(`Could not resolve font: ${family}`);
  }

  return await (await fetch(match[1])).arrayBuffer();
}
