/**
 * Shrink a photo on the phone before upload: a 12 Mpx camera picture becomes a few hundred
 * kilobytes, which matters on slow mobile internet (TZ 13). Drawing it on a canvas also drops
 * the camera's metadata; the server cleans it again anyway (it never trusts the client).
 */

const MAX_SIDE = 1600;
const QUALITY = 0.85;
const UPLOADABLE = new Set(["image/jpeg", "image/png", "image/webp"]);
const MAX_RAW_BYTES = 8 * 1024 * 1024;

type Drawable = { source: CanvasImageSource; width: number; height: number; done: () => void };

async function decode(file: Blob): Promise<Drawable> {
  if ("createImageBitmap" in window) {
    try {
      const bitmap = await createImageBitmap(file, { imageOrientation: "from-image" });
      return { source: bitmap, width: bitmap.width, height: bitmap.height, done: () => bitmap.close() };
    } catch {
      // Older WebViews: fall back to an <img>, which also follows the EXIF orientation.
    }
  }
  const url = URL.createObjectURL(file);
  try {
    const image = new Image();
    image.src = url;
    await image.decode();
    return { source: image, width: image.naturalWidth, height: image.naturalHeight, done: () => {} };
  } finally {
    URL.revokeObjectURL(url);
  }
}

export async function shrinkPhoto(file: File): Promise<Blob> {
  let picture: Drawable;
  try {
    picture = await decode(file);
  } catch {
    // Not decodable here (e.g. HEIC on a desktop); the server decides if it can read it.
    if (UPLOADABLE.has(file.type) && file.size <= MAX_RAW_BYTES) return file;
    throw new Error("photo_unreadable");
  }
  const scale = Math.min(1, MAX_SIDE / Math.max(picture.width, picture.height));
  const canvas = document.createElement("canvas");
  canvas.width = Math.max(1, Math.round(picture.width * scale));
  canvas.height = Math.max(1, Math.round(picture.height * scale));
  const context = canvas.getContext("2d");
  if (!context) throw new Error("photo_unreadable");
  context.fillStyle = "#ffffff"; // transparent PNGs get a white background, like on the server
  context.fillRect(0, 0, canvas.width, canvas.height);
  context.drawImage(picture.source, 0, 0, canvas.width, canvas.height);
  picture.done();
  return new Promise((resolve, reject) =>
    canvas.toBlob((blob) => (blob ? resolve(blob) : reject(new Error("photo_unreadable"))), "image/jpeg", QUALITY),
  );
}
