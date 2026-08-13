import React from "react";
import { motion } from "framer-motion";

function AnalyzerForm({ url, setUrl, onAnalyze, loading, urlIsValid }) {
  return (
    <motion.section
      className="glass-panel control-panel"
      initial={{ opacity: 0, y: 24 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ delay: 0.1 }}
    >
      <div className="panel-header">
        <div>
          <span className="panel-kicker">Smart URL Scanner</span>
          <h2>Paste a website and watch the trust analysis unfold step by step</h2>
        </div>
        <span className={`live-pill ${url.trim() ? "ready" : ""}`}>{url.trim() ? "Ready" : "Idle"}</span>
      </div>

      <div className="input-row">
        <input
          type="text"
          value={url}
          placeholder="https://amazon.com or stripe.com"
          onChange={(event) => setUrl(event.target.value)}
          onKeyDown={(event) => {
            if (event.key === "Enter" && !loading) onAnalyze();
          }}
          className={!urlIsValid ? "input-invalid" : ""}
          aria-invalid={!urlIsValid}
        />
        <motion.button
          type="button"
          className="scan-button"
          onClick={() => onAnalyze()}
          whileHover={{ scale: 1.03, boxShadow: "0 0 30px rgba(29, 242, 195, 0.35)" }}
          whileTap={{ scale: 0.98 }}
          disabled={loading}
        >
          {loading ? (
            <span className="button-loading">
              <span className="button-spinner" />
              Scanning
            </span>
          ) : (
            "Start Analysis"
          )}
        </motion.button>
      </div>
    </motion.section>
  );
}

export default AnalyzerForm;
