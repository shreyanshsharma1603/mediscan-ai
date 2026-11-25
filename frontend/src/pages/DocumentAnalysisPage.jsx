import React, { useEffect, useState } from "react";
import { Link, useParams } from "react-router-dom";
import {
  AlertTriangle,
  Bot,
  CheckCircle2,
  Eye,
  FileText,
  Send,
  ShieldAlert,
  Sparkles,
  Stethoscope,
} from "lucide-react";
import Layout from "../components/Layout";
import { DocTypeBadge, LabStatusBadge } from "../components/StatusBadge";
import { apiFetch, fetchAuthorizedBlobUrl } from "../lib/api";
import { DOC_TYPE_LABELS } from "../i18n/translations";
import { useApp } from "../context/AppContext";

export default function DocumentAnalysisPage() {
  const { id } = useParams();
  const { language, t } = useApp();

  const [doc, setDoc] = useState(null);
  const [loading, setLoading] = useState(true);
  const [overrideType, setOverrideType] = useState("");
  const [savingOverride, setSavingOverride] = useState(false);
  const [sourceTab, setSourceTab] = useState("ocr");
  const [filePreviewUrl, setFilePreviewUrl] = useState(null);

  const [qaHistory, setQaHistory] = useState([]);
  const [question, setQuestion] = useState("");
  const [asking, setAsking] = useState(false);
  const [error, setError] = useState("");

  const loadDoc = async () => {
    setLoading(true);
    try {
      const [detail, qa] = await Promise.all([
        apiFetch(`/api/documents/${id}?language=${language}`),
        apiFetch(`/api/documents/${id}/qa`),
      ]);
      setDoc(detail);
      setOverrideType(detail.classification?.final_type || "other");
      setQaHistory(qa);
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadDoc();
    return () => {
      if (filePreviewUrl) URL.revokeObjectURL(filePreviewUrl);
    };
  }, [id, language]);

  const handleLoadPreview = async () => {
    setSourceTab("preview");
    if (!filePreviewUrl) {
      try {
        const url = await fetchAuthorizedBlobUrl(`/api/documents/${id}/file`);
        setFilePreviewUrl(url);
      } catch (err) {
        setError(err.message);
      }
    }
  };

  const handleOverride = async (nextType) => {
    setOverrideType(nextType);
    setSavingOverride(true);
    try {
      const updated = await apiFetch(`/api/documents/${id}/classification`, {
        method: "PATCH",
        body: JSON.stringify({ document_type: nextType }),
      });
      setDoc(updated);
    } catch (err) {
      setError(err.message);
    } finally {
      setSavingOverride(false);
    }
  };

  const handleAsk = async (e) => {
    e.preventDefault();
    if (!question.trim()) return;
    setAsking(true);
    try {
      const res = await apiFetch(`/api/documents/${id}/qa`, {
        method: "POST",
        body: JSON.stringify({ question, language }),
      });
      setQaHistory((prev) => [...prev, res]);
      setQuestion("");
    } catch (err) {
      setError(err.message);
    } finally {
      setAsking(false);
    }
  };

  if (loading) {
    return (
      <Layout>
        <div className="py-16 text-center text-slate-400">Loading medical intelligence view...</div>
      </Layout>
    );
  }

  if (!doc) {
    return (
      <Layout>
        <div className="rounded-xl bg-rose-500/15 border border-rose-400/30 p-5 text-rose-200">
          {error || "Document not found."}
        </div>
      </Layout>
    );
  }

  return (
    <Layout>
      <div className="flex flex-col lg:flex-row lg:items-center justify-between gap-4 mb-6">
        <div>
          <div className="flex flex-wrap items-center gap-3">
            <h1 className="text-xl sm:text-2xl font-bold text-white">{doc.original_filename}</h1>
            <DocTypeBadge docType={doc.classification.final_type} />
          </div>
          <p className="text-xs text-slate-400 mt-1">
            Report Date: {doc.report_date || "Not detected"} • Pages: {doc.page_count} • OCR Engine: {doc.ocr_engine}
          </p>
        </div>

        <div className="flex flex-wrap items-center gap-3">
          <Link
            to={`/documents/${id}/results`}
            className="px-4 py-2 rounded-xl bg-gradient-to-r from-teal-400 to-cyan-400 text-slate-950 text-xs font-bold hover:brightness-110 transition"
          >
            {t.analysis.viewDetailed}
          </Link>
          <Link
            to={`/doctor-summary?doc=${id}`}
            className="inline-flex items-center gap-1.5 px-4 py-2 rounded-xl bg-slate-900 border border-cyan-500/30 text-cyan-200 text-xs font-semibold hover:border-cyan-400 transition"
          >
            <Stethoscope className="w-3.5 h-3.5" />
            {t.nav.doctorSummary}
          </Link>
        </div>
      </div>

      {doc.ocr_warnings?.length > 0 && (
        <div className="mb-6 rounded-2xl bg-amber-500/10 border border-amber-400/30 p-4 space-y-1">
          <div className="flex items-center gap-2 text-xs font-semibold text-amber-300">
            <AlertTriangle className="w-4 h-4" />
            OCR Quality Diagnostics ({doc.ocr_quality_status} — {Math.round(doc.ocr_quality_score * 100)}%)
          </div>
          {doc.ocr_warnings.map((w, i) => (
            <p key={i} className="text-xs text-amber-200/90 pl-6">
              • {w}
            </p>
          ))}
        </div>
      )}

      {/* Classification & Confidence Bar */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-4 mb-6">
        <div className="glass-card rounded-2xl p-5 lg:col-span-2">
          <div className="flex flex-wrap items-center justify-between gap-3 mb-3">
            <div>
              <div className="text-xs text-slate-400">{t.analysis.classification}</div>
              <div className="text-base font-semibold text-white mt-0.5">
                {DOC_TYPE_LABELS[doc.classification.final_type]}{" "}
                <span className="text-xs font-mono text-cyan-300 ml-2">
                  ({Math.round(doc.classification.confidence * 100)}% {t.analysis.confidence})
                </span>
              </div>
            </div>
            <div className="flex items-center gap-2">
              <label className="text-xs text-slate-400">{t.analysis.overrideLabel}:</label>
              <select
                value={overrideType}
                disabled={savingOverride}
                onChange={(e) => handleOverride(e.target.value)}
                className="bg-slate-900 border border-slate-700 rounded-xl px-3 py-1.5 text-xs text-white"
              >
                {Object.entries(DOC_TYPE_LABELS).map(([k, lbl]) => (
                  <option key={k} value={k}>
                    {lbl}
                  </option>
                ))}
              </select>
            </div>
          </div>
          <div className="flex flex-wrap gap-2">
            {doc.classification.signals.map((sig, i) => (
              <span
                key={i}
                className="text-[11px] px-2.5 py-1 rounded-lg bg-slate-900/80 border border-slate-700 text-slate-300"
              >
                {sig}
              </span>
            ))}
          </div>
        </div>

        <div className="glass-card rounded-2xl p-5 flex flex-col justify-between">
          <div>
            <div className="text-xs text-slate-400">{t.analysis.ocrQuality}</div>
            <div className="text-2xl font-bold font-mono text-white mt-1">
              {Math.round(doc.ocr_quality_score * 100)}%
            </div>
          </div>
          <div className="text-xs text-slate-300 mt-2">
            Status: <span className="text-cyan-300 font-semibold">{doc.ocr_quality_status}</span> •{" "}
            {doc.lab_findings.length} labs • {doc.entities.filter((e) => e.entity_type === "medication").length} meds
          </div>
        </div>
      </div>

      {/* Main Split Grid: AI Summary + Labs vs Source Verification & Q&A */}
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-6">
        <div className="lg:col-span-7 space-y-6">
          {/* Plain-Language Summary */}
          <div className="glass-card rounded-2xl p-6">
            <div className="flex items-center justify-between mb-3">
              <h2 className="text-base font-semibold text-white flex items-center gap-2">
                <Sparkles className="w-4 h-4 text-cyan-300" />
                {t.analysis.plainSummary}
              </h2>
              <span className="text-[11px] font-mono text-slate-400">
                {doc.analysis?.ai_provider}
              </span>
            </div>
            <p className="text-sm text-slate-200 leading-relaxed mb-4">
              {doc.analysis?.plain_summary}
            </p>
            {doc.analysis?.key_takeaways?.length > 0 && (
              <div className="space-y-1.5 pt-3 border-t border-slate-800">
                <div className="text-xs font-semibold text-cyan-300">{t.analysis.keyTakeaways}</div>
                {doc.analysis.key_takeaways.map((tk, i) => (
                  <div key={i} className="text-xs text-slate-300 flex items-start gap-2">
                    <CheckCircle2 className="w-3.5 h-3.5 text-teal-400 shrink-0 mt-0.5" />
                    <span>{tk}</span>
                  </div>
                ))}
              </div>
            )}
          </div>

          {/* Quick Extracted Lab Values */}
          {doc.lab_findings.length > 0 && (
            <div className="glass-card rounded-2xl p-6">
              <div className="flex items-center justify-between mb-4">
                <h2 className="text-base font-semibold text-white">Extracted Lab Values</h2>
                <Link
                  to={`/documents/${id}/results`}
                  className="text-xs text-cyan-300 hover:underline"
                >
                  Full Table →
                </Link>
              </div>
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
                    {doc.lab_findings.slice(0, 8).map((lab) => (
                      <tr key={lab.id}>
                        <td className="py-2.5 pr-3 font-medium text-white">{lab.test_name}</td>
                        <td className="py-2.5 pr-3 font-mono text-cyan-200">
                          {lab.value_raw} {lab.unit || ""}
                        </td>
                        <td className="py-2.5 pr-3 font-mono text-slate-400">
                          {lab.ref_text || "Not printed"}
                        </td>
                        <td className="py-2.5">
                          <LabStatusBadge status={lab.status} />
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </div>
          )}

          {/* Grounded AI Medical Document Assistant (Module 7) */}
          <div className="glass-card rounded-2xl p-6">
            <div className="mb-4">
              <h2 className="text-base font-semibold text-white flex items-center gap-2">
                <Bot className="w-4 h-4 text-cyan-300" />
                {t.analysis.assistantTitle}
              </h2>
              <p className="text-xs text-slate-400 mt-0.5">{t.analysis.assistantSubtitle}</p>
            </div>

            <div className="space-y-3 max-h-72 overflow-y-auto mb-4 pr-1">
              {qaHistory.length === 0 ? (
                <div className="text-xs text-slate-400 bg-slate-900/50 rounded-xl p-4 border border-slate-800">
                  Ask anything about values, units, medications, or dates in this report. If a detail is absent, the assistant will clearly state it is unavailable.
                </div>
              ) : (
                qaHistory.map((item) => (
                  <div key={item.id} className="space-y-2 bg-slate-900/60 rounded-xl p-3.5 border border-slate-800">
                    <div className="text-xs font-semibold text-cyan-200">Q: {item.question}</div>
                    <div className="text-xs text-slate-200 whitespace-pre-line leading-relaxed">
                      {item.answer}
                    </div>
                    {item.citations?.length > 0 && (
                      <div className="flex flex-wrap gap-1.5 pt-1">
                        {item.citations.map((c, idx) => (
                          <span
                            key={idx}
                            className="text-[10px] font-mono px-2 py-0.5 rounded bg-slate-800 text-slate-300"
                          >
                            p.{c.page}: {c.snippet.slice(0, 60)}
                          </span>
                        ))}
                      </div>
                    )}
                  </div>
                ))
              )}
            </div>

            <form onSubmit={handleAsk} className="flex gap-2">
              <input
                type="text"
                value={question}
                onChange={(e) => setQuestion(e.target.value)}
                placeholder={t.analysis.askPlaceholder}
                className="flex-1 px-3.5 py-2.5 rounded-xl bg-slate-900 border border-slate-700 focus:border-cyan-400 text-xs text-white outline-none"
              />
              <button
                type="submit"
                disabled={asking}
                className="inline-flex items-center gap-1.5 px-4 py-2.5 rounded-xl bg-cyan-500 text-slate-950 font-bold text-xs hover:brightness-110 transition disabled:opacity-50"
              >
                <Send className="w-3.5 h-3.5" />
                {t.analysis.askBtn}
              </button>
            </form>
          </div>
        </div>

        {/* Right Column: Source Verification & Original File */}
        <div className="lg:col-span-5 space-y-6">
          <div className="glass-card rounded-2xl p-6">
            <div className="flex items-center justify-between mb-4">
              <h2 className="text-base font-semibold text-white flex items-center gap-2">
                <FileText className="w-4 h-4 text-cyan-300" />
                {t.analysis.sourceVerify}
              </h2>
              <div className="flex rounded-xl bg-slate-900 p-1 border border-slate-800 text-xs">
                <button
                  onClick={() => setSourceTab("ocr")}
                  className={`px-3 py-1 rounded-lg ${sourceTab === "ocr" ? "bg-cyan-500/20 text-cyan-200" : "text-slate-400"}`}
                >
                  OCR Pages
                </button>
                <button
                  onClick={handleLoadPreview}
                  className={`px-3 py-1 rounded-lg flex items-center gap-1 ${sourceTab === "preview" ? "bg-cyan-500/20 text-cyan-200" : "text-slate-400"}`}
                >
                  <Eye className="w-3 h-3" /> Original
                </button>
              </div>
            </div>

            {sourceTab === "ocr" ? (
              <div className="space-y-3 max-h-[560px] overflow-y-auto pr-1">
                {doc.pages.map((p) => (
                  <div key={p.page_number} className="rounded-xl bg-slate-950/80 border border-slate-800 p-3.5">
                    <div className="flex items-center justify-between text-[11px] font-mono text-cyan-300 mb-2">
                      <span>Page {p.page_number} ({p.method})</span>
                      <span>{Math.round(p.avg_confidence * 100)}%</span>
                    </div>
                    <pre className="text-xs font-mono text-slate-300 whitespace-pre-wrap leading-relaxed">
                      {p.text || "(No text recognized on this page)"}
                    </pre>
                  </div>
                ))}
              </div>
            ) : !filePreviewUrl ? (
              <div className="py-12 text-center text-xs text-slate-400">Loading secure document preview...</div>
            ) : doc.mime_type === "application/pdf" ? (
              <iframe
                src={filePreviewUrl}
                title="Original PDF"
                className="w-full h-[540px] rounded-xl bg-white border border-slate-800"
              />
            ) : (
              <img
                src={filePreviewUrl}
                alt="Original Upload"
                className="w-full max-h-[540px] object-contain rounded-xl bg-slate-950"
              />
            )}
          </div>

          <div className="rounded-2xl bg-amber-500/10 border border-amber-400/25 p-4 flex items-start gap-2.5 text-xs text-amber-200/90">
            <ShieldAlert className="w-4 h-4 text-amber-300 shrink-0 mt-0.5" />
            <span>{doc.analysis?.safety_disclaimer}</span>
          </div>
        </div>
      </div>
    </Layout>
  );
}
