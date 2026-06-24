import axios from "axios";

const API = process.env.REACT_APP_BACKEND_URL;

export default axios.create({
  baseURL: API,
});
