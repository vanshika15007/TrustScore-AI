import React from "react";
import { AnimatePresence, motion } from "framer-motion";

const STATUS_ORDER = ["pending", "processing", "completed"];

function StatusTracker({ taskId, taskStatus, backendStatus }) {
  return (
    <motion.section
      className="glass-panel status-tracker"
      initial={{ opacity: 0, y: 18 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ delay: 0.15 }}
    >
      <div className="card-head">
        <h3>Live Task Status</h3>
        <span>{taskId || "No task yet"}</span>
      </div>

      <div className="tracker-row">
        {STATUS_ORDER.map((status) => {
          const active = STATUS_ORDER.indexOf(taskStatus) >= STATUS_ORDER.indexOf(status);
          return (
            <div key={status} className={`tracker-step ${active ? "active" : ""}`}>
              <div className="tracker-dot" />
              <small>{status}</small>
            </div>
          );
        })}
      </div>

      <AnimatePresence mode="wait">
        <motion.p
          key={`${taskStatus}-${backendStatus}`}
          className="tracker-copy"
          initial={{ opacity: 0, y: 8 }}
          animate={{ opacity: 1, y: 0 }}
          exit={{ opacity: 0, y: -8 }}
        >
          Backend is {backendStatus}. Current task state is {taskStatus}.
        </motion.p>
      </AnimatePresence>
    </motion.section>
  );
}

export default StatusTracker;
