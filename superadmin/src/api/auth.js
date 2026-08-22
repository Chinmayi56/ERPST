import api from "./axios";

export const loginWithPassword = (email, password) =>
  api.post("/auth/superadmin/login", { email, password }).then((res) => res.data);

export const sendOtp = (mobile) =>
  api.post("/auth/superadmin/send-otp", { mobile }).then((res) => res.data);

export const verifyOtp = (mobile, otp) =>
  api.post("/auth/superadmin/verify-otp", { mobile, otp }).then((res) => res.data);

export const logout = () => api.post("/auth/logout").then((res) => res.data);

export const getMe = () => api.get("/auth/me").then((res) => res.data);
