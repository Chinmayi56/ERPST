import api from "./axios";

export const loginWithPassword = (email, password) =>
  api.post("/auth/subadmin/login", { email, password }).then((res) => res.data);

export const sendOtp = (mobile) =>
  api.post("/auth/subadmin/send-otp", { mobile }).then((res) => res.data);

export const verifyOtp = (mobile, otp) =>
  api.post("/auth/subadmin/verify-otp", { mobile, otp }).then((res) => res.data);

export const logout = () => api.post("/auth/logout").then((res) => res.data);

export const getMe = () => api.get("/auth/me").then((res) => res.data);

// Public, unauthenticated: lets the login page show the correct demo OTP
// without hardcoding it, so it can never drift out of sync with the
// backend's actual DEMO_OTP/DEMO_MODE settings. Returns
// { demo_mode: boolean, demo_otp: string | null }.
export const getDemoConfig = () => api.get("/auth/demo-config").then((res) => res.data);

