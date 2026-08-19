import { useState, type FC } from "react";
import { RuntimeProvider } from "./RuntimeProvider";
import { Composer, ThreadView } from "./components/Thread";
import { EmailInbox } from "./components/EmailInbox";
import ApiKeyGate from "./components/ApiKeyGate";
import { MicronMark } from "./components/MicronMark";
import { isLocalDev, resolveApiKey, saveApiKey } from "./lib/auth";

const Header: FC = () => (
  <header className="header-blur sticky top-0 z-30 flex items-center justify-between border-b border-[var(--border)] px-4 py-3 sm:px-6">
    <div className="flex items-center gap-3">
      <MicronMark className="h-6 w-auto shrink-0" />
      <div className="h-6 w-px shrink-0 bg-[var(--border)]" />
      <div>
        <h1 className="text-sm font-semibold tracking-tight">
          Back-Office Document Agent
        </h1>
        <p className="text-xs text-[var(--muted-foreground)]">
          Email intake -&gt; shipping orders, purchase orders, invoices, remittance advice
        </p>
      </div>
    </div>
    <span className="hidden items-center gap-1.5 rounded-full border border-[var(--border)] bg-[var(--surface)] px-2.5 py-1 text-xs text-[var(--muted-foreground)] sm:inline-flex">
      <span className="h-1.5 w-1.5 rounded-full bg-[var(--accent)] shadow-[0_0_8px_var(--accent)]" />
      LangSmith Engine demo
    </span>
  </header>
);

export default function App() {
  const [apiKey, setApiKey] = useState<string | null>(() => resolveApiKey());

  // On a real deployment we need a key before the SDK calls will work.
  // On localhost the agent server uses no-op auth, so an empty key is fine.
  if (apiKey === null && !isLocalDev()) {
    return (
      <ApiKeyGate
        onSubmit={(key) => {
          saveApiKey(key);
          setApiKey(key);
        }}
      />
    );
  }

  return (
    <RuntimeProvider assistantId="agent" apiKey={apiKey}>
      <div className="flex h-dvh flex-col bg-[var(--background)]">
        <Header />
        <div className="flex min-h-0 flex-1">
          <EmailInbox />
          <div className="flex min-h-0 flex-1 flex-col">
            <ThreadView />
            <Composer />
          </div>
        </div>
      </div>
    </RuntimeProvider>
  );
}
