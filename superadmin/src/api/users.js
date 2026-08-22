import api from "./axios";

export const listUsers = () => api.get("/superadmin/users").then((res) => res.data);
