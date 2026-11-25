import React, { useEffect, useState } from "react";
import { AlertTriangle, ArrowDown, ArrowUp, GitCompare, Minus, Upload } from "lucide-react";
import {
  Bar,
  BarChart,
  CartesianGrid,
  Legend,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";
import Layout from "../components/Layout";
import { apiFetch, uploadWithProgress } from "../lib/api";
import { useApp } from "../context/AppContext";

export default function CompareReportsPage() {
  const { language, t } = useApp();
  const [docs, setDocs] = useState([]);
  const [docA, setDocA] = useState("");
  const [docB, setDocB] = useState("");
  const [result, setResult] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  const loadDocs = async () => {
    const list = await apiFetch("/api/documents");
    setDocs(list);
    if (list.length >= 2) {
      setDocA(list[1].id);
      setDocB(list[0].id);
    }
  };

  useEffect(() => {
    loadDocs().catch((e) => setError(e.message));
  }, []);

  const handleQuickUpload = async (slot, file) => {
    if (!file) return;
    setError("");
    setLoading(true);
    try {
      const uploaded = await uploadWithProgress(file, {
        language,
        consentConfirmed: true,
      });
      await loadDocs();
      if (slot === "A") setDocA(uploaded.id);
      else setDocB(uploaded.id);
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  const handleCompare = async () => {
    setError("");
    setLoading(true);
    try {
      const res = await apiFetch("/api/insights/compare", {
        method: "POST",
        body: JSON.stringify({ doc_a_id: docA, doc_b_id: docB, language }),
      });
      setResult(res);
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  const chartData = (result?.matched_tests || []).map((m) => ({
    name: m.display_name.slice(0, 18),
    ReportA: m.value_a,
    ReportB: m.value_b,
  }));

  return (
    <Layout>
      <div className="mb-8">
        <h1 className="text-2xl sm:text-3xl font-bold text-white">{t.compare.title}</h1>
        <p className="text-sm text-slate-400 mt-1">{t.compare.subtitle}</p>
      </div>

      <div className="glass-card rounded-2xl p-6 mb-6 space-y-5">
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          <div className="space-y-2">
            <label className="block text-xs font-medium text-slate-300">{t.compare.reportA}</label>
            <select
              value={docA}
              onChange={(e) => setDocA(e.target.value)}
              className="w-full px-3.5 py-2.5 rounded-xl bg-slate-900 border border-slate-700 text-sm text-white"
            >
              <option value="">Select Baseline Report...</option>
              {docs.map((d) => (
                <option key={d.id} value={d.id}>
                  {d.original_filename} ({d.report_date || d.created_at.slice(0, 10)})
                </option>
              ))}
            </select>
            <label className="inline-flex items-center gap-1.5 text-xs text-cyan-300 cursor-pointer hover:underline">
              <Upload className="w-3.5 h-3.5" />
              Or upload Report A directly
              <input
                type="file"
                accept=".pdf,.jpg,.jpeg,.png"
                className="hidden"
                onChange={(e) => handleQuickUpload("A", e.target.files?.[0])}
              />
            </label>
          </div>

          <div className="space-y-2">
            <label className="block text-xs font-medium text-slate-300">{t.compare.reportB}</label>
            <select
              value={docB}
              onChange={(e) => setDocB(e.target.value)}
              className="w-full px-3.5 py-2.5 rounded-xl bg-slate-900 border border-slate-700 text-sm text-white"
            >
              <option value="">Select Follow-Up Report...</option>
              {docs.map((d) => (
                <option key={d.id} value={d.id}>
                  {d.original_filename} ({d.report_date || d.created_at.slice(0, 10)})
                </option>
              ))}
            </select>
            <label className="inline-flex items-center gap-1.5 text-xs text-cyan-300 cursor-pointer hover:underline">
              <Upload className="w-3.5 h-3.5" />
              Or upload Report B directly
              <input
                type="file"
                accept=".pdf,.jpg,.jpeg,.png"
                className="hidden"
                onChange={(e) => handleQuickUpload("B", e.target.files?.[0])}
              />
            </label>
          </div>
        </div>

        {error && (
          <div className="rounded-xl bg-rose-500/15 border border-rose-400/30 p-3 text-xs text-rose-200">
            {error}
          </div>
        )}

        <button
          onClick={handleCompare}
          disabled={loading || !docA || !docB}
          className="inline-flex items-center gap-2 px-5 py-3 rounded-xl bg-gradient-to-r from-teal-400 to-cyan-400 text-slate-950 font-bold text-sm hover:brightness-110 transition disabled:opacity-50"
        >
          <GitCompare className="w-4 h-4" />
          {loading ? "Comparing..." : t.compare.runCompare}
        </button>
      </div>

      {result && (
        <div className="space-y-6">
          <div className="glass-card rounded-2xl p-6">
            <p className="text-sm text-cyan-200 mb-4">{result.narrative_summary}</p>

            {chartData.length > 0 && (
              <div className="h-72 w-full mb-6">
                <ResponsiveContainer width="100%" height="100%">
                  <BarChart data={chartData}>
                    <CartesianGrid strokeDasharray="3 3" stroke="#1e293b" />
                    <XAxis dataKey="name" stroke="#94a3b8" fontSize={11} />
                    <YAxis stroke="#94a3b8" fontSize={11} />
                    <Tooltip
                      contentStyle={{
                        backgroundColor: "#0b162d",
                        borderColor: "#22d3ee40",
                        borderRadius: "12px",
                        fontSize: "12px",
                      }}
                    />
                    <Legend />
                    <Bar dataKey="ReportA" name="Baseline (A)" fill="#14b8a6" radius={[6, 6, 0, 0]} />
                    <Bar dataKey="ReportB" name="Follow-Up (B)" fill="#22d3ee" radius={[6, 6, 0, 0]} />
                  </BarChart>
                </ResponsiveContainer>
              </div>
            )}

            <h2 className="text-base font-semibold text-white mb-3">{t.compare.matchedTitle}</h2>
            {result.matched_tests.length === 0 ? (
              <p className="text-xs text-slate-400">No tests with identical measurement units matched across both reports.</p>
            ) : (
              <div className="overflow-x-auto">
                <table className="w-full text-left text-xs">
                  <thead className="text-slate-400 border-b border-slate-800">
                    <tr>
                      <th className="py-2 pr-3">Test</th>
                      <th className="py-2 pr-3">Unit</th>
                      <th className="py-2 pr-3">Report A</th>
                      <th className="py-2 pr-3">Report B</th>
                      <th className="py-2">Change</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-slate-800/70">
                    {result.matched_tests.map((m) => (
                      <tr key={m.canonical_test_key}>
                        <td className="py-2.5 pr-3 font-medium text-white">{m.display_name}</td>
                        <td className="py-2.5 pr-3 font-mono text-slate-400">{m.unit}</td>
                        <td className="py-2.5 pr-3 font-mono text-slate-200">{m.value_a_raw}</td>
                        <td className="py-2.5 pr-3 font-mono text-cyan-200">{m.value_b_raw}</td>
                        <td className="py-2.5 font-mono">
                          <span
                            className={`inline-flex items-center gap-1 ${
                              m.direction === "increased"
                                ? "text-amber-300"
                                : m.direction === "decreased"
                                ? "text-teal-300"
                                : "text-slate-400"
                            }`}
                          >
                            {m.direction === "increased" && <ArrowUp className="w-3.5 h-3.5" />}
                            {m.direction === "decreased" && <ArrowDown className="w-3.5 h-3.5" />}
                            {m.direction === "unchanged" && <Minus className="w-3.5 h-3.5" />}
                            {m.absolute_change > 0 ? `+${m.absolute_change}` : m.absolute_change}{" "}
                            {m.percent_change !== null ? `(${m.percent_change > 0 ? "+" : ""}${m.percent_change}%)` : ""}
                          </span>
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            )}
          </div>

          {result.incompatible_tests?.length > 0 && (
            <div className="glass-card rounded-2xl p-6 border-amber-400/30">
              <h3 className="text-sm font-semibold text-amber-300 flex items-center gap-2 mb-3">
                <AlertTriangle className="w-4 h-4" />
                {t.compare.incompatibleTitle}
              </h3>
              <div className="space-y-2 text-xs">
                {result.incompatible_tests.map((inc, idx) => (
                  <div key={idx} className="p-3 rounded-xl bg-amber-500/10 border border-amber-400/20 text-amber-100">
                    <strong>{inc.test_name_a}</strong> ({inc.unit_a || "no unit"}) vs{" "}
                    <strong>{inc.test_name_b}</strong> ({inc.unit_b || "no unit"}): {inc.reason}
                  </div>
                ))}
              </div>
            </div>
          )}
        </div>
      )}
    </Layout>
  );
}
