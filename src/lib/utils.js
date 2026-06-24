import { clsx } from "clsx";
import { twMerge } from "tailwind-merge";

// Tailwind class merge helper
export function cn(...inputs) {
  return twMerge(clsx(inputs));
}

// Currency formatter for dashboards
export function formatCurrency(value, currency = "KES") {
  if (value == null || isNaN(value)) return `${currency} 0`;

  return new Intl.NumberFormat("en-KE", {
    style: "currency",
    currency,
    minimumFractionDigits: 0,
  }).format(value);
}

// API base URL
export const API_URL =
  process.env.REACT_APP_API_URL || "http://localhost:8001";
