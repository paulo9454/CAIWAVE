import axios from "axios";

const API = process.env.REACT_APP_BACKEND_URL;

export const demoPay = async (data) => {
  const res = await axios.post(`${API}/demo/pay`, data);
  return res.data;
};

export const demoSession = async (data) => {
  const res = await axios.post(`${API}/demo/session`, data);
  return res.data;
};

export const demoStatus = async () => {
  const res = await axios.get(`${API}/demo/status`);
  return res.data;
};
