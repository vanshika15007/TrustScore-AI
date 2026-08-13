import React from "react";
import { motion } from "framer-motion";

function highlightRiskyWords(text, keywords) {
  if (!keywords.length) return text;
  const escaped = keywords.map((keyword) => keyword.replace(/[.*+?^${}()|[\]\\]/g, "\\$&"));
  const pattern = new RegExp(`(${escaped.join("|")})`, "gi");
  return text.split(pattern).map((part, index) => {
    const isRisky = keywords.some((keyword) => keyword.toLowerCase() === part.toLowerCase());
    return isRisky ? (
      <span key={`${part}-${index}`} className="highlight-risk">
        {part}
      </span>
    ) : (
      <React.Fragment key={`${part}-${index}`}>{part}</React.Fragment>
    );
  });
}

function Explanation({ result }) {
  return (
    <motion.div
      className="glass-panel explanation-card hover-lift"
      initial={{ opacity: 0, y: 22 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ delay: 0.08 }}
    >
      <div className="card-head">
        <h3>AI Explanation</h3>
        <span>Why this score was given</span>
      </div>

      <div className="explanation-body">
        <div className="explanation-row">
          <span className="explanation-icon">🧠</span>
          <p>{highlightRiskyWords(result.summary, result.factors.keywords)}</p>
        </div>

        <div className="explanation-row">
          <span className="explanation-icon">🔒</span>
          <p>
            Security posture: <strong>{result.factors.security}</strong>. Content quality:
            {" "}
            <strong>{result.factors.content_quality}</strong>.
          </p>
        </div>

        <div className="explanation-row">
          <span className="explanation-icon">⚠</span>
          <p>
            Risk indicators:{" "}
            {result.factors.keywords.length
              ? result.factors.keywords.join(", ")
              : "No major scam-like phrases were detected."}
          </p>
        </div>
      </div>
    </motion.div>
  );
}

export default Explanation;
