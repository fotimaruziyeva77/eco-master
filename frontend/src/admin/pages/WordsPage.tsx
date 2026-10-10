import { Plus, X } from "lucide-react";
import { useState, type FormEvent } from "react";

import { useLoad } from "../../hooks/useLoad";
import { adminApi, errorText, type Word, type WordKind } from "../api";
import { LoadError, Loading, PageHead, useToast } from "../ui";

const KINDS: { kind: WordKind; title: string; help: string }[] = [
  {
    kind: "profanity",
    title: "Odobsiz so'zlar",
    help: "Taxallusning istalgan joyida bo'lsa rad etiladi (uch tilda, raqam bilan almashtirilgan harflar ham).",
  },
  {
    kind: "reserved",
    title: "Band taxalluslar",
    help: "Taxallus shu so'z bilan boshlansa yoki tugasa rad etiladi (admin, moderator, ekoustoz…).",
  },
];

/** Profanity and reserved names (TZ 8.1, 8.12). Applies to new nicknames right away. */
export function WordsPage() {
  const words = useLoad(() => adminApi.words(), []);
  return (
    <>
      <PageHead title="So'zlar ro'yxati" />
      {words.loading && !words.data && <Loading />}
      {words.error !== undefined && !words.data && <LoadError error={words.error} onRetry={words.reload} />}
      {words.data && (
        <div className="a-grid-2">
          {KINDS.map((k) => (
            <WordList key={k.kind} {...k} words={words.data!.filter((w) => w.kind === k.kind)} onChange={words.reload} />
          ))}
        </div>
      )}
    </>
  );
}

function WordList({
  kind,
  title,
  help,
  words,
  onChange,
}: {
  kind: WordKind;
  title: string;
  help: string;
  words: Word[];
  onChange: () => void;
}) {
  const toast = useToast();
  const [value, setValue] = useState("");
  const [filter, setFilter] = useState("");

  async function add(e: FormEvent) {
    e.preventDefault();
    try {
      await adminApi.addWord(value, kind);
      setValue("");
      onChange();
    } catch (err) {
      toast(errorText(err));
    }
  }

  async function remove(word: Word) {
    try {
      await adminApi.deleteWord(word.id);
      toast(`«${word.word}» o'chirildi`);
      onChange();
    } catch (err) {
      toast(errorText(err));
    }
  }

  const shown = words.filter((w) => w.word.includes(filter.trim().toLowerCase()));
  return (
    <section className="a-card">
      <h2>
        {title} <span className="a-muted a-small">({words.length})</span>
      </h2>
      <p className="a-help" style={{ marginBottom: 12 }}>
        {help}
      </p>
      <form className="a-row" style={{ marginBottom: 12, flexWrap: "nowrap" }} onSubmit={(e) => void add(e)}>
        <input className="a-input" placeholder="Yangi so'z" value={value} maxLength={64} onChange={(e) => setValue(e.target.value)} />
        <button type="submit" className="a-btn" disabled={value.trim().length < 2}>
          <Plus size={16} /> Qo'shish
        </button>
      </form>
      {words.length > 20 && (
        <input className="a-input" style={{ marginBottom: 10 }} placeholder="Ro'yxatdan qidirish" value={filter} onChange={(e) => setFilter(e.target.value)} />
      )}
      <div className="a-chips">
        {shown.map((w) => (
          <span key={w.id} className="a-word">
            {w.word}
            <button type="button" onClick={() => void remove(w)} aria-label={`${w.word} — o'chirish`}>
              <X size={13} />
            </button>
          </span>
        ))}
        {shown.length === 0 && <span className="a-muted a-small">Bo'sh</span>}
      </div>
    </section>
  );
}
