import api from "./axios";

export const listRecords = (module, params = {}) => api.get(`/subadmin/erp/${module}`, { params }).then(r => r.data);
export const getModuleStats = module => api.get(`/subadmin/erp/${module}/stats`).then(r => r.data);
export const createRecord = (module, data) => api.post(`/subadmin/erp/${module}`, { data }).then(r => r.data);
export const updateRecord = (module, id, data) => api.put(`/subadmin/erp/${module}/${id}`, { data }).then(r => r.data);
export const deleteRecord = (module, id) => api.delete(`/subadmin/erp/${module}/${id}`).then(r => r.data);
export const updateStatus = (module, id, status) => api.patch(`/subadmin/erp/${module}/${id}/status`, { status }).then(r => r.data);
export const updateLeaveStatus = (id, status) => api.patch(`/subadmin/erp/leaves/${id}/status`, { status }).then(r => r.data);
export const uploadDocument = file => { const fd = new FormData(); fd.append("file", file); return api.post("/subadmin/erp/documents/upload", fd).then(r => r.data); };
export const getEmployeeOptions = () => api.get("/subadmin/erp/options/employees").then(r => r.data);
export const getClientOptions = () => api.get("/subadmin/erp/options/clients").then(r => r.data);
export const getServiceOptions = () => api.get("/subadmin/erp/options/services").then(r => r.data);
export const getProjectOptions = () => api.get("/subadmin/erp/options/projects").then(r => r.data);
