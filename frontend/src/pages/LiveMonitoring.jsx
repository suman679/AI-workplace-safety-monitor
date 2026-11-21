import { Play, Square } from "lucide-react";
import { useCallback, useEffect, useRef, useState } from "react";
import { ModelBanner, SiteRulesSelect, SummaryCards } from "../components/DetectionBits";
import { Banner, PageHeader, SelectField } from "../components/ui";
import useFetch from "../hooks/useFetch";
import usePermissions from "../hooks/usePermissions";
import { tokenStore } from "../services/api";

const WS_BASE = import.meta.env.VITE_API_URL.replace(/^http/, "ws");
const COLORS = { SAFE: "#34d399", WARNING: "#fbbf24", VIOLATION: "#f87171" };
const CLOSE_MESSAGES = { 4401: "Authentication expired. Please log in again.", 4403: "Your role cannot run live monitoring.", 4404: "Site or camera not found.", 1011: "Live detection failed." };

export default function LiveMonitoring() {
  const { data: sites } = useFetch("/api/sites");
  const [siteId, setSiteId] = useState("");
  const [cameraId, setCameraId] = useState("");
  const { data: cameras } = useFetch("/api/cameras", { site_id: siteId || undefined });
  const { canWrite } = usePermissions();

  const [running, setRunning] = useState(false);
  const [error, setError] = useState("");
  const [aspect, setAspect] = useState(16 / 9);
  const [stats, setStats] = useState(null);
  const [fps, setFps] = useState(0);
  const [lastViolation, setLastViolation] = useState(null);

  const videoRef = useRef(null);
  const overlayRef = useRef(null);
  const captureRef = useRef(document.createElement("canvas"));
  const wsRef = useRef(null);
  const streamRef = useRef(null);
  const runningRef = useRef(false);
  const times = useRef([]);

  const stop = useCallback(() => {
    runningRef.current = false;
    wsRef.current?.close();
    wsRef.current = null;
    streamRef.current?.getTracks().forEach((t) => t.stop());
    streamRef.current = null;
    if (videoRef.current) videoRef.current.srcObject = null;
    const c = overlayRef.current;
    c?.getContext("2d").clearRect(0, 0, c.width, c.height);
    setRunning(false);
    setFps(0);
  }, []);

  useEffect(() => stop, [stop]);

  function draw(msg) {
    const video = videoRef.current;
    const canvas = overlayRef.current;
    if (!video || !canvas) return;
    canvas.width = video.clientWidth;
    canvas.height = video.clientHeight;
    const ctx = canvas.getContext("2d");
    ctx.clearRect(0, 0, canvas.width, canvas.height);
    const px = (b) => [b[0] * canvas.width, b[1] * canvas.height, (b[2] - b[0]) * canvas.width, (b[3] - b[1]) * canvas.height];
    ctx.lineWidth = 1;
    ctx.strokeStyle = "#38bdf8";
    msg.ppe_detections.forEach((d) => ctx.strokeRect(...px(d.box)));
    ctx.font = "13px Inter, sans-serif";
    msg.persons.forEach((p) => {
      const [x, y, w, h] = px(p.box);
      const color = COLORS[p.state];
      ctx.lineWidth = 3;
      ctx.strokeStyle = color;
      ctx.strokeRect(x, y, w, h);
      const label = `#${p.person_id} ${Math.round(p.confidence * 100)}%${p.violations.length ? " | " + p.violations.join(", ") : ""}`;
      const tw = ctx.measureText(label).width + 10;
      ctx.fillStyle = color;
      ctx.fillRect(x, Math.max(0, y - 22), tw, 22);
      ctx.fillStyle = "#0b111b";
      ctx.fillText(label, x + 5, Math.max(16, y - 6));
    });
  }

  function onResult(msg) {
    draw(msg);
    setStats(msg.summary);
    const now = performance.now();
    times.current = [...times.current.filter((t) => now - t < 1000), now];
    setFps(times.current.length);
    const bad = msg.persons.find((p) => p.violations.length);
    if (bad) setLastViolation({ text: `Worker #${bad.person_id}: ${bad.violations.join(", ")}`, time: new Date().toLocaleTimeString() });
  }

  function sendFrame() {
    const ws = wsRef.current;
    const video = videoRef.current;
    if (!runningRef.current || !ws || ws.readyState !== WebSocket.OPEN) return;
    if (!video.videoWidth) return void setTimeout(sendFrame, 100);
    const cap = captureRef.current;
    const scale = Math.min(1, 640 / video.videoWidth);
    cap.width = Math.round(video.videoWidth * scale);
    cap.height = Math.round(video.videoHeight * scale);
    cap.getContext("2d").drawImage(video, 0, 0, cap.width, cap.height);
    cap.toBlob((blob) => blob && ws.readyState === WebSocket.OPEN && ws.send(blob), "image/jpeg", 0.7);
  }

  async function start() {
    setError("");
    setStats(null);
    let stream;
    try {
      stream = await navigator.mediaDevices.getUserMedia({ video: { width: { ideal: 960 }, height: { ideal: 540 } }, audio: false });
    } catch {
      setError("Camera access was blocked or no camera was found.");
      return;
    }
    streamRef.current = stream;
    const video = videoRef.current;
    video.srcObject = stream;
    await video.play().catch(() => {});
    if (video.videoWidth) setAspect(video.videoWidth / video.videoHeight);

    const params = new URLSearchParams({ token: tokenStore.get()?.access_token || "" });
    if (siteId) params.set("site_id", siteId);
    if (cameraId) params.set("camera_id", cameraId);
    const ws = new WebSocket(`${WS_BASE}/ws/detect?${params}`);
    wsRef.current = ws;
    runningRef.current = true;
    ws.onopen = () => { setRunning(true); sendFrame(); };
    ws.onmessage = (ev) => {
      const msg = JSON.parse(ev.data);
      if (msg.error) setError(msg.error);
      else onResult(msg);
      sendFrame();
    };
    ws.onerror = () => setError((e) => e || "Unable to connect to AI server.");
    ws.onclose = (ev) => {
      if (!runningRef.current) return;
      setError((e) => e || CLOSE_MESSAGES[ev.code] || "Connection to the AI server was lost.");
      stop();
    };
  }

  const webcams = cameras?.filter((c) => c.source_type === "WEBCAM") || [];
  return (
    <div>
      <PageHeader title="Live Monitoring" subtitle="Real-time PPE detection from your webcam" />
      <ModelBanner />
      <Banner>{error}</Banner>
      {!canWrite && <Banner tone="amber">Your role cannot run live monitoring.</Banner>}
      <div className="card mb-5 grid items-end gap-4 p-5 md:grid-cols-[1fr_1fr_auto]">
        <SiteRulesSelect sites={sites} value={siteId} onChange={(v) => { setSiteId(v); setCameraId(""); }} SelectField={SelectField} />
        <SelectField label="Camera (optional, marked online while running)" value={cameraId} onChange={(e) => setCameraId(e.target.value)} disabled={running}>
          <option value="">No camera record</option>
          {webcams.map((c) => <option key={c.id} value={c.id}>{c.name} ({c.camera_code})</option>)}
        </SelectField>
        {running
          ? <button className="btn-danger" onClick={stop}><Square size={16} /> Stop camera</button>
          : <button className="btn-accent" onClick={start} disabled={!canWrite}><Play size={16} /> Start camera</button>}
      </div>

      <div className="grid gap-5 xl:grid-cols-[1fr_320px]">
        <div className="card overflow-hidden p-2">
          <div className="relative mx-auto w-full max-w-4xl bg-black" style={{ aspectRatio: aspect }}>
            <video ref={videoRef} muted playsInline onLoadedMetadata={(e) => setAspect(e.target.videoWidth / e.target.videoHeight)} className="absolute inset-0 h-full w-full" />
            <canvas ref={overlayRef} className="pointer-events-none absolute inset-0 h-full w-full" />
            {!running && <div className="absolute inset-0 grid place-items-center text-sm text-slate-500">Camera is off</div>}
          </div>
        </div>
        <div className="space-y-3">
          <SummaryCards items={[
            { label: "Workers", value: stats?.workers },
            { label: "Compliant", value: stats?.compliant, tone: "text-emerald-400" },
            { label: "Violations", value: stats?.violations, tone: stats?.violations ? "text-red-400" : undefined },
            { label: "Safety score", value: stats?.safety_score == null ? null : `${stats.safety_score}%` },
            { label: "FPS", value: running ? fps : null },
          ]} />
          <div className="card p-4">
            <div className="text-xs text-slate-400">Last violation</div>
            <div className="mt-1 text-sm text-white">{lastViolation ? lastViolation.text : "None yet"}</div>
            {lastViolation && <div className="text-xs text-slate-500">{lastViolation.time}</div>}
          </div>
        </div>
      </div>
    </div>
  );
}

