import React, { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { Activity, Calendar } from "lucide-react";
import {
  CartesianGrid,
  Line,
  LineChart,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";
import Layout from "../components/Layout";
import { DocTypeBadge } from "../components/StatusBadge";
import { apiFetch } from "../lib/api";
import { useApp } from "../context/AppContext";

export default function TimelinePage() {
  const { t } = useApp();
  const [timeline, setTimeline] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    apiFetch("/api/insights/timeline")
      .then(setTimeline)
      .finally(() => setLoading(false));
  }, []);

  return (
    <Layout>
      <div className="mb-8">
        <h1 className="text-2xl sm:text-3xl font-bold text-white">{t.timeline.title}</h1>
        <p className="text-sm text-slate-400 mt-1">{t.timeline.subtitle}</p>
      </div>

      {loading ? (
        <div className="py-12 text-center text-slate-400">Loading timeline...</div>
      ) : (
        <div className="space-y-6">
          <div className="glass-card rounded-2xl p-6">
            <h2 className="text-base font-semibold text-white flex items-center gap-2 mb-4">
              <Activity className="w-4 h-4 text-cyan-300" />
              {t.timeline.trendsTitle}
            </h2>
            {(timeline?.comparable_trends || []).length === 0 ? (
              <p className="text-xs text-slate-400">
                Upload at least two reports sharing the same biomarker and compatible measurement unit to see longitudinal trends.
              </p>
            ) : (
              <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
                {timeline.comparable_trends.map((series) => (
                  <div
                    key={`${series.canonical_test_key}-${series.unit}`}
                    className="rounded-xl bg-slate-900/60 border border-slate-800 p-4"
                  >
                    <div className="flex items-center justify-between mb-3">
                      <span className="text-sm font-semibold text-white">{series.display_name}</span>
                      <span className="text-xs font-mono text-cyan-300">{series.unit}</span>
                    </div>
                    <div className="h-52 w-full">
                      <ResponsiveContainer width="100%" height="100%">
                        <LineChart data={series.points}>
                          <CartesianGrid strokeDasharray="3 3" stroke="#1e293b" />
                          <XAxis dataKey="date" stroke="#94a3b8" fontSize={11} />
                          <YAxis stroke="#94a3b8" fontSize={11} domain={["auto", "auto"]} />
                          <Tooltip
                            contentStyle={{
                              backgroundColor: "#0b162d",
                              borderColor: "#22d3ee40",
                              borderRadius: "10px",
                              fontSize: "12px",
                            }}
                          />
                          <Line
                            type="monotone"
                            dataKey="value"
                            stroke="#22d3ee"
                            strokeWidth={2.5}
                            dot={{ r: 4, fill: "#14b8a6" }}
                          />
                        </LineChart>
                      </ResponsiveContainer>
                    </div>
                  </div>
                ))}
              </div>
            )}
          </div>

          <div className="glass-card rounded-2xl p-6">
            <h2 className="text-base font-semibold text-white flex items-center gap-2 mb-4">
              <Calendar className="w-4 h-4 text-teal-300" />
              {t.timeline.docsTitle}
            </h2>
            {(timeline?.timeline_documents || []).length === 0 ? (
              <p className="text-xs text-slate-400">No documents in your timeline yet.</p>
            ) : (
              <div className="relative pl-6 border-l border-cyan-500/30 space-y-5">
                {timeline.timeline_documents.map((doc) => (
                  <div key={doc.id} className="relative">
                    <span className="absolute -left-[29px] top-1.5 w-3 h-3 rounded-full bg-cyan-400 ring-4 ring-[#060d1b]" />
                    <div className="p-4 rounded-xl bg-slate-900/60 border border-slate-800 flex flex-col sm:flex-row sm:items-center justify-between gap-3">
                      <div>
                        <div className="text-xs font-mono text-cyan-300">
                          {doc.report_date || doc.created_at.slice(0, 10)}
                        </div>
                        <Link
                          to={`/documents/${doc.id}`}
                          className="text-sm font-semibold text-white hover:text-cyan-300 transition"
                        >
                          {doc.original_filename}
                        </Link>
                      </div>
                      <DocTypeBadge docType={doc.document_type || "other"} />
                    </div>
                  </div>
                ))}
              </div>
            )}
          </div>
        </div>
      )}
    </Layout>
  );
}
