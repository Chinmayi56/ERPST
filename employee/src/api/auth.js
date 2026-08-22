import api from "./axios";

export const employeeLogin = (email, password) =>
  api.post("/auth/employee/login", { email, password }).then((res) => res.data);

// Public, unauthenticated -- used to poll application status before a login
// account exists (pre-approval, there is no JWT yet).
export const getApplicationStatus = (email) =>
  api.get("/auth/employee/application-status", { params: { email } }).then((res) => res.data);

export const logout = () => api.post("/auth/logout").then((res) => res.data);

export const getMe = () => api.get("/auth/me").then((res) => res.data);
