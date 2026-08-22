import api from "./axios";

export const getDashboardSummary = () =>
  api.get("/subadmin/dashboard").then((res) => res.data);
