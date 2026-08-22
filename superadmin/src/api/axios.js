import axios from "axios";

const API_URL = import.meta.env.VITE_API_URL || "http://localhost:8001/api";

const api = axios.create({
  baseURL: API_URL,
});

// Attach JWT to every request if present
api.interceptors.request.use((config) => {
  const token = localStorage.getItem("strivenest_token");
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

// On 401, clear auth state and redirect to login
api.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response && error.response.status === 401) {
      localStorage.removeItem("strivenest_token");
      localStorage.removeItem("strivenest_user");
      if (window.location.pathname !== "/login") {
        window.location.href = "/login";
      }
    }
    return Promise.reject(error);
  }
);

export default api;
