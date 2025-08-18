"use client";
import { useState, useMemo, FormEvent, KeyboardEvent } from "react";

type Verse = {
  id: string; chapter: string; verse: string;
  english: string; transliteration: string; sanskrit?: string;
};

export default function Page() {
  const [q,setQ] = useState("");
  const [summary,setSummary] = useState("");
  const [verses,setVerses] = useState<Verse[]>([]);
  const [loading,setLoading] = useState(false);
  const [showSanskrit,setShowSanskrit] = useState<Record<string, boolean>>({});

  const backendUrl = useMemo(() =>
    (process.env.NEXT_PUBLIC_BACKEND_URL as string) || "http://localhost:8000/ask",
  []);

  const ask = async () => {
    if (!q.trim()) return;
    setLoading(true);
    setSummary(""); setVerses([]);
    const r = await fetch(backendUrl, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ query: q.trim() }),
    });
    const data = await r.json();
    setSummary(data.summary || data.answer || "");
    setVerses((data.verses || []).map((v: any) => ({
      id: v.id,
      chapter: v.chapter,
      verse: v.verse,
      english: v.english || v.text || v.transliteration || "",
      transliteration: v.transliteration || "",
      sanskrit: v.sanskrit || ""
    })));
    setLoading(false);
  };

  const onSubmit = (e: FormEvent) => { e.preventDefault(); void ask(); };
  const onKeyDown = (e: KeyboardEvent<HTMLInputElement>) => {
    if (e.key === "Enter") { e.preventDefault(); void ask(); }
  };

  const toggleSanskrit = (id:string) =>
    setShowSanskrit(s => ({...s, [id]: !s[id]}));

  return (
    <div className="min-h-screen peacock-bg">
      {/* center everything vertically */}
      <main className="mx-auto max-w-3xl px-6 flex min-h-screen items-center justify-center">
        <div className="w-full">
          {/* title centered */}
          <header className="text-center mb-8">
            <h1 className="text-5xl md:text-6xl font-extrabold tracking-tight">
              🦚
              <span className="bg-gradient-to-r from-teal-300 via-emerald-400 to-indigo-400 bg-clip-text text-transparent">
                ArjunaAI
              </span>
            </h1>
            <p className="mt-2 text-sm text-white/80">
              Find guidance through the Gita, one question at a time.
            </p>
          </header>

          {/* big centered search bar + Ask ⏎ button inline */}
          <form onSubmit={onSubmit} className="glass rounded-2xl p-3 md:p-4 mb-8">
            <div className="flex items-center gap-2">
              <input
                value={q}
                onChange={e=>setQ(e.target.value)}
                onKeyDown={onKeyDown}
                placeholder="Ask about detachment, duty, devotion… or try 2:47"
                className="w-full rounded-xl border border-white/10 bg-white/5 px-5 py-4 text-lg text-white placeholder-white/60 focus:outline-none focus:ring-2 focus:ring-emerald-300/60"
              />
              <button
                type="submit"
                disabled={loading}
                className="shrink-0 inline-flex items-center gap-2 rounded-xl bg-emerald-400/90 px-5 py-4 text-lg font-semibold text-slate-900 shadow hover:bg-emerald-300 focus:outline-none focus:ring-2 focus:ring-emerald-200 disabled:opacity-60"
                aria-label="Ask"
                title="Ask"
              >
                {loading ? (
                  <>
                    <span className="h-4 w-4 animate-spin rounded-full border-2 border-slate-800 border-t-transparent" />
                    Thinking…
                  </>
                ) : <>Ask <span aria-hidden>⏎</span></>}
              </button>
            </div>
          </form>

          {/* answer */}
          {summary && (
            <section className="glass rounded-2xl p-5 mb-6">
              <h2 className="mb-2 text-lg font-semibold text-emerald-200">Summary</h2>
              <p className="leading-relaxed text-white/90">{summary}</p>
            </section>
          )}

          {/* verses */}
          {verses.length > 0 && (
            <section className="space-y-3">
              <h2 className="px-1 text-lg font-semibold text-emerald-200">Verses</h2>
              <ul className="grid grid-cols-1 gap-3">
                {verses.map(v => (
                  <li key={v.id} className="glass rounded-2xl p-4">
                    <div className="mb-1 font-medium text-white">{v.english}</div>
                    <div className="mb-2 text-xs font-semibold uppercase tracking-wide text-emerald-200/90">
                      Chapter {v.chapter}:{v.verse}
                    </div>
                    {v.transliteration && (
                      <div className="text-sm italic text-white/80">{v.transliteration}</div>
                    )}
                    {v.sanskrit && (
                      <div className="mt-2">
                        <button
                          type="button"
                          onClick={()=>toggleSanskrit(v.id)}
                          className="text-sm text-indigo-200 underline underline-offset-4 hover:text-indigo-100"
                        >
                          {showSanskrit[v.id] ? "Hide Sanskrit" : "Show Sanskrit"}
                        </button>
                        {showSanskrit[v.id] && (
                          <pre className="mt-2 whitespace-pre-wrap text-sm text-white/90">
                            {v.sanskrit}
                          </pre>
                        )}
                      </div>
                    )}
                  </li>
                ))}
              </ul>
            </section>
          )}

          {/* (you removed the “Try …” prompt; we’ll keep the page clean) */}
        </div>
      </main>
    </div>
  );
}
