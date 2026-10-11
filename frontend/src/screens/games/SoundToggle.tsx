import { Volume2, VolumeX } from "lucide-react";
import { useState } from "react";
import { useTranslation } from "react-i18next";

import { setSoundOn, soundOn } from "../../sound";

/** Speaker button of the games: sounds on or off, remembered on this device. */
export function SoundToggle() {
  const { t } = useTranslation();
  const [on, setOn] = useState(soundOn);
  return (
    <button
      type="button"
      className="icon-button"
      aria-pressed={on}
      aria-label={t(on ? "games.soundOff" : "games.soundOn")}
      onClick={() => {
        setSoundOn(!on);
        setOn(!on);
      }}
    >
      {on ? <Volume2 size={20} /> : <VolumeX size={20} />}
    </button>
  );
}
