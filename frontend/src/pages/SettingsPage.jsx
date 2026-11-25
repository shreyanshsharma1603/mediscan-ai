import React, { useState } from "react";
import { useNavigate } from "react-router-dom";
import { CheckCircle2, Globe, ShieldCheck, Trash2 } from "lucide-react";
import Layout from "../components/Layout";
import { apiFetch } from "../lib/api";
import { LANGUAGES } from "../i18n/translations";
import { useApp } from "../context/AppContext";

export default function SettingsPage() {
  const { user, setUser, language, setLanguage, healthInfo, logout, t } = useApp();
  const navigate = useNavigate();
  const [retentionDays, setRetentionDays] = useState(user?.retention_days || 30);
  const [savedMsg, setSavedMsg] = useState("");
  const [confirmDelete, setConfirmDelete] = useState(false);

  const handleSave = async () => {
    const updated = await apiFetch("/api/auth/preferences", {
      method: "PATCH",
      body: JSON.stringify({
        preferred_language: language,
        retention_days: Number(retentionDays),
      }),
    });
    setUser(updated);
    setSavedMsg("Preferences and automatic document retention updated.");
    setTimeout(() => setSavedMsg(""), 3500);
  };

  const handleDeleteAccount = async () => {
    await apiFetch("/api/auth/account", { method: "DELETE" });
    logout();
    navigate("/");
  };

  return (
    <Layout>
      <div className="mb-8">
        <h1 className="text-2xl sm:text-3xl font-bold text-white">{t.settings.title}</h1>
        <p className="text-sm text-slate-400 mt-1">{t.settings.subtitle}</p>
      </div>

      <div className="space-y-6 max-w-3xl">
        <div className="glass-card rounded-2xl p-6 space-y-4">
          <h2 className="text-base font-semibold text-white flex items-center gap-2">
            <Globe className="w-4 h-4 text-cyan-300" />
            Interface & Explanation Language (8 Languages)
          </h2>
          <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
            {LANGUAGES.map((l) => (
              <button
                key={l.code}
                type="button"
                onClick={() => setLanguage(l.code)}
                className={`p-3 rounded-xl border text-left transition ${
                  language === l.code
                    ? "bg-cyan-500/20 border-cyan-400 text-white"
                    : "bg-slate-900/60 border-slate-800 text-slate-300 hover:border-slate-600"
                }`}
              >
                <div className="text-sm font-semibold">{l.native}</div>
                <div className="text-[11px] text-slate-400">{l.label}</div>
              </button>
            ))}
          </div>
        </div>

        <div className="glass-card rounded-2xl p-6 space-y-4">
          <h2 className="text-base font-semibold text-white flex items-center gap-2">
            <ShieldCheck className="w-4 h-4 text-teal-300" />
            Privacy, Auto-Deletion & AI Engine Status
          </h2>

          <div>
            <label className="block text-xs font-medium text-slate-300 mb-2">
              Automatic Document Deletion Window (Days): <span className="font-mono text-cyan-300">{retentionDays} days</span>
            </label>
            <input
              type="range"
              min="1"
              max="365"
              value={retentionDays}
              onChange={(e) => setRetentionDays(e.target.value)}
              className="w-full accent-cyan-400"
            />
          </div>

          <div className="rounded-xl bg-slate-900/70 border border-slate-800 p-4 text-xs space-y-1.5">
            <div className="text-slate-300">
              <strong>Backend AI Status:</strong>{" "}
              {healthInfo?.gemini_configured
                ? `Gemini API active (${healthInfo.gemini_model}) via secure server-side key`
                : "Running deterministic clinical parser + grounded fallback (set GEMINI_API_KEY in backend/.env to enable live Gemini API)"}
            </div>
            <div className="text-slate-400">
              API keys are stored exclusively on the backend server and are never exposed to the browser.
            </div>
          </div>

          {savedMsg && (
            <div className="flex items-center gap-2 text-xs text-emerald-300">
              <CheckCircle2 className="w-4 h-4" />
              {savedMsg}
            </div>
          )}

          <button
            onClick={handleSave}
            className="px-5 py-2.5 rounded-xl bg-gradient-to-r from-teal-400 to-cyan-400 text-slate-950 font-bold text-sm hover:brightness-110 transition"
          >
            {t.settings.saveBtn}
          </button>
        </div>

        <div className="glass-card rounded-2xl p-6 border-rose-500/25 space-y-3">
          <h2 className="text-base font-semibold text-rose-300 flex items-center gap-2">
            <Trash2 className="w-4 h-4" />
            Data Deletion Control
          </h2>
          <p className="text-xs text-slate-300">
            Permanently erase your user account, uploaded files, extracted entities, and analysis history.
          </p>
          {!confirmDelete ? (
            <button
              onClick={() => setConfirmDelete(true)}
              className="px-4 py-2 rounded-xl bg-rose-500/15 border border-rose-400/30 text-rose-200 text-xs font-semibold hover:bg-rose-500/25 transition"
            >
              {t.settings.deleteAllBtn}
            </button>
          ) : (
            <div className="flex items-center gap-3">
              <button
                onClick={handleDeleteAccount}
                className="px-4 py-2 rounded-xl bg-rose-600 text-white text-xs font-bold"
              >
                Confirm Permanent Deletion
              </button>
              <button
                onClick={() => setConfirmDelete(false)}
                className="px-4 py-2 rounded-xl bg-slate-800 text-slate-300 text-xs"
              >
                Cancel
              </button>
            </div>
          )}
        </div>
      </div>
    </Layout>
  );
}
