import { useMemo } from "react";
import { encode } from "uqr";

/**
 * QR code as crisp SVG. Always dark on white with a quiet zone, also in the dark theme:
 * phone cameras read it reliably from a projector or a printed sheet.
 */
export function QrCode({ value, label, className = "qr" }: { value: string; label: string; className?: string }) {
  const { size, path } = useMemo(() => {
    const { data } = encode(value, { ecc: "M", border: 4 });
    let d = "";
    data.forEach((row, y) => {
      // One rectangle per horizontal run of dark modules keeps the path short.
      for (let x = 0; x < row.length; x++) {
        if (!row[x]) continue;
        let run = 1;
        while (row[x + run]) run++;
        d += `M${x} ${y}h${run}v1h-${run}z`;
        x += run;
      }
    });
    return { size: data.length, path: d };
  }, [value]);

  return (
    <svg className={className} viewBox={`0 0 ${size} ${size}`} role="img" aria-label={label} shapeRendering="crispEdges">
      <rect width={size} height={size} fill="#ffffff" />
      <path d={path} fill="#002117" />
    </svg>
  );
}
