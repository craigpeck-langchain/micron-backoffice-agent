import { useMemo, useState, type FC } from "react";
import { useComposerRuntime } from "@assistant-ui/react";
import { SAMPLE_EMAILS, type SampleEmail } from "../data/sampleEmails.generated";

const DOC_TYPE_LABELS: Record<string, string> = {
  shipping_order: "Shipping orders",
  purchase_order: "Purchase orders",
  invoice: "Invoices",
  remittance_advice: "Remittance advice",
  out_of_scope: "Out of scope",
};

const DOC_TYPE_ORDER = ["shipping_order", "purchase_order", "invoice", "remittance_advice", "out_of_scope"];

const groupByDocType = (emails: SampleEmail[]) => {
  const groups = new Map<string, SampleEmail[]>();
  for (const email of emails) {
    const key = email.docTypeExpected;
    if (!groups.has(key)) groups.set(key, []);
    groups.get(key)!.push(email);
  }
  return DOC_TYPE_ORDER.filter((k) => groups.has(k)).map((k) => ({
    docType: k,
    label: DOC_TYPE_LABELS[k] ?? k,
    emails: groups.get(k)!,
  }));
};

type Filter = "all" | "flaws";

const EmailRow: FC<{ email: SampleEmail; onSend: (email: SampleEmail) => void }> = ({ email, onSend }) => (
  <button
    onClick={() => onSend(email)}
    className="w-full rounded-lg border border-transparent px-2.5 py-2 text-left transition-colors hover:border-[var(--border)] hover:bg-[var(--surface-hover)]"
  >
    <div className="flex items-start justify-between gap-2">
      <span className="line-clamp-1 text-xs font-medium text-[var(--foreground)]">{email.subject}</span>
    </div>
    <div className="mt-0.5 flex items-center gap-1.5">
      <span className="line-clamp-1 text-[11px] text-[var(--muted-foreground)]">{email.from}</span>
      {email.plantedFlaw && <span className="flaw-badge shrink-0">flaw</span>}
    </div>
  </button>
);

/**
 * Sidebar listing the synthetic fixture emails so a presenter can click one
 * instead of typing - fills the composer via useComposerRuntime and sends
 * immediately. Source data is generated from fixtures/emails/*.json by
 * scripts/export_frontend_emails.py.
 */
export const EmailInbox: FC = () => {
  const composerRuntime = useComposerRuntime();
  const [filter, setFilter] = useState<Filter>("all");

  const visible = useMemo(
    () => (filter === "flaws" ? SAMPLE_EMAILS.filter((e) => e.plantedFlaw) : SAMPLE_EMAILS),
    [filter],
  );
  const groups = useMemo(() => groupByDocType(visible), [visible]);

  const handleSend = (email: SampleEmail) => {
    composerRuntime.setText(email.text);
    composerRuntime.send();
  };

  return (
    <aside className="hidden w-72 shrink-0 flex-col border-r border-[var(--border)] bg-[var(--background-elevated)] lg:flex">
      <div className="flex items-center justify-between border-b border-[var(--border)] px-3 py-2.5">
        <h2 className="text-xs font-semibold uppercase tracking-wide text-[var(--muted-foreground)]">
          Sample inbox
        </h2>
        <div className="flex gap-1 rounded-full bg-[var(--muted)] p-0.5 text-[10px] font-medium">
          <button
            onClick={() => setFilter("all")}
            className={`rounded-full px-2 py-0.5 transition-colors ${filter === "all" ? "bg-[var(--surface)] text-[var(--foreground)] shadow-sm" : "text-[var(--muted-foreground)]"}`}
          >
            All
          </button>
          <button
            onClick={() => setFilter("flaws")}
            className={`rounded-full px-2 py-0.5 transition-colors ${filter === "flaws" ? "bg-[var(--surface)] text-[var(--foreground)] shadow-sm" : "text-[var(--muted-foreground)]"}`}
          >
            Flaws
          </button>
        </div>
      </div>
      <div className="flex-1 overflow-y-auto px-2 py-2">
        {groups.map((group) => (
          <div key={group.docType} className="mb-3">
            <h3 className="px-2 py-1 text-[10px] font-semibold uppercase tracking-wide text-[var(--muted-foreground)]">
              {group.label}
            </h3>
            <div className="flex flex-col gap-0.5">
              {group.emails.map((email) => (
                <EmailRow key={email.id} email={email} onSend={handleSend} />
              ))}
            </div>
          </div>
        ))}
      </div>
    </aside>
  );
};
