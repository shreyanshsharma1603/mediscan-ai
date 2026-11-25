import React, { useState } from "react";
import { Link, useNavigate } from "react-router-dom";
import { Activity, AlertCircle, Lock, Mail, ShieldCheck, User } from "lucide-react";
import { apiFetch } from "../lib/api";
import { useApp } from "../context/AppContext";
import { LANGUAGES } from "../i18n/translations";

export default function AuthPage() {
  const { language, loginSuccess, t } = useApp();
  const navigate = useNavigate();
  const [mode, setMode] = useState("register");
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [fullName, setFullName] = useState("");
  const [prefLang, setPrefLang] = useState(language || "en");
  const [consentAccepted, setConsentAccepted] = useState(false);
  const [error, setError] = useState("");
  const [submitting, setSubmitting] = useState(false);

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError("");
    setSubmitting(true);
    try {
      if (mode === "register") {
        if (!consentAccepted) {
          throw new Error("Please accept the informational consent & medical disclaimer.");
        }
        const data = await apiFetch("/api/auth/register", {
          method: "POST",
          body: JSON.stringify({
            email,
            password,
            full_name: fullName,
            preferred_language: prefLang,
            consent_accepted: consentAccepted,
          }),
        });
        loginSuccess(data);
      } else {
        const data = await apiFetch("/api/auth/login", {
          method: "POST",
          body: JSON.stringify({ email, password }),
        });
        loginSuccess(data);
      }
      navigate("/dashboard");
    } catch (err) {
      setError(err.message);
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <div className="min-h-screen flex items-center justify-center p-4">
      <div className="w-full max-w-md glass-card rounded-3xl p-7 sm:p-8 shadow-2xl">
        <Link to="/" className="flex items-center gap-3 mb-6">
          <div className="w-10 h-10 rounded-xl bg-gradient-to-br from-teal-400 to-cyan-500 flex items-center justify-center">
            <Activity className="w-5 h-5 text-slate-950" />
          </div>
          <div>
            <div className="font-bold text-white">{t.brand}</div>
            <div className="text-xs text-cyan-300/80">{t.tagline}</div>
          </div>
        </Link>

        <h1 className="text-2xl font-bold text-white mb-1">
          {mode === "register" ? t.auth.registerTitle : t.auth.signInTitle}
        </h1>
        <p className="text-xs text-slate-400 mb-6">
          Private per-user medical vault with strict access isolation.
        </p>

        {error && (
          <div className="mb-4 flex items-start gap-2 rounded-xl bg-rose-500/15 border border-rose-400/30 p-3 text-xs text-rose-200">
            <AlertCircle className="w-4 h-4 shrink-0 mt-0.5 text-rose-300" />
            <span>{error}</span>
          </div>
        )}

        <form onSubmit={handleSubmit} className="space-y-4">
          {mode === "register" && (
            <div>
              <label className="block text-xs font-medium text-slate-300 mb-1.5">
                {t.auth.fullName}
              </label>
              <div className="relative">
                <User className="w-4 h-4 text-slate-400 absolute left-3.5 top-3" />
                <input
                  type="text"
                  required
                  value={fullName}
                  onChange={(e) => setFullName(e.target.value)}
                  placeholder="Alex Mercer"
                  className="w-full pl-10 pr-3.5 py-2.5 rounded-xl bg-slate-900/90 border border-slate-700 focus:border-cyan-400 text-sm text-white outline-none"
                />
              </div>
            </div>
          )}

          <div>
            <label className="block text-xs font-medium text-slate-300 mb-1.5">
              {t.auth.email}
            </label>
            <div className="relative">
              <Mail className="w-4 h-4 text-slate-400 absolute left-3.5 top-3" />
              <input
                type="email"
                required
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                placeholder="patient@example.com"
                className="w-full pl-10 pr-3.5 py-2.5 rounded-xl bg-slate-900/90 border border-slate-700 focus:border-cyan-400 text-sm text-white outline-none"
              />
            </div>
          </div>

          <div>
            <label className="block text-xs font-medium text-slate-300 mb-1.5">
              {t.auth.password}
            </label>
            <div className="relative">
              <Lock className="w-4 h-4 text-slate-400 absolute left-3.5 top-3" />
              <input
                type="password"
                required
                minLength={6}
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                placeholder="••••••••"
                className="w-full pl-10 pr-3.5 py-2.5 rounded-xl bg-slate-900/90 border border-slate-700 focus:border-cyan-400 text-sm text-white outline-none"
              />
            </div>
          </div>

          {mode === "register" && (
            <>
              <div>
                <label className="block text-xs font-medium text-slate-300 mb-1.5">
                  {t.auth.language}
                </label>
                <select
                  value={prefLang}
                  onChange={(e) => setPrefLang(e.target.value)}
                  className="w-full px-3.5 py-2.5 rounded-xl bg-slate-900/90 border border-slate-700 text-sm text-white outline-none"
                >
                  {LANGUAGES.map((l) => (
                    <option key={l.code} value={l.code}>
                      {l.native} ({l.label})
                    </option>
                  ))}
                </select>
              </div>

              <label className="flex items-start gap-2.5 p-3 rounded-xl bg-slate-900/60 border border-cyan-500/20 text-xs text-slate-300 cursor-pointer">
                <input
                  type="checkbox"
                  checked={consentAccepted}
                  onChange={(e) => setConsentAccepted(e.target.checked)}
                  className="mt-0.5 accent-cyan-400"
                />
                <span>{t.auth.consentLabel}</span>
              </label>
            </>
          )}

          <button
            type="submit"
            disabled={submitting}
            className="w-full py-3 rounded-xl bg-gradient-to-r from-teal-400 to-cyan-400 text-slate-950 font-bold text-sm hover:brightness-110 transition disabled:opacity-60"
          >
            {submitting
              ? "Processing..."
              : mode === "register"
              ? t.auth.registerBtn
              : t.auth.signInBtn}
          </button>
        </form>

        <div className="mt-5 pt-4 border-t border-slate-800 flex items-center justify-between text-xs">
          <button
            type="button"
            onClick={() => {
              setError("");
              setMode(mode === "register" ? "login" : "register");
            }}
            className="text-cyan-300 hover:text-cyan-200 font-medium"
          >
            {mode === "register" ? t.auth.switchToLogin : t.auth.switchToRegister}
          </button>
          <span className="inline-flex items-center gap-1 text-slate-400">
            <ShieldCheck className="w-3.5 h-3.5 text-teal-400" />
            Private Vault
          </span>
        </div>
      </div>
    </div>
  );
}
