import React, { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { AlertTriangle, Pill, ShieldAlert } from "lucide-react";
import Layout from "../components/Layout";
import { apiFetch } from "../lib/api";
import { useApp } from "../context/AppContext";

export default function PrescriptionReaderPage() {
  const { t } = useApp();
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    apiFetch("/api/insights/prescriptions")
      .then(setData)
      .finally(() => setLoading(false));
  }, []);

  return (
    <Layout>
      <div className="mb-6">
        <h1 className="text-2xl sm:text-3xl font-bold text-white">{t.prescriptions.title}</h1>
        <p className="text-sm text-slate-400 mt-1">{t.prescriptions.subtitle}</p>
      </div>

      {data?.safety_notice && (
        <div className="mb-6 rounded-2xl bg-amber-500/10 border border-amber-400/25 p-4 flex items-start gap-2.5 text-xs text-amber-200">
          <ShieldAlert className="w-4 h-4 text-amber-300 shrink-0 mt-0.5" />
          <span>{data.safety_notice}</span>
        </div>
      )}

      {loading ? (
        <div className="py-12 text-center text-slate-400">Loading extracted prescriptions...</div>
      ) : (data?.medications || []).length === 0 ? (
        <div className="glass-card rounded-2xl p-8 text-center text-sm text-slate-400">
          No prescriptions or medication entries extracted yet. Upload a prescription or load the synthetic demo kit from the Dashboard.
        </div>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          {data.medications.map((med) => (
            <div key={med.id} className="glass-card rounded-2xl p-5 space-y-3">
              <div className="flex items-start justify-between gap-3">
                <div className="flex items-center gap-2.5">
                  <div className="w-9 h-9 rounded-xl bg-emerald-500/15 border border-emerald-400/30 flex items-center justify-center">
                    <Pill className="w-4 h-4 text-emerald-300" />
                  </div>
                  <div>
                    <div className="text-base font-bold text-white">{med.medicine_name}</div>
                    <div className="text-xs font-mono text-cyan-300">{med.dosage || "Dosage not detected"}</div>
                  </div>
                </div>
                <Link
                  to={`/documents/${med.document_id}`}
                  className="text-[11px] text-cyan-300 hover:underline shrink-0"
                >
                  {med.report_date}
                </Link>
              </div>

              <div className="grid grid-cols-2 gap-2 text-xs bg-slate-900/60 rounded-xl p-3 border border-slate-800">
                <div>
                  <span className="text-slate-400 block text-[11px]">Frequency</span>
                  <span className="text-slate-100 font-medium">{med.frequency || "Unclear — verify"}</span>
                </div>
                <div>
                  <span className="text-slate-400 block text-[11px]">Duration</span>
                  <span className="text-slate-100 font-medium">{med.duration || "Not specified"}</span>
                </div>
              </div>

              {med.needs_verification && (
                <div className="flex items-start gap-2 rounded-xl bg-amber-500/10 border border-amber-400/25 p-2.5 text-xs text-amber-200">
                  <AlertTriangle className="w-3.5 h-3.5 text-amber-300 shrink-0 mt-0.5" />
                  <span>{med.verification_reason || "Verify dosage and frequency with original prescription."}</span>
                </div>
              )}

              <div className="text-[11px] font-mono text-slate-400 truncate">
                Source ({med.filename}, p.{med.source_page}): {med.source_snippet}
              </div>
            </div>
          ))}
        </div>
      )}
    </Layout>
  );
}
