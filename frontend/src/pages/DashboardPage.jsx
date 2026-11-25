import React, { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { motion } from "framer-motion";
import {
  AlertTriangle,
  ArrowUpRight,
  FilePlus2,
  FileText,
  Pill,
  Sparkles,
  Trash2,
} from "lucide-react";
import Layout from "../components/Layout";
import { DocTypeBadge } from "../components/StatusBadge";
import { apiFetch } from "../lib/api";
import { useApp } from "../context/AppContext";

export default function DashboardPage() {
  const { t } = useApp();
  const [docs, setDocs] = useState([]);
  const [loading, setLoading] = useState(true);
  const [loadingDemo, setLoadingDemo] = useState(false);
  const [error, setError] = useState("");

  const fetchDocs = async () => {
    setLoading(true);
    try {
      const data = await apiFetch("/api/documents");
      setDocs(data);
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchDocs();
  }, []);

  const handleLoadDemo = async () => {
    setLoadingDemo(true);
    setError("");
    try {
      await apiFetch("/api/documents/load-synthetic-demo", { method: "POST" });
      await fetchDocs();
    } catch (err) {
      setError(err.message);
    } finally {
      setLoadingDemo(false);
    }
  };

  const handleDelete = async (id) => {
    try {
      await apiFetch(`/api/documents/${id}`, { method: "DELETE" });
      setDocs((prev) => prev.filter((d) => d.id !== id));
    } catch (err) {
      setError(err.message);
    }
  };

  const totalAbnormal = docs.reduce((acc, d) => acc + (d.abnormal_count || 0), 0);
  const totalVerify = docs.reduce((acc, d) => acc + (d.verification_needed_count || 0), 0);
  const totalMeds = docs.reduce((acc, d) => acc + (d.medication_count || 0), 0);

  const stats = [
    { label: t.dashboard.totalDocs, value: docs.length, icon: FileText, tone: "text-cyan-300" },
    { label: t.dashboard.abnormalFlags, value: totalAbnormal, icon: AlertTriangle, tone: "text-amber-300" },
    { label: t.dashboard.verifyCount, value: totalVerify, icon: Sparkles, tone: "text-violet-300" },
    { label: t.dashboard.medsCount, value: totalMeds, icon: Pill, tone: "text-emerald-300" },
  ];

  return (
    <Layout>
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 mb-8">
        <div>
          <h1 className="text-2xl sm:text-3xl font-bold text-white">{t.dashboard.title}</h1>
          <p className="text-sm text-slate-400 mt-1">{t.dashboard.subtitle}</p>
        </div>

        <div className="flex flex-wrap items-center gap-3">
          <button
            onClick={handleLoadDemo}
            disabled={loadingDemo}
            className="inline-flex items-center gap-2 px-4 py-2.5 rounded-xl bg-slate-900 border border-cyan-500/30 text-cyan-200 text-xs sm:text-sm font-semibold hover:border-cyan-400 transition disabled:opacity-60"
          >
            <Sparkles className="w-4 h-4 text-cyan-300" />
            {loadingDemo ? "Generating Synthetic PDFs..." : t.dashboard.loadDemo}
          </button>
          <Link
            to="/upload"
            className="inline-flex items-center gap-2 px-4 py-2.5 rounded-xl bg-gradient-to-r from-teal-400 to-cyan-400 text-slate-950 text-xs sm:text-sm font-bold hover:brightness-110 transition"
          >
            <FilePlus2 className="w-4 h-4" />
            {t.dashboard.uploadNew}
          </Link>
        </div>
      </div>

      {error && (
        <div className="mb-6 rounded-xl bg-rose-500/15 border border-rose-400/30 p-4 text-sm text-rose-200">
          {error}
        </div>
      )}

      <div className="grid grid-cols-2 lg:grid-cols-4 gap-4 mb-8">
        {stats.map((s) => {
          const Icon = s.icon;
          return (
            <div key={s.label} className="glass-card rounded-2xl p-5">
              <div className="flex items-center justify-between mb-2">
                <span className="text-xs text-slate-400 font-medium">{s.label}</span>
                <Icon className={`w-4 h-4 ${s.tone}`} />
              </div>
              <div className="text-2xl sm:text-3xl font-bold font-mono text-white">{s.value}</div>
            </div>
          );
        })}
      </div>

      <div className="glass-card rounded-2xl p-6">
        <div className="flex items-center justify-between mb-5">
          <h2 className="text-lg font-semibold text-white">{t.dashboard.recentDocs}</h2>
          <span className="text-xs text-slate-400">{docs.length} document(s)</span>
        </div>

        {loading ? (
          <div className="py-12 text-center text-sm text-slate-400">Loading documents...</div>
        ) : docs.length === 0 ? (
          <div className="py-12 text-center max-w-md mx-auto">
            <p className="text-sm text-slate-300 mb-5">{t.dashboard.emptyState}</p>
            <button
              onClick={handleLoadDemo}
              disabled={loadingDemo}
              className="px-5 py-2.5 rounded-xl bg-cyan-500/20 border border-cyan-400/40 text-cyan-200 text-sm font-semibold hover:bg-cyan-500/30 transition"
            >
              {t.dashboard.loadDemo}
            </button>
          </div>
        ) : (
          <div className="space-y-3">
            {docs.map((doc, idx) => (
              <motion.div
                key={doc.id}
                initial={{ opacity: 0, y: 8 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ delay: idx * 0.03 }}
                className="flex flex-col md:flex-row md:items-center justify-between gap-4 p-4 rounded-xl bg-slate-900/60 border border-slate-800 hover:border-cyan-500/30 transition"
              >
                <div className="space-y-1.5">
                  <div className="flex flex-wrap items-center gap-2.5">
                    <Link
                      to={`/documents/${doc.id}`}
                      className="text-sm font-semibold text-white hover:text-cyan-300 transition"
                    >
                      {doc.original_filename}
                    </Link>
                    <DocTypeBadge docType={doc.classification?.final_type} />
                    <span className="text-[11px] font-mono text-slate-400">
                      {Math.round((doc.classification?.confidence || 0) * 100)}% conf
                    </span>
                  </div>
                  <div className="flex flex-wrap items-center gap-4 text-xs text-slate-400">
                    <span>Date: {doc.report_date || doc.created_at.slice(0, 10)}</span>
                    <span>Pages: {doc.page_count}</span>
                    <span>OCR: {doc.ocr_quality_status} ({Math.round((doc.ocr_quality_score || 0) * 100)}%)</span>
                    {doc.lab_count > 0 && <span>Labs: {doc.lab_count}</span>}
                    {doc.abnormal_count > 0 && (
                      <span className="text-amber-300 font-medium">
                        {doc.abnormal_count} out of range
                      </span>
                    )}
                    {doc.medication_count > 0 && (
                      <span className="text-emerald-300">{doc.medication_count} meds</span>
                    )}
                  </div>
                </div>

                <div className="flex items-center gap-2.5">
                  <Link
                    to={`/documents/${doc.id}`}
                    className="inline-flex items-center gap-1.5 px-3.5 py-2 rounded-xl bg-cyan-500/15 border border-cyan-400/30 text-cyan-200 text-xs font-semibold hover:bg-cyan-500/25 transition"
                  >
                    Analyze <ArrowUpRight className="w-3.5 h-3.5" />
                  </Link>
                  <button
                    onClick={() => handleDelete(doc.id)}
                    title="Delete Document"
                    className="p-2 rounded-xl bg-slate-800/80 text-slate-400 hover:text-rose-300 hover:bg-rose-500/15 transition"
                  >
                    <Trash2 className="w-4 h-4" />
                  </button>
                </div>
              </motion.div>
            ))}
          </div>
        )}
      </div>
    </Layout>
  );
}
