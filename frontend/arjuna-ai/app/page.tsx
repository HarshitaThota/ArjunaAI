"use client";
import { useState } from "react";

export default function Page() {
  const [q,setQ] = useState("");
  const [resp,setResp] = useState<any>(null);
  const ask = async () => {
    const r = await fetch("http://localhost:8000/ask", {
      method:"POST",
      headers:{"Content-Type":"application/json"},
      body: JSON.stringify({ query: q })
    });
    setResp(await r.json());
  };
  return (
    <main className="p-6 max-w-3xl mx-auto">
      <h1 className="text-2xl font-semibold mb-4">Bhagavad Gita Q&A</h1>
      <div className="flex gap-2 mb-4">
        <input className="border px-3 py-2 flex-1" value={q} onChange={e=>setQ(e.target.value)} placeholder="Ask about detachment, duty, devotion..." />
        <button className="px-4 py-2 bg-black text-white" onClick={ask}>Ask</button>
      </div>

      {resp && (
        <div className="space-y-4">
          <div>
            <h2 className="font-medium">Answer</h2>
            <p className="mt-1 whitespace-pre-wrap">{resp.answer}</p>
            <div className="text-sm opacity-70 mt-1">Confidence: {(resp.confidence*100).toFixed(0)}%</div>
          </div>
          <div>
            <h2 className="font-medium">Supporting Verses</h2>
            <ul className="list-disc ml-6">
              {resp.verses?.map((v:any)=>(
                <li key={v.id}><b>{v.id}</b>: {v.text}</li>
              ))}
            </ul>
          </div>
        </div>
      )}
    </main>
  );
}
