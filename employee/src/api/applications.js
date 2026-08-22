import api from "./axios";

export const submitApplication = (payload) =>
  api.post("/employee-applications", payload).then((res) => res.data);

export const uploadDocument = (file) => {
  const formData = new FormData();
  formData.append("file", file);
  return api
    .post("/uploads", formData, { headers: { "Content-Type": "multipart/form-data" } })
    .then((res) => res.data);
};
