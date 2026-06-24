export function safeError(error) {
  if (!error) return "Unknown error";

  const data = error?.response?.data;

  if (!data) {
    return error.message || "Network error";
  }

  const detail = data?.detail;

  if (Array.isArray(detail)) {
    return detail
      .map(d => d?.msg || JSON.stringify(d))
      .join(", ");
  }

  if (typeof detail === "string") {
    return detail;
  }

  if (typeof detail === "object") {
    return detail?.msg || detail?.message || JSON.stringify(detail);
  }

  return "Server error";
}
