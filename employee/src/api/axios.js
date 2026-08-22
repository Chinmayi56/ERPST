import axios from "axios";

const API_URL = import.meta.env.VITE_API_URL || "http://localhost:8001/api";

const api = axios.create({
  baseURL: API_URL,
});

// Attach the employee JWT to every request if present (post-approval login).
api.interceptors.request.use((config) => {
  const token = localStorage.getItem("strivenest_employee_token");
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

// On 401 (missing/expired/invalid token), clear auth state and send the
// employee back to the login screen.
api.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response && error.response.status === 401) {
      localStorage.removeItem("strivenest_employee_token");
      localStorage.removeItem("strivenest_employee_user");
      if (window.location.pathname !== "/login" && window.location.pathname !== "/register") {
        window.location.href = "/login";
      }
    }
    return Promise.reject(error);
  }
);

export default api;
