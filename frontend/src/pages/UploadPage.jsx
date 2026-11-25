import React, { useEffect, useRef, useState } from "react";
import { useNavigate } from "react-router-dom";
import { AlertCircle, CheckCircle2, FileText, FileUp, ShieldCheck } from "lucide-react";
import Layout from "../components/Layout";
import { useApp } from "../context/AppContext";
import { uploadWithProgress } from "../lib/api";

const ALLOWED_TYPES = ["application/pdf", "image/jpeg", "image/jpg", "image/png"];
const MAX_MB = 15;

export default function UploadPage() {
  const { language, t } = useApp();
  const navigate = useNavigate();
  const inputRef = useRef(null);

  const [file, setFile] = useState(null);
  const [previewUrl, setPreviewUrl] = useState(null);
  const [dragOver, setDragOver] = useState(false);
  const [consent, setConsent] = useState(true);
  const [progress, setProgress] = useState(0);
  const [uploading, setUploading] = useState(false);
  const [error, setError] = useState("");

  useEffect(() => {
    return () => {
      if (previewUrl) URL.revokeObjectURL(previewUrl);
    };
  }, [previewUrl]);

  const handleSelectFile = (selected) => {
    setError("");
    if (!selected) return;

    const ext = selected.name.split(".").pop()?.toLowerCase();
    if (!["pdf", "jpg", "jpeg", "png"].includes(ext || "") && !ALLOWED_TYPES.includes(selected.type)) {
      setError("Unsupported file format. Please select a PDF, JPG, JPEG, or PNG report.");
      return;
    }
    if (selected.size === 0) {
      setError("Selected file is empty (0 bytes).");
      return;
    }
    if (selected.size > MAX_MB * 1024 * 1024) {
      setError(`File size exceeds the ${MAX_MB} MB limit.`);
      return;
    }

    if (previewUrl) URL.revokeObjectURL(previewUrl);
    setFile(selected);
    setPreviewUrl(URL.createObjectURL(selected));
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (!file) {
      setError("Please select a medical document first.");
      return;
    }
    if (!consent) {
      setError("Please confirm the informational consent checkbox before uploading.");
      return;
    }

    setUploading(true);
    setProgress(10);
    setError("");
    try {
      const doc = await uploadWithProgress(file, {
        language,
        consentConfirmed: consent,
        onProgress: (pct) => setProgress(Math.max(15, Math.min(95, pct))),
      });
      setProgress(100);
      navigate(`/documents/${doc.id}`);
    } catch (err) {
      setError(err.message);
      setProgress(0);
    } finally {
      setUploading(false);
    }
  };

  return (
    <Layout>
      <div className="mb-8">
        <h1 className="text-2xl sm:text-3xl font-bold text-white">{t.upload.title}</h1>
        <p className="text-sm text-slate-400 mt-1">{t.upload.subtitle}</p>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <form onSubmit={handleSubmit} className="glass-card rounded-2xl p-6 space-y-5">
          <div
            onDragOver={(e) => {
              e.preventDefault();
              setDragOver(true);
            }}
            onDragLeave={() => setDragOver(false)}
            onDrop={(e) => {
              e.preventDefault();
              setDragOver(false);
              handleSelectFile(e.dataTransfer.files?.[0]);
            }}
            onClick={() => inputRef.current?.click()}
            className={`cursor-pointer rounded-2xl border-2 border-dashed p-8 text-center transition ${
              dragOver
                ? "border-cyan-400 bg-cyan-500/10"
                : "border-slate-700 hover:border-cyan-500/50 bg-slate-900/40"
            }`}
          >
            <input
              ref={inputRef}
              type="file"
              accept=".pdf,.jpg,.jpeg,.png"
              className="hidden"
              onChange={(e) => handleSelectFile(e.target.files?.[0])}
            />
            <div className="w-12 h-12 rounded-2xl bg-cyan-500/15 border border-cyan-400/25 flex items-center justify-center mx-auto mb-4">
              <FileUp className="w-6 h-6 text-cyan-300" />
            </div>
            <p className="text-sm font-medium text-white mb-1">{t.upload.dropzone}</p>
            <p className="text-xs text-slate-400">{t.upload.formats}</p>
          </div>

          {file && (
            <div className="flex items-center justify-between p-3.5 rounded-xl bg-slate-900/70 border border-cyan-500/20 text-xs">
              <div className="flex items-center gap-2.5 truncate">
                <CheckCircle2 className="w-4 h-4 text-emerald-400 shrink-0" />
                <span className="text-white font-medium truncate">{file.name}</span>
              </div>
              <span className="text-slate-400 font-mono shrink-0 ml-2">
                {(file.size / 1024).toFixed(1)} KB
              </span>
            </div>
          )}

          {uploading && (
            <div className="space-y-2">
              <div className="flex justify-between text-xs text-cyan-200">
                <span>{t.upload.uploading}</span>
                <span className="font-mono">{progress}%</span>
              </div>
              <div className="h-2 rounded-full bg-slate-800 overflow-hidden">
                <div
                  className="h-full bg-gradient-to-r from-teal-400 to-cyan-400 transition-all duration-300"
                  style={{ width: `${progress}%` }}
                />
              </div>
            </div>
          )}

          {error && (
            <div className="flex items-start gap-2 rounded-xl bg-rose-500/15 border border-rose-400/30 p-3.5 text-xs text-rose-200">
              <AlertCircle className="w-4 h-4 shrink-0 mt-0.5 text-rose-300" />
              <span>{error}</span>
            </div>
          )}

          <label className="flex items-start gap-2.5 p-3.5 rounded-xl bg-slate-900/60 border border-slate-800 text-xs text-slate-300 cursor-pointer">
            <input
              type="checkbox"
              checked={consent}
              onChange={(e) => setConsent(e.target.checked)}
              className="mt-0.5 accent-cyan-400"
            />
            <span>{t.upload.consentCheck}</span>
          </label>

          <button
            type="submit"
            disabled={uploading || !file}
            className="w-full py-3.5 rounded-xl bg-gradient-to-r from-teal-400 to-cyan-400 text-slate-950 font-bold text-sm hover:brightness-110 transition disabled:opacity-50"
          >
            {uploading ? t.upload.uploading : t.upload.analyzeBtn}
          </button>

          <div className="flex items-center gap-2 text-[11px] text-slate-400">
            <ShieldCheck className="w-4 h-4 text-teal-400 shrink-0" />
            <span>
              Radiology PDFs/images analyze written radiologist report text only, not raw diagnostic imaging pixels.
            </span>
          </div>
        </form>

        <div className="glass-card rounded-2xl p-6 flex flex-col min-h-[420px]">
          <h2 className="text-sm font-semibold text-white mb-4 flex items-center gap-2">
            <FileText className="w-4 h-4 text-cyan-300" />
            Document Preview
          </h2>
          {!previewUrl ? (
            <div className="flex-1 rounded-xl bg-slate-900/50 border border-slate-800 flex items-center justify-center text-xs text-slate-500">
              Select a PDF or image to preview it before OCR extraction.
            </div>
          ) : file?.type === "application/pdf" || file?.name.toLowerCase().endsWith(".pdf") ? (
            <iframe
              src={previewUrl}
              title="PDF Preview"
              className="flex-1 w-full min-h-[380px] rounded-xl border border-slate-800 bg-white"
            />
          ) : (
            <div className="flex-1 rounded-xl bg-slate-950 border border-slate-800 p-2 flex items-center justify-center overflow-hidden">
              <img
                src={previewUrl}
                alt="Medical Document Preview"
                className="max-h-[420px] object-contain rounded-lg"
              />
            </div>
          )}
        </div>
      </div>
    </Layout>
  );
}
