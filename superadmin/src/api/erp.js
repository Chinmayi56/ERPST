import api from "./axios";

export const listRecords = (module, params = {}) => api.get(`/superadmin/erp/${module}`, { params }).then(r => r.data);
export const getModuleStats = module => api.get(`/superadmin/erp/${module}/stats`).then(r => r.data);
export const createRecord = (module, data) => api.post(`/superadmin/erp/${module}`, { data }).then(r => r.data);
export const updateRecord = (module, id, data) => api.put(`/superadmin/erp/${module}/${id}`, { data }).then(r => r.data);
export const deleteRecord = (module, id) => api.delete(`/superadmin/erp/${module}/${id}`).then(r => r.data);
export const updateStatus = (module, id, status) => api.patch(`/superadmin/erp/${module}/${id}/status`, { status }).then(r => r.data);
export const updateLeaveStatus = (id, status) => api.patch(`/superadmin/erp/leaves/${id}/status`, { status }).then(r => r.data);
export const uploadDocument = file => { const fd = new FormData(); fd.append("file", file); return api.post("/superadmin/erp/documents/upload", fd).then(r => r.data); };
export const getEmployeeOptions = () => api.get("/superadmin/erp/options/employees").then(r => r.data);
export const getClientOptions = () => api.get("/superadmin/erp/options/clients").then(r => r.data);
export const getServiceOptions = () => api.get("/superadmin/erp/options/services").then(r => r.data);
export const getProjectOptions = () => api.get("/superadmin/erp/options/projects").then(r => r.data);
