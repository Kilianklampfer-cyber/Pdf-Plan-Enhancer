const API_BASE = import.meta.env.VITE_API_BASE_URL || "http://127.0.0.1:8000/api";

async function parseApiError(response) {
  try {
    const payload = await response.json();
    return payload.detail || payload.error || "Die Anfrage konnte nicht verarbeitet werden.";
  } catch {
    return "Die Anfrage konnte nicht verarbeitet werden.";
  }
}

export async function uploadPdf(file) {
  const formData = new FormData();
  formData.append("file", file);

  const response = await fetch(`${API_BASE}/upload`, {
    method: "POST",
    body: formData,
  });

  if (!response.ok) throw new Error(await parseApiError(response));
  return response.json();
}

export async function uploadBatch(files) {
  const formData = new FormData();
  files.forEach((file) => formData.append("files", file));

  const response = await fetch(`${API_BASE}/batch-upload`, {
    method: "POST",
    body: formData,
  });

  if (!response.ok) throw new Error(await parseApiError(response));
  return response.json();
}

export async function requestPreview(fileId, page, params) {
  const response = await fetch(`${API_BASE}/preview`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ file_id: fileId, page, params }),
  });

  if (!response.ok) throw new Error(await parseApiError(response));
  return response.json();
}

export async function exportPdf(fileId, params) {
  const response = await fetch(`${API_BASE}/export`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ file_id: fileId, params }),
  });

  if (!response.ok) throw new Error(await parseApiError(response));
  return response.blob();
}

export async function exportBatch(fileIds, params) {
  const response = await fetch(`${API_BASE}/batch-export`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ file_ids: fileIds, params }),
  });

  if (!response.ok) throw new Error(await parseApiError(response));
  return response.blob();
}
