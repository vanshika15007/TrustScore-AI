import React, { useEffect, useMemo, useRef, useState } from "react";
import axios from "axios";
import { AnimatePresence } from "framer-motion";
import Hero from "./components/Hero";
import AnalyzerForm from "./components/AnalyzerForm";
import Loader from "./components/Loader";
import StatusTracker from "./components/StatusTracker";
import ScoreCircle from "./components/ScoreCircle";
import Charts from "./components/Charts";
import Explanation from "./components/Explanation";
import ErrorCard from "./components/ErrorCard";
import "./App.css";

const API_BASE = import.meta.env.VITE_API_BASE_URL ?? "http://127.0.0.1:8000";
const REQUEST_TIMEOUT_MS = 15000;
const LOADING_STEPS = [
  { label: "Scraping website", status: "Render and extract visible content" },
  { label: "Running AI model", status: "Analyzing chunked text with BERT" },
  { label: "Calculating trust score", status: "Combining risk, security, and quality" },
];

function normalizeUrl(value) {
  const trimmed = value.trim();
  if (!trimmed) return "";
  if (/^https?:\/\//i.test(trimmed)) return trimmed;
  return `https://${trimmed}`;
}

function isValidUrl(value) {
  if (!value.trim()) return true;
  try {
    const normalized = normalizeUrl(value);
    const parsed = new URL(normalized);
    return Boolean(parsed.hostname);
  } catch {
    return false;
  }
}

function formatBackendError(err) {
  if (err.code === "ECONNABORTED") {
    return "The request timed out. Try again or scan a lighter page.";
  }

  if (err.response?.data?.detail) {
    return err.response.data.detail;
  }

  if (err.message?.includes("Network Error")) {
    return "Could not reach the backend. Start FastAPI and try again.";
  }

  return err.message || "Something went wrong while scanning the website.";
}

function buildSuggestions(errorMessage) {
  const lowered = (errorMessage || "").toLowerCase();
  if (lowered.includes("blocked") || lowered.includes("low content")) {
    return ["wikipedia.org", "amazon.com", "stripe.com"];
  }
  return ["example.com", "openai.com", "github.com"];
}

function trustLabel(score) {
  if (score >= 75) return "Trusted";
  if (score >= 45) return "Medium";
  return "Risky";
}

function successTone() {
  try {
    const AudioContextClass = window.AudioContext || window.webkitAudioContext;
    if (!AudioContextClass) return;

    const audioContext = new AudioContextClass();
    const oscillator = audioContext.createOscillator();
    const gain = audioContext.createGain();

    oscillator.type = "sine";
    oscillator.frequency.setValueAtTime(740, audioContext.currentTime);
    gain.gain.setValueAtTime(0.0001, audioContext.currentTime);
    gain.gain.exponentialRampToValueAtTime(0.08, audioContext.currentTime + 0.01);
    gain.gain.exponentialRampToValueAtTime(0.0001, audioContext.currentTime + 0.25);

    oscillator.connect(gain);
    gain.connect(audioContext.destination);
    oscillator.start();
    oscillator.stop(audioContext.currentTime + 0.25);
  } catch {
    // Ignore audio failures to keep the scan flow smooth.
  }
}

function App() {
  const [url, setUrl] = useState("");
  const [backendStatus, setBackendStatus] = useState("checking");
  const [loading, setLoading] = useState(false);
  const [loadingStep, setLoadingStep] = useState(0);
  const [taskStatus, setTaskStatus] = useState("idle");
  const [result, setResult] = useState(null);
  const [error, setError] = useState("");
  const [taskId, setTaskId] = useState("");
  const [lastScannedUrl, setLastScannedUrl] = useState("");
  const pollingRef = useRef(null);

  const urlIsValid = isValidUrl(url);
  const suggestions = useMemo(() => buildSuggestions(error), [error]);

  useEffect(() => {
    let active = true;

    async function checkBackend() {
      try {
        await axios.get(`${API_BASE}/health`, { timeout: 5000 });
        if (active) setBackendStatus("online");
      } catch {
        if (active) setBackendStatus("offline");
      }
    }

    checkBackend();
    const intervalId = window.setInterval(checkBackend, 15000);

    return () => {
      active = false;
      window.clearInterval(intervalId);
    };
  }, []);

  useEffect(() => {
    if (!loading) return undefined;

    const intervalId = window.setInterval(() => {
      setLoadingStep((current) => (current + 1) % LOADING_STEPS.length);
    }, 1600);

    return () => window.clearInterval(intervalId);
  }, [loading]);

  useEffect(() => () => {
    if (pollingRef.current) {
      window.clearTimeout(pollingRef.current);
    }
  }, []);

  async function pollTask(nextTaskId) {
    try {
      const response = await axios.get(`${API_BASE}/status/${nextTaskId}`, {
        timeout: REQUEST_TIMEOUT_MS,
      });

      const payload = response.data;
      setTaskStatus(payload.task_status);

      if (payload.task_status === "completed" && payload.result) {
        setLoading(false);
        setResult(payload.result);
        setError("");
        successTone();
        return;
      }

      if (payload.task_status === "failed") {
        setLoading(false);
        setError(payload.error || "The scan failed.");
        return;
      }

      pollingRef.current = window.setTimeout(() => {
        pollTask(nextTaskId);
      }, 1800);
    } catch (err) {
      setLoading(false);
      setError(formatBackendError(err));
    }
  }

  async function analyze(nextUrl = url) {
    const preparedUrl = normalizeUrl(nextUrl);
    if (!preparedUrl || !isValidUrl(nextUrl)) {
      setError("Enter a valid website URL before scanning.");
      return;
    }

    if (pollingRef.current) {
      window.clearTimeout(pollingRef.current);
    }

    setLoading(true);
    setLoadingStep(0);
    setTaskStatus("pending");
    setTaskId("");
    setError("");
    setResult(null);
    setLastScannedUrl(preparedUrl);

    try {
      const response = await axios.post(
        `${API_BASE}/analyze`,
        { url: preparedUrl },
        { timeout: REQUEST_TIMEOUT_MS },
      );

      setTaskId(response.data.task_id);
      setTaskStatus(response.data.cached ? "completed" : "processing");
      pollTask(response.data.task_id);
    } catch (err) {
      setLoading(false);
      setError(formatBackendError(err));
    }
  }

  return (
    <div className="app-shell">
      <div className="bg-grid" />
      <div className="glow glow-left" />
      <div className="glow glow-right" />
      <div className="particle-field" aria-hidden="true">
        {Array.from({ length: 18 }).map((_, index) => (
          <span key={index} className={`particle particle-${(index % 6) + 1}`} />
        ))}
      </div>

      <Hero backendStatus={backendStatus} taskStatus={taskStatus} />

      <AnalyzerForm
        url={url}
        setUrl={setUrl}
        onAnalyze={analyze}
        loading={loading}
        urlIsValid={urlIsValid}
      />

      <StatusTracker taskId={taskId} taskStatus={taskStatus} backendStatus={backendStatus} />

      <AnimatePresence mode="wait">
        {loading ? <Loader steps={LOADING_STEPS} activeStep={loadingStep} /> : null}

        {!loading && error ? (
          <ErrorCard
            error={error}
            suggestions={suggestions}
            onRetry={lastScannedUrl ? () => analyze(lastScannedUrl) : null}
            onSuggestionClick={setUrl}
          />
        ) : null}

        {!loading && result ? (
          <div className="results">
            <div className="results-grid">
              <ScoreCircle result={result} verdict={trustLabel(result.trust_score)} />
              <Explanation result={result} />
            </div>
            <Charts result={result} />
          </div>
        ) : null}
      </AnimatePresence>
    </div>
  );
}

export default App;
