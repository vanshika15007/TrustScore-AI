import React, { useMemo } from "react";
import { motion } from "framer-motion";
import {
  Bar,
  BarChart,
  CartesianGrid,
  Cell,
  Pie,
  PieChart,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";

const PIE_COLORS = ["#7c5cff", "#1df2c3", "#ffd166"];

function Charts({ result }) {
  const pieData = useMemo(
    () => [
      { name: "Sentiment", value: Math.round(result.factors.sentiment * 100) },
      { name: "Security", value: result.factors.security === "HTTPS" ? 100 : 35 },
      {
        name: "Content Quality",
        value:
          result.factors.content_quality === "Good"
            ? 88
            : result.factors.content_quality === "Moderate"
              ? 58
              : 22,
      },
    ],
    [result],
  );

  const barData = useMemo(() => {
    if (!result.factors.keywords.length) {
      return [{ keyword: "No keyword hits", frequency: 0 }];
    }
    return result.factors.keywords.map((keyword) => ({
      keyword,
      frequency: 1,
    }));
  }, [result]);

  return (
    <div className="dashboard-grid">
      <motion.div className="glass-panel chart-card hover-lift" initial={{ opacity: 0, y: 18 }} animate={{ opacity: 1, y: 0 }}>
        <div className="card-head">
          <h3>Trust Factors</h3>
          <span>Sentiment, security, and content quality</span>
        </div>
        <div className="chart-wrap">
          <ResponsiveContainer width="100%" height="100%">
            <PieChart>
              <Pie data={pieData} dataKey="value" innerRadius={48} outerRadius={90} paddingAngle={5}>
                {pieData.map((entry, index) => (
                  <Cell key={entry.name} fill={PIE_COLORS[index]} />
                ))}
              </Pie>
              <Tooltip />
            </PieChart>
          </ResponsiveContainer>
        </div>
      </motion.div>

      <motion.div className="glass-panel chart-card hover-lift" initial={{ opacity: 0, y: 18 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: 0.08 }}>
        <div className="card-head">
          <h3>Risk Keyword Frequency</h3>
          <span>Detected risky terms</span>
        </div>
        <div className="chart-wrap">
          <ResponsiveContainer width="100%" height="100%">
            <BarChart data={barData}>
              <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.08)" />
              <XAxis dataKey="keyword" stroke="#d8deff" angle={-14} textAnchor="end" height={64} />
              <YAxis stroke="#d8deff" allowDecimals={false} />
              <Tooltip />
              <Bar dataKey="frequency" radius={[12, 12, 0, 0]}>
                {barData.map((entry, index) => (
                  <Cell key={`${entry.keyword}-${index}`} fill="#ff6b7f" />
                ))}
              </Bar>
            </BarChart>
          </ResponsiveContainer>
        </div>
      </motion.div>
    </div>
  );
}

export default Charts;
