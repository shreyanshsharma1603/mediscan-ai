import React, { useEffect, useState } from "react";
import { useSearchParams } from "react-router-dom";
import { Download, FileText, ShieldAlert, Stethoscope } from "lucide-react";
import Layout from "../components/Layout";
import { apiFetch, fetchAuthorizedBlobUrl } from "../lib/api";
import { useApp } from "../context/AppContext";

export default function DoctorSummaryPage() {
  const { language, t } = useApp();
  const [searchParams] = useSearchParams();
  const [docs, setDocs] = useState([]);
  const [selectedId, setSelectedId] = useState(searchParams.get("doc") || "");
  const [summary, setSummary] = useState(null);
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    apiFetch("/api/documents").then((list) => {
      setDocs(list);
      if (!selectedId && list.length > 0) {
        setSelectedId(list[0].id);
      }
    });
  }, []);

  useEffect(() => {
    if (!selectedId) return;
    setLoading(true);
    apiFetch(`/api/documents/${selectedId}/doctor-summary?language=${language}`)
      .then(setSummary)
      .finally(() => setLoading(false));
  }, [selectedId, language]);

  const handleDownloadPdf = async () => {
    if (!selectedId) return;
    const url = await fetchAuthorizedBlobUrl(
      `/api/documents/${selectedId}/doctor-summary/pdf?language=${language}`
    );
    const a = document.createElement("a");
    a.href = url;
    a.download = `MediScan_Doctor_Summary_${selectedId.slice(0, 8)}.pdf`;
    document.body.appendChild(a);
    a.click();
    a.remove();
    URL.revokeObjectURL(url);
  };

  return (
    <Layout>
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 mb-6">
        <div>
          <h1 className="text-2xl sm:text-3xl font-bold text-white">{t.doctorSummary.title}</h1>
          <p className="text-sm text-slate-400 mt-1">{t.doctorSummary.subtitle}</p>
        </div>

        <button
          onClick={handleDownloadPdf}
          disabled={!selectedId}
          className="inline-flex items-center gap-2 px-5 py-3 rounded-xl bg-gradient-to-r from-teal-400 to-cyan-400 text-slate-950 font-bold text-sm hover:brightness-110 transition disabled:opacity-50"
        >
          <Download className="w-4 h-4" />
          {t.doctorSummary.exportPdf}
        </button>
      </div>

      <div className="glass-card rounded-2xl p-5 mb-6">
        <label className="block text-xs font-medium text-slate-300 mb-2">
          {t.doctorSummary.selectDoc}
        </label>
        <select
          value={selectedId}
          onChange={(e) => setSelectedId(e.target.value)}
          className="w-full sm:max-w-lg px-3.5 py-2.5 rounded-xl bg-slate-900 border border-slate-700 text-sm text-white"
        >
          {docs.length === 0 && <option value="">No documents uploaded</option>}
          {docs.map((d) => (
            <option key={d.id} value={d.id}>
              {d.original_filename} ({d.report_date || d.created_at.slice(0, 10)})
            </option>
          ))}
        </select>
      </div>

      {loading ? (
        <div className="py-12 text-center text-slate-400">Generating clinician summary...</div>
      ) : summary ? (
        <div className="glass-card rounded-2xl p-6 space-y-6">
          <div className="flex flex-wrap items-center justify-between gap-4 border-b border-slate-800 pb-4">
            <div className="flex items-center gap-3">
              <Stethoscope className="w-5 h-5 text-cyan-300" />
              <div>
                <h2 className="text-lg font-bold text-white">{summary.patient_name}</h2>
                <p className="text-xs text-slate-400">
                  Type: {summary.document_type.replace("_", " ")} • Date: {summary.report_date || "N/A"}
                </p>
              </div>
            </div>
            <span className="text-xs font-mono px-2.5 py-1 rounded-lg bg-slate-900 border border-slate-700 text-cyan-300">
              Lang: {summary.language}
            </span>
          </div>

          <div>
            <h3 className="text-xs font-semibold uppercase tracking-wider text-cyan-300 mb-2">
              Concise Overview
            </h3>
            <p className="text-sm text-slate-200 leading-relaxed">{summary.concise_clinical_summary}</p>
          </div>

          {summary.extracted_values?.length > 0 && (
            <div>
              <h3 className="text-xs font-semibold uppercase tracking-wider text-cyan-300 mb-2">
                Extracted Lab Measurements
              </h3>
              <div className="overflow-x-auto">
                <table className="w-full text-left text-xs">
                  <thead className="text-slate-400 border-b border-slate-800">
                    <tr>
                      <th className="py-2 pr-3">Test</th>
                      <th className="py-2 pr-3">Value</th>
                      <th className="py-2 pr-3">Ref Range</th>
                      <th className="py-2">Status</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-slate-800/70">
                    {summary.extracted_values.map((v, i) => (
                      <tr key={i}>
                        <td className="py-2 pr-3 text-white font-medium">{v.test_name}</td>
                        <td className="py-2 pr-3 font-mono text-cyan-200">
                          {v.value} {v.unit !== "-" ? v.unit : ""}
                        </td>
                        <td className="py-2 pr-3 font-mono text-slate-400">{v.reference_range}</td>
                        <td className="py-2 text-slate-300">{v.status.replace("_", " ")}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </div>
          )}

          {summary.uncertainties_for_verification?.length > 0 && (
            <div>
              <h3 className="text-xs font-semibold uppercase tracking-wider text-amber-300 mb-2">
                Uncertainties for Manual Verification
              </h3>
              <ul className="space-y-1.5 text-xs text-amber-200/90">
                {summary.uncertainties_for_verification.map((u, i) => (
                  <li key={i}>• {u}</li>
                ))}
              </ul>
            </div>
          )}

          {summary.questions_for_clinician?.length > 0 && (
            <div>
              <h3 className="text-xs font-semibold uppercase tracking-wider text-teal-300 mb-2">
                Suggested Questions for Clinician Discussion
              </h3>
              <ul className="space-y-1.5 text-xs text-slate-200">
                {summary.questions_for_clinician.map((q, i) => (
                  <li key={i} className="flex items-start gap-2">
                    <FileText className="w-3.5 h-3.5 text-teal-400 shrink-0 mt-0.5" />
                    <span>{q}</span>
                  </li>
                ))}
              </ul>
            </div>
          )}

          <div className="rounded-xl bg-amber-500/10 border border-amber-400/25 p-3.5 flex items-start gap-2 text-xs text-amber-200">
            <ShieldAlert className="w-4 h-4 text-amber-300 shrink-0 mt-0.5" />
            <span>{summary.safety_disclaimer}</span>
          </div>
        </div>
      ) : null}
    </Layout>
  );
}
