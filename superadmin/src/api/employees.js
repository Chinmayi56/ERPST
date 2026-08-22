import api from "./axios";

export const listEmployees = (status) =>
  api
    .get("/superadmin/employees", { params: status ? { status } : {} })
    .then((res) => res.data);

export const getEmployee = (employeeId) =>
  api.get(`/superadmin/employees/${employeeId}`).then((res) => res.data);

export const updateEmployee = (employeeId, updates) =>
  api.patch(`/superadmin/employees/${employeeId}`, updates).then((res) => res.data);

export const disableEmployee = (employeeId) =>
  api.post(`/superadmin/employees/${employeeId}/disable`).then((res) => res.data);
