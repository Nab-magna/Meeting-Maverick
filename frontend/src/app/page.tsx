"use client";

import { useState } from "react";
import ReactMarkdown from "react-markdown";
import Image from "next/image";

interface SummaryResponse {
  summary: string;
}

export default function Home() {
  const [transcript, setTranscript] = useState<string>("");
  const [summary, setSummary] = useState<string>("");
  const [loading, setLoading] = useState<boolean>(false);
  const [error, setError] = useState<string | null>("");



  const handleSummarize = async () => {
    if (!transcript.trim()) return;
    setLoading(true);
    setError(null);
    setSummary("");
    try {
      const response = await fetch("http://localhost:8000/summarize", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({ transcript }),
      });
      if (!response.ok) {
        throw new Error("failed to fetch summary");
      }
      const data: SummaryResponse = await response.json();
      setSummary(data.summary);
    } catch (err: any) {
      setError(err.message || "Unknown error occurred");
    } finally {
      setLoading(false);
    }
  };

  const handleExportNotion=()=>{

  };
  const handleExportSlack=()=>{

  };
  const handleExportGmail=()=>{

  };


  return (
    <main className="flex flex-col items-center justify-center min-h-screen px-4 py-6 bg-gray-50">
      <h1 className="text-3xl font-bold mb-6">🎯 Transcript Summarizer</h1>

      <textarea
        value={transcript}
        onChange={(e) => setTranscript(e.target.value)}
        placeholder="Paste your meeting transcript here..."
        className="w-full max-w-3xl h-60 p-4 border border-gray-300 rounded-lg resize-none mb-4"
      />

      <button
        onClick={handleSummarize}
        disabled={loading}
        className="flex items-center justify-center gap-2 bg-blue-600 text-white px-6 py-2 rounded hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed"
      >
        {loading && (
          <svg
            className="w-5 h-5 animate-spin text-white"
            xmlns="http://www.w3.org/2000/svg"
            fill="none"
            viewBox="0 0 24 24"
          >
            <circle
              className="opacity-25"
              cx="12"
              cy="12"
              r="10"
              stroke="currentColor"
              strokeWidth="4"
            />
            <path
              className="opacity-75"
              fill="currentColor"
              d="M4 12a8 8 0 018-8"
              stroke="currentColor"
              strokeWidth="4"
              strokeLinecap="round"
            />
          </svg>
        )}
        {loading ? "Summarizing..." : "Summarize"}
      </button>

      {error && <p className="text-red-600 mt-4">{error}</p>}

      {summary && (
        <div>
          <div className="mt-6 w-full max-w-3xl p-4 bg-white rounded shadow">
            <h2 className="text-xl font-semibold mb-2">📝 Summary</h2>
            <div className="prose max-w-none">
              <ReactMarkdown>{summary}</ReactMarkdown>
            </div>
          </div>
          <div className="mt-8 flex items-center gap-4">
            <h2 className="text-lg font-medium">Export to</h2>

            <button className="flex items-center gap-2 px-4 py-2 bg-blue-600 text-white rounded-lg shadow-sm hover:bg-blue-700 transition"
            onClick={handleExportNotion}>
              <Image
                src="/notion-icon.png"
                alt="Notion"
                width={20}
                height={20}
              />
              Notion
            </button>

            <button className="flex items-center gap-2 px-4 py-2 bg-green-600 text-white rounded-lg shadow-sm hover:bg-green-700 transition"
            onClick={handleExportSlack}>
              <Image src="/slack_icon.png" alt="Slack" width={20} height={20} />
              Slack
            </button>

            <button className="flex items-center gap-2 px-4 py-2 bg-red-600 text-white rounded-lg shadow-sm hover:bg-red-700 transition"
            onClick={handleExportGmail}>
              <Image src="/gmail-icon.jpg" alt="Gmail" width={20} height={20} />
              Email
            </button>
          </div>
        </div>
      )}
    </main>
  );
}
