import { FileText, ShieldCheck, type LucideIcon } from "lucide-react";
import { useTranslation } from "react-i18next";

import { SubpageHeader } from "../components/ui";
import { useBack } from "../hooks/useBack";

const DOCUMENTS = {
  privacy: {
    icon: ShieldCheck,
    sections: ["collect", "notCollect", "why", "who", "classes", "market", "delete", "contact"],
  },
  terms: {
    icon: FileText,
    sections: ["about", "who", "safety", "nickname", "points", "market", "content", "changes", "contact"],
  },
} satisfies Record<string, { icon: LucideIcon; sections: string[] }>;

export type LegalDocumentKind = keyof typeof DOCUMENTS;

/**
 * Draft privacy notice (TZ 11.2) and terms of use (TZ 8.1, 9.1). The final texts come after
 * the legal review (TZ 11.4).
 */
export function LegalContent({ kind }: { kind: LegalDocumentKind }) {
  const { t } = useTranslation();
  const { icon: Icon, sections } = DOCUMENTS[kind];
  return (
    <article className="stack">
      <h1 className="row">
        <Icon size={26} aria-hidden="true" /> {t(`${kind}.title`)}
      </h1>
      <p className="note">{t(`${kind}.draft`)}</p>
      {sections.map((section) => (
        <section key={section} className="card stack" style={{ gap: 6 }}>
          <h3>{t(`${kind}.${section}Title`)}</h3>
          <p className="text-2">{t(`${kind}.${section}Text`)}</p>
        </section>
      ))}
    </article>
  );
}

function LegalScreen({ kind }: { kind: LegalDocumentKind }) {
  const { t } = useTranslation();
  const back = useBack("/profile");
  return (
    <main className="screen">
      <SubpageHeader onBack={back} title={t(`profile.${kind}`)} />
      <LegalContent kind={kind} />
    </main>
  );
}

export const PrivacyScreen = () => <LegalScreen kind="privacy" />;
export const TermsScreen = () => <LegalScreen kind="terms" />;
