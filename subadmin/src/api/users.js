import api from "./axios";

export const listUsers = () => api.get("/subadmin/users").then((res) => res.data);
