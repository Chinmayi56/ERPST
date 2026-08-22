import api from "./axios";

export const listApplications = (status) =>
  api
    .get("/superadmin/applications", { params: status ? { status } : {} })
    .then((res) => res.data);

export const getApplication = (applicationId) =>
  api.get(`/superadmin/applications/${applicationId}`).then((res) => res.data);

export const approveApplication = (applicationId) =>
  api.post(`/superadmin/applications/${applicationId}/approve`).then((res) => res.data);

export const rejectApplication = (applicationId, reason) =>
  api
    .post(`/superadmin/applications/${applicationId}/reject`, { reason })
    .then((res) => res.data);
