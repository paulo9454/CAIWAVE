import { API_URL } from "./utils";
import axios from "axios";

const TOKEN_KEY = "caitech_token";
const USER_KEY = "caitech_user";

export const setAuthToken = (token) => {
  localStorage.setItem(TOKEN_KEY, token);
  axios.defaults.headers.common["Authorization"] = `Bearer ${token}`;
};

export const getAuthToken = () => {
  return localStorage.getItem(TOKEN_KEY);
};

export const setUser = (user) => {
  localStorage.setItem(USER_KEY, JSON.stringify(user));
};

export const getUser = () => {
  const user = localStorage.getItem(USER_KEY);
  return user ? JSON.parse(user) : null;
};

export const clearAuth = () => {
  localStorage.removeItem(TOKEN_KEY);
  localStorage.removeItem(USER_KEY);
  delete axios.defaults.headers.common["Authorization"];
};

export const isAuthenticated = () => {
  const token = getAuthToken();
  return !!token;
};

export const initializeAuth = () => {
  const token = getAuthToken();
  if (token) {
    axios.defaults.headers.common["Authorization"] = `Bearer ${token}`;
  }
};

export const login = async (email, password) => {
  const response = await axios.post(`${API_URL}/auth/login`, {
    email,
    password,
  });
  const { token, user } = response.data;
  setAuthToken(token);
  setUser(user);
  return user;
};

export const register = async (userData) => {
  const response = await axios.post(`${API_URL}/auth/register`, userData);
  const { token, user } = response.data;
  setAuthToken(token);
  setUser(user);
  return user;
};

export const logout = () => {
  clearAuth();
  window.location.href = "/login";
};

export const getCurrentUser = async () => {
  const response = await axios.get(`${API_URL}/auth/me`);
  setUser(response.data);
  return response.data;
};

export const ROLES = {
  SUPER_ADMIN: "super_admin",
  HOTSPOT_OWNER: "hotspot_owner",
  ADVERTISER: "advertiser",
  END_USER: "end_user",
};

export const hasRole = (user, roles) => {
  if (!user) return false;
  if (typeof roles === "string") return user.role === roles;
  return roles.includes(user.role);
};

export const getRoleName = (role) => {
  const names = {
    super_admin: "Super Admin",
    hotspot_owner: "Hotspot Owner",
    advertiser: "Advertiser",
    end_user: "User",
  };
  return names[role] || role;
};

export const getDashboardPath = (role) => {
  const paths = {
    super_admin: "/admin",
    hotspot_owner: "/owner",
    advertiser: "/advertiser",
    end_user: "/",
  };
  return paths[role] || "/";
};
