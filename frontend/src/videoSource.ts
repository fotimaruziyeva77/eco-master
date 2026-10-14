/** What a project's video link is: a YouTube video, a file the app can play, or another page. */
export type VideoSource = { kind: "youtube"; id: string } | { kind: "file"; url: string } | { kind: "link"; url: string };

export function parseVideo(url: string): VideoSource {
  const youtube = url.match(
    /(?:youtube\.com\/(?:watch\?v=|shorts\/|embed\/)|youtu\.be\/)([A-Za-z0-9_-]{6,})/,
  );
  if (youtube) return { kind: "youtube", id: youtube[1] };
  if (/\.(mp4|webm|m3u8)(\?|$)/i.test(url)) return { kind: "file", url };
  return { kind: "link", url };
}
