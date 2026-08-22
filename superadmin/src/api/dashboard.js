import api from "./axios";

export const getDashboardSummary = () =>
  api.get("/superadmin/dashboard").then((res) => res.data);
