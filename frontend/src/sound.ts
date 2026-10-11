/**
 * Short game sounds made by the Web Audio API: no sound files to download. Off with the
 * speaker button in the games; the choice stays on this device.
 */

const OFF_KEY = "ekoustoz.sound.off";

let context: AudioContext | null = null;

export function soundOn(): boolean {
  try {
    return localStorage.getItem(OFF_KEY) !== "1";
  } catch {
    return true;
  }
}

export function setSoundOn(on: boolean): void {
  try {
    if (on) localStorage.removeItem(OFF_KEY);
    else localStorage.setItem(OFF_KEY, "1");
  } catch {
    // Private mode: the choice lasts until the app is closed.
  }
}

function audio(): AudioContext | null {
  if (!soundOn()) return null;
  try {
    const Context = window.AudioContext ?? (window as unknown as { webkitAudioContext?: typeof AudioContext }).webkitAudioContext;
    if (!Context) return null;
    context ??= new Context();
    if (context.state === "suspended") void context.resume();
    return context;
  } catch {
    return null;
  }
}

/** One note: frequency in Hz, start and length in seconds from now. */
function note(ctx: AudioContext, frequency: number, start: number, length: number, type: OscillatorType = "sine", volume = 0.14) {
  const osc = ctx.createOscillator();
  const gain = ctx.createGain();
  const at = ctx.currentTime + start;
  osc.type = type;
  osc.frequency.setValueAtTime(frequency, at);
  gain.gain.setValueAtTime(0.0001, at);
  gain.gain.exponentialRampToValueAtTime(volume, at + 0.015);
  gain.gain.exponentialRampToValueAtTime(0.0001, at + length);
  osc.connect(gain).connect(ctx.destination);
  osc.start(at);
  osc.stop(at + length + 0.02);
}

export const sound = {
  /** Two quick rising notes. */
  correct() {
    const ctx = audio();
    if (!ctx) return;
    note(ctx, 660, 0, 0.12);
    note(ctx, 990, 0.09, 0.18);
  },
  /** A short low buzz. */
  wrong() {
    const ctx = audio();
    if (!ctx) return;
    note(ctx, 196, 0, 0.22, "triangle", 0.16);
    note(ctx, 147, 0.12, 0.26, "triangle", 0.14);
  },
  /** A little fanfare for a finished round or a new level. */
  fanfare() {
    const ctx = audio();
    if (!ctx) return;
    [523, 659, 784, 1047].forEach((f, i) => note(ctx, f, i * 0.11, 0.24, "triangle", 0.12));
  },
};
