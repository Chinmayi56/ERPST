import api from "./axios";

export const listApplications = (status) =>
  api
    .get("/subadmin/applications", { params: status ? { status } : {} })
    .then((res) => res.data);

export const getApplication = (applicationId) =>
  api.get(`/subadmin/applications/${applicationId}`).then((res) => res.data);

export const approveApplication = (applicationId) =>
  api.post(`/subadmin/applications/${applicationId}/approve`).then((res) => res.data);

export const rejectApplication = (applicationId, reason) =>
  api
    .post(`/subadmin/applications/${applicationId}/reject`, { reason })
    .then((res) => res.data);
