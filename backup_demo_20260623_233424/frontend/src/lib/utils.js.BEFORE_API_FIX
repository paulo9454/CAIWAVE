import { clsx } from "clsx";
import { twMerge } from "tailwind-merge";

export function cn(...inputs) {
  return twMerge(clsx(inputs));
}

export const API_URL = `${process.env.REACT_APP_BACKEND_URL}/api`;

export const formatCurrency = (amount, currency = "KES") => {
  return `${currency} ${amount.toLocaleString()}`;
};

export const formatDate = (date) => {
  return new Date(date).toLocaleDateString("en-KE", {
    year: "numeric",
    month: "short",
    day: "numeric",
  });
};

export const formatDateTime = (date) => {
  return new Date(date).toLocaleString("en-KE", {
    year: "numeric",
    month: "short",
    day: "numeric",
    hour: "2-digit",
    minute: "2-digit",
  });
};

export const formatDuration = (minutes) => {
  if (minutes < 60) return `${minutes} min`;
  if (minutes < 1440) return `${Math.floor(minutes / 60)} hr`;
  return `${Math.floor(minutes / 1440)} day`;
};

export const getStatusColor = (status) => {
  const colors = {
    active: "text-green-500",
    completed: "text-green-500",
    pending: "text-yellow-500",
    expired: "text-gray-500",
    failed: "text-red-500",
    cancelled: "text-red-500",
    draft: "text-gray-500",
    paused: "text-yellow-500",
  };
  return colors[status] || "text-gray-500";
};

export const getStatusBadgeClass = (status) => {
  const classes = {
    active: "badge-active",
    completed: "badge-active",
    pending: "badge-pending",
    expired: "badge-inactive",
    failed: "badge-inactive",
    cancelled: "badge-inactive",
    draft: "badge-inactive",
    paused: "badge-pending",
  };
  return classes[status] || "badge-inactive";
};
