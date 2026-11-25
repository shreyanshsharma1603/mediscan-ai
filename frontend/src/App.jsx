import React from "react";
import { BrowserRouter, Navigate, Route, Routes } from "react-router-dom";
import { AppProvider, useApp } from "./context/AppContext";
import LandingPage from "./pages/LandingPage";
import AuthPage from "./pages/AuthPage";
import DashboardPage from "./pages/DashboardPage";
import UploadPage from "./pages/UploadPage";
import DocumentAnalysisPage from "./pages/DocumentAnalysisPage";
import DetailedResultsPage from "./pages/DetailedResultsPage";
import CompareReportsPage from "./pages/CompareReportsPage";
import TimelinePage from "./pages/TimelinePage";
import PrescriptionReaderPage from "./pages/PrescriptionReaderPage";
import DoctorSummaryPage from "./pages/DoctorSummaryPage";
import SettingsPage from "./pages/SettingsPage";

function ProtectedRoute({ children }) {
  const { user, loading } = useApp();
  if (loading) {
    return (
      <div className="min-h-screen flex items-center justify-center text-sm text-cyan-300">
        Initializing MediScan AI...
      </div>
    );
  }
  if (!user) {
    return <Navigate to="/auth" replace />;
  }
  return children;
}

export default function App() {
  return (
    <AppProvider>
      <BrowserRouter>
        <Routes>
          <Route path="/" element={<LandingPage />} />
          <Route path="/auth" element={<AuthPage />} />
          <Route
            path="/dashboard"
            element={
              <ProtectedRoute>
                <DashboardPage />
              </ProtectedRoute>
            }
          />
          <Route
            path="/upload"
            element={
              <ProtectedRoute>
                <UploadPage />
              </ProtectedRoute>
            }
          />
          <Route
            path="/documents/:id"
            element={
              <ProtectedRoute>
                <DocumentAnalysisPage />
              </ProtectedRoute>
            }
          />
          <Route
            path="/documents/:id/results"
            element={
              <ProtectedRoute>
                <DetailedResultsPage />
              </ProtectedRoute>
            }
          />
          <Route
            path="/compare"
            element={
              <ProtectedRoute>
                <CompareReportsPage />
              </ProtectedRoute>
            }
          />
          <Route
            path="/timeline"
            element={
              <ProtectedRoute>
                <TimelinePage />
              </ProtectedRoute>
            }
          />
          <Route
            path="/prescriptions"
            element={
              <ProtectedRoute>
                <PrescriptionReaderPage />
              </ProtectedRoute>
            }
          />
          <Route
            path="/doctor-summary"
            element={
              <ProtectedRoute>
                <DoctorSummaryPage />
              </ProtectedRoute>
            }
          />
          <Route
            path="/settings"
            element={
              <ProtectedRoute>
                <SettingsPage />
              </ProtectedRoute>
            }
          />
          <Route path="*" element={<Navigate to="/" replace />} />
        </Routes>
      </BrowserRouter>
    </AppProvider>
  );
}
