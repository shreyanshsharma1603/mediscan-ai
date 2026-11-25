import React, { createContext, useContext, useEffect, useState } from "react";
import { apiFetch, getToken, setToken } from "../lib/api";
import { getTranslations } from "../i18n/translations";

const AppContext = createContext(null);

export function AppProvider({ children }) {
  const [user, setUser] = useState(null);
  const [loading, setLoading] = useState(true);
  const [language, setLanguageState] = useState(
    localStorage.getItem("mediscan_lang") || "en"
  );
  const [healthInfo, setHealthInfo] = useState(null);

  useEffect(() => {
    apiFetch("/api/health").then(setHealthInfo).catch(() => {});
    const token = getToken();
    if (!token) {
      setLoading(false);
      return;
    }
    apiFetch("/api/auth/me")
      .then((u) => {
        setUser(u);
        if (u.preferred_language) {
          setLanguageState(u.preferred_language);
          localStorage.setItem("mediscan_lang", u.preferred_language);
        }
      })
      .catch(() => {
        setToken(null);
        setUser(null);
      })
      .finally(() => setLoading(false));
  }, []);

  const setLanguage = async (nextLang) => {
    setLanguageState(nextLang);
    localStorage.setItem("mediscan_lang", nextLang);
    if (user) {
      try {
        const updated = await apiFetch("/api/auth/preferences", {
          method: "PATCH",
          body: JSON.stringify({ preferred_language: nextLang }),
        });
        setUser(updated);
      } catch {
        // ignore background preference sync error
      }
    }
  };

  const loginSuccess = (authPayload) => {
    setToken(authPayload.access_token);
    setUser(authPayload.user);
    if (authPayload.user?.preferred_language) {
      setLanguageState(authPayload.user.preferred_language);
      localStorage.setItem("mediscan_lang", authPayload.user.preferred_language);
    }
  };

  const logout = () => {
    setToken(null);
    setUser(null);
  };

  const t = getTranslations(language);

  return (
    <AppContext.Provider
      value={{
        user,
        setUser,
        loading,
        language,
        setLanguage,
        t,
        healthInfo,
        loginSuccess,
        logout,
      }}
    >
      {children}
    </AppContext.Provider>
  );
}

export function useApp() {
  return useContext(AppContext);
}
