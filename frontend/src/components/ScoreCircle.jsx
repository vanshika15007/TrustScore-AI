import React, { useEffect, useMemo, useState } from "react";
import { motion } from "framer-motion";

function toneForScore(score) {
  if (score >= 75) return "safe";
  if (score >= 45) return "medium";
  return "risky";
}

function ScoreCircle({ result, verdict }) {
  const [displayScore, setDisplayScore] = useState(0);
  const score = Math.round(result.trust_score);
  const tone = toneForScore(score);
  const ringOffset = 408 - (408 * score) / 100;
  const needleRotation = -90 + (180 * score) / 100;

  useEffect(() => {
    let frameId;
    const startedAt = performance.now();
    const duration = 1200;

    const tick = (timestamp) => {
      const progress = Math.min((timestamp - startedAt) / duration, 1);
      setDisplayScore(Math.round(score * progress));
      if (progress < 1) {
        frameId = window.requestAnimationFrame(tick);
      }
    };

    frameId = window.requestAnimationFrame(tick);
    return () => window.cancelAnimationFrame(frameId);
  }, [score]);

  const toneLabel = useMemo(() => tone, [tone]);

  return (
    <motion.div
      className={`glass-panel score-card tone-${toneLabel}`}
      initial={{ opacity: 0, y: 22 }}
      animate={{ opacity: 1, y: 0 }}
    >
      <div className="score-card-head">
        <div>
          <span className="panel-kicker">Trust Score</span>
          <h3>{verdict}</h3>
        </div>
        <span className={`score-chip score-chip-${toneLabel}`}>{result.risk_level} Risk</span>
      </div>

      <div className="score-visuals">
        <div className="score-circle-card">
          <svg viewBox="0 0 160 160" className="score-ring">
            <defs>
              <linearGradient id="trustGradientPremium" x1="0%" y1="0%" x2="100%" y2="100%">
                <stop offset="0%" stopColor="#ff5fd2" />
                <stop offset="50%" stopColor="#7c5cff" />
                <stop offset="100%" stopColor="#1df2c3" />
              </linearGradient>
            </defs>
            <circle cx="80" cy="80" r="65" className="ring-track" />
            <motion.circle
              cx="80"
              cy="80"
              r="65"
              className="ring-progress"
              strokeDasharray="408"
              initial={{ strokeDashoffset: 408 }}
              animate={{ strokeDashoffset: ringOffset }}
              transition={{ duration: 1.2, ease: "easeOut" }}
              stroke="url(#trustGradientPremium)"
            />
          </svg>
          <div className="score-center">
            <span>Live score</span>
            <strong>{displayScore}</strong>
            <p>{verdict}</p>
          </div>
        </div>

        <div className="trust-meter">
          <div className="trust-meter-arc" />
          <motion.div
            className="trust-meter-needle"
            initial={{ rotate: -90 }}
            animate={{ rotate: needleRotation }}
            transition={{ duration: 1.1, ease: "easeOut" }}
          />
          <div className="trust-meter-center" />
          <div className="trust-meter-labels">
            <span>Risk</span>
            <span>Trust</span>
          </div>
        </div>
      </div>
    </motion.div>
  );
}

export default ScoreCircle;
