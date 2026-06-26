import { clsx } from "clsx";
import { twMerge } from "tailwind-merge";

// Tailwind merge helper
export function cn(...inputs) {
  return twMerge(clsx(inputs));
}

// Currency formatter
export function formatCurrency(value, currency = "KES") {
  if (value == null || isNaN(value)) return `${currency} 0`;

  return new Intl.NumberFormat("en-KE", {
    style: "currency",
    currency,
    minimumFractionDigits: 0,
  }).format(value);
}

// API base URL (single source of truth)
export const API_URL =
  process.env.REACT_APP_BACKEND_URL?.endsWith("/api")
    ? process.env.REACT_APP_BACKEND_URL
    : `${process.env.REACT_APP_BACKEND_URL}/api`;
