import React, { useState, useRef, useEffect } from "react";

// WhisperFlow React single-file component
// Usage: paste this into a React app (Vite / CRA). Tailwind CSS classes are used.
// It expects a backend upload endpoint at: POST /upload (multipart form-data, field 'audio', 'language', 'task')

export default function WhisperFlowUI() {
  const [recording, setRecording] = useState(false);
  const [mediaRecorder, setMediaRecorder] = useState(null);
  const [chunks, setChunks] = useState([]);
  const [status, setStatus] = useState("idle");
  const [transcript, setTranscript] = useState("");
  const [summary, setSummary] = useState("");
  const [tasks, setTasks] = useState([]);
  const [notes, setNotes] = useState([]);
  const [language, setLanguage] = useState("auto");
  const [task, setTask] = useState("transcribe");
  const [processing, setProcessing] = useState(false);
  const micRef = useRef(null);
  const streamRef = useRef(null);

  useEffect(() => {
    // try to fetch existing notes (optional endpoint: /list-notes)
    fetch("/list-notes")
      .then((r) => r.json())
      .then((j) => {
        if (Array.isArray(j)) setNotes(j);
      })
      .catch(() => {});
  }, []);

  useEffect(() => {
    // cleanup on unmount
    return () => {
      if (streamRef.current) {
        streamRef.current.getTracks().forEach((t) => t.stop());
      }
    };
  }, []);

  const startRecording = async () => {
    try {
      setStatus("asking-permission");
      const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
      streamRef.current = stream;
      const mr = new MediaRecorder(stream, { mimeType: "audio/webm" });
      const localChunks = [];
      mr.ondataavailable = (e) => {
        if (e.data && e.data.size > 0) localChunks.push(e.data);
      };
      mr.onstart = () => {
        setStatus("recording");
        setChunks([]);
      };
      mr.onstop = async () => {
        setStatus("stopped");
        setChunks(localChunks);
        await sendAudio(localChunks);
        // stop tracks
        stream.getTracks().forEach((t) => t.stop());
        streamRef.current = null;
      };
      setMediaRecorder(mr);
      mr.start();
      setRecording(true);
    } catch (err) {
      console.error(err);
      setStatus("mic-error");
      setRecording(false);
    }
  };

  const stopRecording = () => {
    if (mediaRecorder && mediaRecorder.state === "recording") {
      mediaRecorder.stop();
      setRecording(false);
      setProcessing(true);
      setStatus("processing");
    }
  };

  const sendAudio = async (blobChunks) => {
    setStatus("uploading");
    const blob = new Blob(blobChunks, { type: "audio/webm" });
    const fd = new FormData();
    fd.append("audio", blob, "mic.webm");
    fd.append("language", language);
    fd.append("task", task);

    try {
      const res = await fetch("/upload", { method: "POST", body: fd });
      const j = await res.json();
      if (!res.ok) throw new Error(j.error || "upload failed");

      setTranscript(j.transcript || "");
      setSummary(j.summary || "");
      setTasks(j.tasks || []);
      setStatus("done");
      setProcessing(false);
      // refresh notes list if backend exposes it
      fetch("/list-notes")
        .then((r) => r.json())
        .then((j2) => {
          if (Array.isArray(j2)) setNotes(j2);
        })
        .catch(() => {});
    } catch (err) {
      console.error(err);
      setStatus("error");
      setProcessing(false);
    }
  };

  // Press-and-hold handlers for mouse/touch
  const handleMouseDown = (e) => {
    e.preventDefault();
    startRecording();
  };
  const handleMouseUp = (e) => {
    e.preventDefault();
    stopRecording();
  };

  // keyboard support: Space toggles record
  useEffect(() => {
    const onKey = (e) => {
      if (e.code === "Space" && document.activeElement === document.body) {
        if (!recording) startRecording();
        else stopRecording();
      }
    };
    window.addEventListener("keydown", onKey);
    return () => window.removeEventListener("keydown", onKey);
  }, [recording, mediaRecorder]);

  // small helper: pretty status
  const statusLabel = () => {
    switch (status) {
      case "idle":
        return "Ready";
      case "asking-permission":
        return "Allow microphone";
      case "recording":
        return "Recording…";
      case "processing":
        return "Processing…";
      case "uploading":
        return "Uploading…";
      case "done":
        return "Done";
      case "error":
        return "Error";
      case "mic-error":
        return "Mic access error";
      default:
        return status;
    }
  };

  return (
    <div className="min-h-screen bg-gradient-to-b from-slate-50 to-white p-6">
      <div className="max-w-4xl mx-auto">
        <header className="flex items-center justify-between mb-6">
          <div>
            <h1 className="text-3xl font-extrabold">WhisperFlow — Local</h1>
            <p className="text-sm text-slate-600 mt-1">English & Hindi — press and hold to speak</p>
          </div>
          <div className="text-right">
            <div className="text-xs text-slate-500">Status</div>
            <div className="text-sm font-medium">{statusLabel()}</div>
          </div>
        </header>

        <main className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          {/* Left: controls */}
          <section className="lg:col-span-1 space-y-4">
            <div className="card bg-white rounded-2xl p-4 shadow-sm">
              <label className="block text-xs text-slate-500">Language</label>
              <select
                value={language}
                onChange={(e) => setLanguage(e.target.value)}
                className="mt-2 w-full rounded-md border px-3 py-2"
              >
                <option value="auto">Auto detect</option>
                <option value="en">English</option>
                <option value="hi">Hindi</option>
              </select>

              <label className="block text-xs text-slate-500 mt-3">Output</label>
              <select
                value={task}
                onChange={(e) => setTask(e.target.value)}
                className="mt-2 w-full rounded-md border px-3 py-2"
              >
                <option value="transcribe">Transcript (same language)</option>
                <option value="translate">Translate → English</option>
              </select>

              <div className="mt-4 flex items-center gap-3">
                <button
                  ref={micRef}
                  onMouseDown={handleMouseDown}
                  onMouseUp={handleMouseUp}
                  onTouchStart={handleMouseDown}
                  onTouchEnd={handleMouseUp}
                  className={`flex items-center justify-center w-20 h-20 rounded-full shadow-lg transform transition-all ${
                    recording ? "scale-95 bg-red-600" : "bg-white"
                  }`}
                >
                  <span className={`text-2xl ${recording ? "text-white" : "text-red-600"}`}>
                    🎤
                  </span>
                </button>
                <div>
                  <div className="text-xs text-slate-500">Hold to record</div>
                  <div className="text-sm font-medium">{statusLabel()}</div>
                </div>
              </div>

              <div className="mt-4 text-xs text-slate-500">
                Tip: Click in any text box to place caret — the paste action saves notes on the server and returns results here.
              </div>
            </div>

            <div className="card bg-white rounded-2xl p-4 shadow-sm">
              <h3 className="text-sm font-semibold mb-2">Recent Notes</h3>
              {notes.length === 0 ? (
                <div className="text-xs text-slate-500">No notes yet.</div>
              ) : (
                <ul className="space-y-2 text-sm">
                  {notes.map((n) => (
                    <li key={n} className="text-slate-700">{n}</li>
                  ))}
                </ul>
              )}
            </div>
          </section>

          {/* Right: results */}
          <section className="lg:col-span-2 space-y-4">
            <div className="card bg-white rounded-2xl p-4 shadow-sm">
              <h2 className="text-lg font-semibold mb-2">Summary</h2>
              <div className="min-h-[60px] text-slate-700">{processing ? "Working..." : summary || <span className="text-slate-400">No summary yet.</span>}</div>
            </div>

            <div className="card bg-white rounded-2xl p-4 shadow-sm">
              <h2 className="text-lg font-semibold mb-2">Action Items</h2>
              {tasks.length === 0 ? (
                <div className="text-slate-400">No action items detected.</div>
              ) : (
                <ul className="list-inside list-disc space-y-1">
                  {tasks.map((t, i) => (
                    <li key={i}>{t}</li>
                  ))}
                </ul>
              )}
            </div>

            <div className="card bg-white rounded-2xl p-4 shadow-sm">
              <h2 className="text-lg font-semibold mb-2">Transcript</h2>
              <pre className="whitespace-pre-wrap text-slate-700">{transcript || <span className="text-slate-400">No transcript yet.</span>}</pre>
            </div>
          </section>
        </main>

        <footer className="mt-8 text-center text-xs text-slate-400">Local Whisper • Your machine • No cloud required</footer>
      </div>
    </div>
  );
}
