import React from "react";
import { motion } from "framer-motion";

function ErrorCard({ error, suggestions, onRetry, onSuggestionClick }) {
  return (
    <motion.section
      className="glass-panel error-card"
      initial={{ opacity: 0, scale: 0.96, y: 18 }}
      animate={{ opacity: 1, scale: 1, y: 0 }}
      exit={{ opacity: 0, y: -18 }}
    >
      <motion.div
        className="warning-icon"
        animate={{ rotate: [0, -8, 8, -4, 4, 0] }}
        transition={{ duration: 1.4, repeat: Infinity, repeatDelay: 1.2 }}
      >
        !
      </motion.div>
      <h3>This site blocks scraping or has low readable content</h3>
      <p>{error}</p>

      <div className="suggestion-row">
        {suggestions.map((site) => (
          <motion.button
            key={site}
            type="button"
            className="suggestion-chip"
            onClick={() => onSuggestionClick(site)}
            whileHover={{ scale: 1.05, y: -1 }}
            whileTap={{ scale: 0.98 }}
          >
            {site}
          </motion.button>
        ))}
      </div>

      {onRetry ? (
        <motion.button
          type="button"
          className="retry-button"
          onClick={onRetry}
          whileHover={{ scale: 1.03, boxShadow: "0 0 28px rgba(255, 107, 127, 0.3)" }}
          whileTap={{ scale: 0.98 }}
        >
          Retry analysis
        </motion.button>
      ) : null}
    </motion.section>
  );
}

export default ErrorCard;
