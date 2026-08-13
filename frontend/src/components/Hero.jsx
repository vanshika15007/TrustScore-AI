import React, { useEffect, useState } from "react";
import { motion } from "framer-motion";

const HEADLINE = "Analyze trust in real-time...";

function Hero({ backendStatus, taskStatus }) {
  const [typedText, setTypedText] = useState("");

  useEffect(() => {
    let index = 0;
    const intervalId = window.setInterval(() => {
      index += 1;
      setTypedText(HEADLINE.slice(0, index));
      if (index >= HEADLINE.length) {
        window.clearInterval(intervalId);
      }
    }, 70);

    return () => window.clearInterval(intervalId);
  }, []);

  return (
    <section className="hero">
      <div className="hero-backdrop" />
      <motion.div
        className="hero-copy"
        initial={{ opacity: 0, y: 24 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.7 }}
      >
        <span className="eyebrow">AI Trust Analyzer</span>
        <motion.h1 initial={{ opacity: 0 }} animate={{ opacity: 1 }} transition={{ delay: 0.1 }}>
          {typedText}
          <span className="typing-caret" />
        </motion.h1>
        <motion.p
          initial={{ opacity: 0, y: 12 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.25 }}
        >
          Premium trust intelligence for modern websites with live task tracking,
          animated insights, and AI-generated explanations.
        </motion.p>

        <div className="hero-status">
          <div className="status-card">
            <span>Backend</span>
            <strong className={`status-text ${backendStatus}`}>{backendStatus}</strong>
          </div>
          <div className="status-card">
            <span>Task</span>
            <strong>{taskStatus}</strong>
          </div>
        </div>
      </motion.div>
    </section>
  );
}

export default Hero;
