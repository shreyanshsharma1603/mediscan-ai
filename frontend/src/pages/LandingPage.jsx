import React from "react";
import { Link } from "react-router-dom";
import { motion } from "framer-motion";
import {
  Activity,
  ArrowRight,
  FileSearch,
  GitCompare,
  Globe,
  Pill,
  ShieldCheck,
  Sparkles,
  Stethoscope,
} from "lucide-react";
import { useApp } from "../context/AppContext";
import { LANGUAGES } from "../i18n/translations";

export default function LandingPage() {
  const { user, language, setLanguage, t } = useApp();

  const capabilities = [
    {
      icon: FileSearch,
      title: "OCR & 7 Clinical Pipelines",
      desc: "Blood tests, urine reports, prescriptions, written radiology reports, discharge summaries, and clinical notes.",
    },
    {
      icon: ShieldCheck,
      title: "Printed Range Verification",
      desc: "Compares values strictly against printed reference ranges—never invents missing intervals or diagnoses.",
    },
    {
      icon: GitCompare,
      title: "Unit-Safe Comparisons",
      desc: "Tracks changes across reports and timelines while automatically blocking incompatible measurement units.",
    },
    {
      icon: Globe,
      title: "8-Language Intelligence",
      desc: "Full interface and plain-language summaries in English, Hindi, Bengali, Tamil, Telugu, Marathi, Spanish, and French.",
    },
    {
      icon: Pill,
      title: "Prescription Reader",
      desc: "Extracts medicine names, dosages, and schedules verbatim with uncertainty flags for unclear lines.",
    },
    {
      icon: Stethoscope,
      title: "Clinician PDF Summary",
      desc: "Exports concise doctor-ready PDF summaries listing extracted values, uncertainties, and patient questions.",
    },
  ];

  return (
    <div className="min-h-screen flex flex-col">
      <header className="border-b border-cyan-500/15 bg-[#060d1b]/80 backdrop-blur-md sticky top-0 z-30">
        <div className="max-w-7xl mx-auto px-6 py-4 flex items-center justify-between gap-4">
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 rounded-xl bg-gradient-to-br from-teal-400 to-cyan-500 flex items-center justify-center shadow-lg shadow-cyan-500/25">
              <Activity className="w-5 h-5 text-slate-950" />
            </div>
            <div>
              <span className="font-bold text-lg text-white">{t.brand}</span>
              <span className="hidden sm:inline text-xs text-cyan-300/80 ml-2.5">
                {t.tagline}
              </span>
            </div>
          </div>

          <div className="flex items-center gap-3">
            <select
              value={language}
              onChange={(e) => setLanguage(e.target.value)}
              className="bg-slate-900 border border-cyan-500/25 rounded-xl px-3 py-1.5 text-xs text-slate-100"
            >
              {LANGUAGES.map((l) => (
                <option key={l.code} value={l.code}>
                  {l.native}
                </option>
              ))}
            </select>
            <Link
              to={user ? "/dashboard" : "/auth"}
              className="px-4 py-2 rounded-xl bg-gradient-to-r from-teal-500 to-cyan-500 text-slate-950 text-sm font-semibold hover:brightness-110 transition"
            >
              {user ? t.nav.dashboard : t.nav.login}
            </Link>
          </div>
        </div>
      </header>

      <main className="flex-1 max-w-7xl mx-auto px-6 py-14 sm:py-20 w-full">
        <motion.div
          initial={{ opacity: 0, y: 18 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.45 }}
          className="max-w-3xl"
        >
          <div className="inline-flex items-center gap-2 px-3.5 py-1.5 rounded-full bg-cyan-500/10 border border-cyan-400/25 text-cyan-200 text-xs font-medium mb-6">
            <Sparkles className="w-3.5 h-3.5 text-cyan-300" />
            {t.landing.badge}
          </div>
          <h1 className="text-4xl sm:text-5xl lg:text-6xl font-extrabold tracking-tight text-white leading-[1.1] mb-6">
            {t.landing.heroTitle}
          </h1>
          <p className="text-base sm:text-lg text-slate-300 leading-relaxed mb-8">
            {t.landing.heroSubtitle}
          </p>

          <div className="flex flex-wrap items-center gap-4">
            <Link
              to={user ? "/upload" : "/auth"}
              className="inline-flex items-center gap-2 px-6 py-3.5 rounded-xl bg-gradient-to-r from-teal-400 to-cyan-400 text-slate-950 font-bold text-sm shadow-lg shadow-cyan-500/25 hover:brightness-110 transition"
            >
              {t.landing.ctaPrimary}
              <ArrowRight className="w-4 h-4" />
            </Link>
            <Link
              to={user ? "/dashboard" : "/auth"}
              className="inline-flex items-center gap-2 px-6 py-3.5 rounded-xl bg-slate-900/90 border border-cyan-500/25 text-slate-100 font-semibold text-sm hover:border-cyan-400/50 transition"
            >
              {t.landing.ctaSecondary}
            </Link>
          </div>
        </motion.div>

        <section className="mt-16">
          <h2 className="text-xl font-bold text-white mb-6">{t.landing.featuresTitle}</h2>
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-5">
            {capabilities.map((cap, idx) => {
              const Icon = cap.icon;
              return (
                <motion.div
                  key={cap.title}
                  initial={{ opacity: 0, y: 12 }}
                  animate={{ opacity: 1, y: 0 }}
                  transition={{ delay: 0.05 * idx }}
                  className="glass-card glass-card-hover rounded-2xl p-6"
                >
                  <div className="w-10 h-10 rounded-xl bg-cyan-500/15 border border-cyan-400/25 flex items-center justify-center mb-4">
                    <Icon className="w-5 h-5 text-cyan-300" />
                  </div>
                  <h3 className="text-base font-semibold text-white mb-2">{cap.title}</h3>
                  <p className="text-sm text-slate-300/90 leading-relaxed">{cap.desc}</p>
                </motion.div>
              );
            })}
          </div>
        </section>

        <div className="mt-14 rounded-2xl bg-amber-500/10 border border-amber-400/25 p-5 text-xs sm:text-sm text-amber-200/90">
          <strong className="text-amber-300">Healthcare Safety Notice:</strong> {t.disclaimerShort}
        </div>
      </main>
    </div>
  );
}
