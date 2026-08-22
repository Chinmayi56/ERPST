import api from "./axios";

export const listEmployees = (status) =>
  api
    .get("/subadmin/employees", { params: status ? { status } : {} })
    .then((res) => res.data);

export const getEmployee = (employeeId) =>
  api.get(`/subadmin/employees/${employeeId}`).then((res) => res.data);

export const updateEmployee = (employeeId, updates) =>
  api.patch(`/subadmin/employees/${employeeId}`, updates).then((res) => res.data);

export const disableEmployee = (employeeId) =>
  api.post(`/subadmin/employees/${employeeId}/disable`).then((res) => res.data);
