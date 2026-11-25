import React from "react";
import { AlertTriangle, CheckCircle2, HelpCircle, TrendingDown, TrendingUp } from "lucide-react";
import { DOC_TYPE_LABELS } from "../i18n/translations";
import { useApp } from "../context/AppContext";

export function LabStatusBadge({ status }) {
  const { t } = useApp();
  const label = t.statuses[status] || status;

  const styles = {
    within_range: {
      cls: "bg-emerald-500/15 text-emerald-300 border-emerald-400/30",
      Icon: CheckCircle2,
    },
    below_range: {
      cls: "bg-amber-500/15 text-amber-300 border-amber-400/30",
      Icon: TrendingDown,
    },
    above_range: {
      cls: "bg-rose-500/15 text-rose-300 border-rose-400/30",
      Icon: TrendingUp,
    },
    reference_unavailable: {
      cls: "bg-slate-500/15 text-slate-300 border-slate-400/30",
      Icon: HelpCircle,
    },
    manual_verification_needed: {
      cls: "bg-violet-500/15 text-violet-300 border-violet-400/30",
      Icon: AlertTriangle,
    },
  };

  const cfg = styles[status] || styles.reference_unavailable;
  const Icon = cfg.Icon;

  return (
    <span className={`inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full text-xs font-medium border ${cfg.cls}`}>
      <Icon className="w-3.5 h-3.5" />
      {label}
    </span>
  );
}

export function DocTypeBadge({ docType }) {
  return (
    <span className="inline-flex items-center px-2.5 py-1 rounded-lg text-xs font-semibold bg-cyan-500/15 text-cyan-200 border border-cyan-400/30">
      {DOC_TYPE_LABELS[docType] || docType}
    </span>
  );
}
