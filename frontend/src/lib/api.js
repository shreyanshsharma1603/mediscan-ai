const API_BASE = import.meta.env.VITE_API_BASE || "";

export function getToken() {
  return localStorage.getItem("mediscan_token");
}

export function setToken(token) {
  if (token) {
    localStorage.setItem("mediscan_token", token);
  } else {
    localStorage.removeItem("mediscan_token");
  }
}

export async function apiFetch(path, options = {}) {
  const token = getToken();
  const headers = new Headers(options.headers || {});
  if (token) {
    headers.set("Authorization", `Bearer ${token}`);
  }
  if (!(options.body instanceof FormData) && !headers.has("Content-Type") && options.body) {
    headers.set("Content-Type", "application/json");
  }

  const res = await fetch(`${API_BASE}${path}`, {
    ...options,
    headers,
  });

  if (!res.ok) {
    let detail = `Request failed (${res.status})`;
    try {
      const errData = await res.json();
      detail = errData.detail || detail;
    } catch {
      // ignore json parse error
    }
    const err = new Error(detail);
    err.status = res.status;
    throw err;
  }

  const ct = res.headers.get("content-type") || "";
  if (ct.includes("application/json")) {
    return res.json();
  }
  return res;
}

export function uploadWithProgress(file, { language, consentConfirmed, onProgress }) {
  return new Promise((resolve, reject) => {
    const xhr = new XMLHttpRequest();
    xhr.open("POST", `${API_BASE}/api/documents/upload`);
    const token = getToken();
    if (token) {
      xhr.setRequestHeader("Authorization", `Bearer ${token}`);
    }

    xhr.upload.onprogress = (evt) => {
      if (evt.lengthComputable && onProgress) {
        onProgress(Math.round((evt.loaded / evt.total) * 100));
      }
    };

    xhr.onload = () => {
      try {
        const data = JSON.parse(xhr.responseText || "{}");
        if (xhr.status >= 200 && xhr.status < 300) {
          resolve(data);
        } else {
          reject(new Error(data.detail || `Upload failed (${xhr.status})`));
        }
      } catch {
        reject(new Error(`Upload failed (${xhr.status})`));
      }
    };

    xhr.onerror = () => reject(new Error("Network error during upload"));

    const form = new FormData();
    form.append("file", file);
    if (language) form.append("language", language);
    form.append("consent_confirmed", consentConfirmed ? "true" : "false");
    xhr.send(form);
  });
}

export async function fetchAuthorizedBlobUrl(path) {
  const res = await apiFetch(path);
  const blob = await res.blob();
  return URL.createObjectURL(blob);
}
