import React, { useState } from "react";
import { Link, useLocation, useNavigate } from "react-router-dom";
import {
  Activity,
  FilePlus2,
  FileText,
  GitCompare,
  Globe,
  LayoutDashboard,
  LogOut,
  Menu,
  Pill,
  Settings,
  ShieldAlert,
  Stethoscope,
  X,
} from "lucide-react";
import { useApp } from "../context/AppContext";
import { LANGUAGES } from "../i18n/translations";

export default function Layout({ children }) {
  const { user, language, setLanguage, t, logout } = useApp();
  const location = useLocation();
  const navigate = useNavigate();
  const [mobileOpen, setMobileOpen] = useState(false);

  const navItems = [
    { to: "/dashboard", label: t.nav.dashboard, icon: LayoutDashboard },
    { to: "/upload", label: t.nav.upload, icon: FilePlus2 },
    { to: "/compare", label: t.nav.compare, icon: GitCompare },
    { to: "/timeline", label: t.nav.timeline, icon: Activity },
    { to: "/prescriptions", label: t.nav.prescriptions, icon: Pill },
    { to: "/doctor-summary", label: t.nav.doctorSummary, icon: Stethoscope },
    { to: "/settings", label: t.nav.settings, icon: Settings },
  ];

  const handleLogout = () => {
    logout();
    navigate("/");
  };

  return (
    <div className="min-h-screen flex flex-col lg:flex-row">
      {/* Desktop Sidebar */}
      <aside className="hidden lg:flex lg:w-64 lg:flex-col lg:fixed lg:inset-y-0 bg-[#071022]/95 border-r border-cyan-500/15 px-4 py-6 z-30">
        <Link to="/" className="flex items-center gap-3 px-2 mb-8">
          <div className="w-10 h-10 rounded-xl bg-gradient-to-br from-teal-400 to-cyan-500 flex items-center justify-center shadow-lg shadow-cyan-500/20">
            <FileText className="w-5 h-5 text-slate-950" />
          </div>
          <div>
            <div className="text-base font-bold tracking-tight text-white">{t.brand}</div>
            <div className="text-[11px] text-cyan-300/80">Document Intelligence</div>
          </div>
        </Link>

        <nav className="flex-1 space-y-1.5">
          {navItems.map((item) => {
            const Icon = item.icon;
            const active = location.pathname === item.to || (item.to !== "/dashboard" && location.pathname.startsWith(item.to));
            return (
              <Link
                key={item.to}
                to={item.to}
                className={`flex items-center gap-3 px-3.5 py-2.5 rounded-xl text-sm font-medium transition-all ${
                  active
                    ? "bg-gradient-to-r from-teal-500/20 to-cyan-500/15 text-cyan-200 border border-cyan-400/30 shadow-sm"
                    : "text-slate-300 hover:text-white hover:bg-slate-800/60 border border-transparent"
                }`}
              >
                <Icon className={`w-4 h-4 ${active ? "text-cyan-300" : "text-slate-400"}`} />
                <span>{item.label}</span>
              </Link>
            );
          })}
        </nav>

        <div className="mt-6 pt-4 border-t border-slate-800 space-y-3">
          {user && (
            <div className="px-2">
              <div className="text-xs font-semibold text-white truncate">{user.full_name}</div>
              <div className="text-[11px] text-slate-400 truncate">{user.email}</div>
            </div>
          )}
          <button
            onClick={handleLogout}
            className="w-full flex items-center gap-2.5 px-3.5 py-2 rounded-xl text-sm text-rose-300 hover:bg-rose-500/10 border border-transparent hover:border-rose-500/25 transition"
          >
            <LogOut className="w-4 h-4" />
            <span>{t.nav.logout}</span>
          </button>
        </div>
      </aside>

      {/* Main Content Area */}
      <div className="flex-1 lg:pl-64 flex flex-col min-h-screen">
        {/* Top Header Bar */}
        <header className="sticky top-0 z-20 bg-[#060d1b]/85 backdrop-blur-md border-b border-cyan-500/10 px-4 sm:px-6 py-3 flex items-center justify-between gap-4">
          <div className="flex items-center gap-3">
            <button
              onClick={() => setMobileOpen(!mobileOpen)}
              className="lg:hidden p-2 rounded-lg bg-slate-800/70 text-slate-200"
              aria-label="Toggle Menu"
            >
              {mobileOpen ? <X className="w-5 h-5" /> : <Menu className="w-5 h-5" />}
            </button>
            <div className="hidden sm:flex items-center gap-2 text-xs text-amber-200/90 bg-amber-500/10 border border-amber-400/25 rounded-full px-3 py-1">
              <ShieldAlert className="w-3.5 h-3.5 text-amber-300 shrink-0" />
              <span className="truncate max-w-xl">{t.disclaimerShort}</span>
            </div>
          </div>

          <div className="flex items-center gap-3 ml-auto">
            <div className="flex items-center gap-1.5 bg-slate-900/90 border border-cyan-500/20 rounded-xl px-2.5 py-1.5">
              <Globe className="w-4 h-4 text-cyan-400" />
              <select
                value={language}
                onChange={(e) => setLanguage(e.target.value)}
                aria-label="Select Language"
                className="bg-transparent text-xs font-medium text-slate-100 focus:outline-none cursor-pointer"
              >
                {LANGUAGES.map((l) => (
                  <option key={l.code} value={l.code} className="bg-slate-900 text-slate-100">
                    {l.native} ({l.label})
                  </option>
                ))}
              </select>
            </div>
          </div>
        </header>

        {/* Mobile Drawer */}
        {mobileOpen && (
          <div className="lg:hidden bg-[#081326] border-b border-cyan-500/20 px-4 py-3 space-y-1">
            {navItems.map((item) => {
              const Icon = item.icon;
              return (
                <Link
                  key={item.to}
                  to={item.to}
                  onClick={() => setMobileOpen(false)}
                  className="flex items-center gap-3 px-3 py-2 rounded-lg text-sm text-slate-200 hover:bg-slate-800"
                >
                  <Icon className="w-4 h-4 text-cyan-400" />
                  <span>{item.label}</span>
                </Link>
              );
            })}
            <button
              onClick={handleLogout}
              className="w-full flex items-center gap-3 px-3 py-2 rounded-lg text-sm text-rose-300 hover:bg-rose-500/10"
            >
              <LogOut className="w-4 h-4" />
              <span>{t.nav.logout}</span>
            </button>
          </div>
        )}

        <main className="flex-1 p-4 sm:p-6 lg:p-8 max-w-7xl w-full mx-auto">
          {children}
        </main>
      </div>
    </div>
  );
}
