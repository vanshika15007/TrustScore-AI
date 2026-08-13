import React from "react";
import { motion } from "framer-motion";

function Loader({ steps, activeStep }) {
  const progress = ((activeStep + 1) / steps.length) * 100;

  return (
    <motion.section
      key="loading"
      className="glass-panel loading-panel premium-loader"
      initial={{ opacity: 0, y: 22 }}
      animate={{ opacity: 1, y: 0 }}
      exit={{ opacity: 0, y: -18 }}
    >
      <div className="scanner-core">
        <motion.div
          className="scanner-ring ring-a"
          animate={{ rotate: 360 }}
          transition={{ repeat: Infinity, duration: 2.2, ease: "linear" }}
        />
        <motion.div
          className="scanner-ring ring-b"
          animate={{ rotate: -360 }}
          transition={{ repeat: Infinity, duration: 2.8, ease: "linear" }}
        />
        <motion.div
          className="scanner-pulse"
          animate={{ scale: [0.88, 1.12, 0.88], opacity: [0.45, 1, 0.45] }}
          transition={{ repeat: Infinity, duration: 1.6, ease: "easeInOut" }}
        />
        <div className="scanner-dot" />
      </div>

      <div className="loading-copy">
        <h3>Running premium trust analysis</h3>
        <p>{steps[activeStep]?.status}</p>

        <div className="progress-shell">
          <motion.div
            className="progress-fill"
            initial={{ width: 0 }}
            animate={{ width: `${progress}%` }}
            transition={{ duration: 0.8, ease: "easeOut" }}
          />
        </div>

        <motion.div
          className="loading-steps"
          initial="hidden"
          animate="visible"
          variants={{
            hidden: {},
            visible: {
              transition: {
                staggerChildren: 0.12,
              },
            },
          }}
        >
          {steps.map((step, index) => (
            <motion.div
              key={step.label}
              className={`loading-step ${index <= activeStep ? "active" : ""}`}
              variants={{
                hidden: { opacity: 0, y: 8 },
                visible: { opacity: 1, y: 0 },
              }}
            >
              <span>{index < activeStep ? "✔" : ""}</span>
              <small>{step.label}</small>
            </motion.div>
          ))}
        </motion.div>
      </div>
    </motion.section>
  );
}

export default Loader;
