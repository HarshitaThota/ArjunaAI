"use client";
import { useState } from "react";

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

  const ask = async () => {
    setLoading(true);
    setSummary(""); setVerses([]);
    const backendUrl = (import.meta as any).env?.NEXT_PUBLIC_BACKEND_URL ?? "http://localhost:8000/ask";
    const r = await fetch(
      backendUrl,
      {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ query: q }),
      }
    );
    const data = await r.json();
    setSummary(data.summary || data.answer || "");
    setVerses((data.verses || []).map((v: any) => ({
      id: v.id,
      chapter: v.chapter,
      verse: v.verse,
      english: v.text,
      transliteration: v.transliteration || "",
      sanskrit: v.sanskrit || ""
    })));

    setLoading(false);
  };

  const toggleSanskrit = (id:string) =>
    setShowSanskrit(s => ({...s, [id]: !s[id]}));

  return (
    <main className="p-6 max-w-2xl mx-auto space-y-6">
      <h1 className="text-2xl font-semibold">ArjunaAI</h1>
      <div className="flex gap-2">
        <input
          value={q}
          onChange={e=>setQ(e.target.value)}
          placeholder="Ask about detachment, duty, devotion… or try '2:47'"
          className="border px-3 py-2 flex-1 rounded"
        />
        <button onClick={ask} disabled={loading}
                className="px-4 py-2 bg-black text-white rounded">
          {loading ? "Thinking…" : "Ask"}
        </button>
      </div>

      {summary && (
        <section>
          <h2 className="font-medium mb-1">Summary</h2>
          <p className="leading-relaxed">{summary}</p>
        </section>
      )}

      {verses.length > 0 && (
        <section>
          <h2 className="font-medium mb-2">Verses</h2>
          <ul className="space-y-3">
            {verses.map(v => (
              <li key={v.id} className="border rounded p-3">
                <div className="text-sm opacity-70 mb-1">
                  Chapter {v.chapter}:{v.verse}
                </div>
                <div className="font-medium mb-1">{v.english}</div>
                {v.transliteration && (
                  <div className="text-sm italic opacity-80">{v.transliteration}</div>
                )}
                {v.sanskrit && (
                  <button onClick={()=>toggleSanskrit(v.id)}
                          className="mt-2 text-sm underline">
                    {showSanskrit[v.id] ? "Hide Sanskrit" : "Show Sanskrit"}
                  </button>
                )}
                {v.sanskrit && showSanskrit[v.id] && (
                  <pre className="mt-2 text-sm whitespace-pre-wrap">{v.sanskrit}</pre>
                )}
              </li>
            ))}
          </ul>
        </section>
      )}
    </main>
  );
}
