import React, { useEffect, useState } from "react";
import { Link, useParams } from "react-router-dom";
import { AlertTriangle, ArrowLeft, BookOpen, CheckCircle, HelpCircle } from "lucide-react";
import Layout from "../components/Layout";
import { LabStatusBadge } from "../components/StatusBadge";
import { apiFetch } from "../lib/api";
import { useApp } from "../context/AppContext";

export default function DetailedResultsPage() {
  const { id } = useParams();
  const { language, t } = useApp();
  const [doc, setDoc] = useState(null);
  const [loading, setLoading] = useState(true);

  const load = async () => {
    setLoading(true);
    try {
      const data = await apiFetch(`/api/documents/${id}?language=${language}`);
      setDoc(data);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    load();
  }, [id, language]);

  const handleVerifyEntity = async (entityId, currentVerified) => {
    await apiFetch(`/api/documents/${id}/entities/${entityId}/verify`, {
      method: "PATCH",
      body: JSON.stringify({ verified: !currentVerified }),
    });
    await load();
  };

  if (loading || !doc) {
    return (
      <Layout>
        <div className="py-12 text-center text-slate-400">Loading detailed results...</div>
      </Layout>
    );
  }

  return (
    <Layout>
      <div className="mb-6">
        <Link
          to={`/documents/${id}`}
          className="inline-flex items-center gap-1.5 text-xs text-cyan-300 hover:underline mb-2"
        >
          <ArrowLeft className="w-3.5 h-3.5" /> Back to Document Intelligence
        </Link>
        <h1 className="text-2xl font-bold text-white">{t.results.title}</h1>
        <p className="text-xs text-slate-400 mt-1">{doc.original_filename}</p>
      </div>

      {/* Lab Values Table */}
      <div className="glass-card rounded-2xl p-6 mb-6">
        <h2 className="text-base font-semibold text-white mb-4">{t.results.labTable}</h2>
        {doc.lab_findings.length === 0 ? (
          <p className="text-xs text-slate-400">No structured numerical laboratory measurements were found in this document.</p>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full text-left text-xs">
              <thead className="text-slate-400 border-b border-slate-800">
                <tr>
                  <th className="py-2.5 pr-4">{t.results.testName}</th>
                  <th className="py-2.5 pr-4">{t.results.result}</th>
                  <th className="py-2.5 pr-4">{t.results.refRange}</th>
                  <th className="py-2.5 pr-4">{t.results.status}</th>
                  <th className="py-2.5">{t.results.source}</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-800/70">
                {doc.lab_findings.map((lab) => (
                  <tr key={lab.id}>
                    <td className="py-3 pr-4">
                      <div className="font-semibold text-white">{lab.test_name}</div>
                      {lab.verification_reason && (
                        <div className="text-[11px] text-amber-300/90 mt-0.5">
                          {lab.verification_reason}
                        </div>
                      )}
                    </td>
                    <td className="py-3 pr-4 font-mono text-cyan-200 font-semibold">
                      {lab.value_raw} {lab.unit || ""}
                    </td>
                    <td className="py-3 pr-4 font-mono text-slate-300">
                      {lab.ref_text || "Not printed on report"}
                    </td>
                    <td className="py-3 pr-4">
                      <LabStatusBadge status={lab.status} />
                    </td>
                    <td className="py-3 font-mono text-[11px] text-slate-400 max-w-xs truncate">
                      p.{lab.source_page}: {lab.source_snippet}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>

      {/* All Extracted Entities & Verification */}
      <div className="glass-card rounded-2xl p-6 mb-6">
        <h2 className="text-base font-semibold text-white mb-4">Extracted Entities & Source Verification</h2>
        <div className="space-y-2.5">
          {doc.entities.map((ent) => (
            <div
              key={ent.id}
              className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 p-3.5 rounded-xl bg-slate-900/60 border border-slate-800 text-xs"
            >
              <div>
                <div className="flex items-center gap-2">
                  <span className="px-2 py-0.5 rounded bg-slate-800 text-cyan-300 font-mono text-[10px]">
                    {ent.entity_type}
                  </span>
                  <span className="font-semibold text-white">{ent.name}</span>
                  {ent.value && <span className="font-mono text-cyan-200">{ent.value} {ent.unit || ""}</span>}
                </div>
                {ent.observation && <p className="text-slate-300 mt-1">{ent.observation}</p>}
                <p className="text-[11px] font-mono text-slate-500 mt-1">
                  Source p.{ent.source_page}: {ent.source_snippet}
                </p>
              </div>
              <button
                onClick={() => handleVerifyEntity(ent.id, ent.verified_by_user)}
                className={`inline-flex items-center gap-1.5 px-3 py-1.5 rounded-lg border text-xs font-medium shrink-0 ${
                  ent.verified_by_user
                    ? "bg-emerald-500/15 border-emerald-400/30 text-emerald-300"
                    : "bg-slate-800 border-slate-700 text-slate-300 hover:border-cyan-400/40"
                }`}
              >
                <CheckCircle className="w-3.5 h-3.5" />
                {ent.verified_by_user ? "Verified" : "Mark Verified"}
              </button>
            </div>
          ))}
        </div>
      </div>

      {/* Glossary, Questions & Uncertainties */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        <div className="glass-card rounded-2xl p-6">
          <h3 className="text-sm font-semibold text-white flex items-center gap-2 mb-3">
            <BookOpen className="w-4 h-4 text-cyan-300" />
            {t.results.glossary}
          </h3>
          <div className="space-y-3">
            {(doc.analysis?.terminology_glossary || []).map((g, i) => (
              <div key={i} className="text-xs">
                <div className="font-semibold text-cyan-200">{g.term}</div>
                <div className="text-slate-300 mt-0.5">{g.plain_definition}</div>
              </div>
            ))}
          </div>
        </div>

        <div className="glass-card rounded-2xl p-6">
          <h3 className="text-sm font-semibold text-white flex items-center gap-2 mb-3">
            <HelpCircle className="w-4 h-4 text-teal-300" />
            {t.results.questions}
          </h3>
          <ul className="space-y-2.5 text-xs text-slate-300">
            {(doc.analysis?.questions_for_doctor || []).map((q, i) => (
              <li key={i} className="p-2.5 rounded-xl bg-slate-900/60 border border-slate-800">
                {q}
              </li>
            ))}
          </ul>
        </div>

        <div className="glass-card rounded-2xl p-6">
          <h3 className="text-sm font-semibold text-white flex items-center gap-2 mb-3">
            <AlertTriangle className="w-4 h-4 text-amber-300" />
            {t.results.uncertainties}
          </h3>
          <ul className="space-y-2 text-xs text-amber-200/90">
            {(doc.analysis?.uncertainty_notes || []).length === 0 ? (
              <li className="text-slate-400">No major extraction uncertainties flagged.</li>
            ) : (
              doc.analysis.uncertainty_notes.map((u, i) => (
                <li key={i} className="p-2.5 rounded-xl bg-amber-500/10 border border-amber-400/20">
                  {u}
                </li>
              ))
            )}
          </ul>
        </div>
      </div>
    </Layout>
  );
}
