import api from "./axios";

export const listRegistrationLinks = () =>
  api.get("/subadmin/registration-links").then((res) => res.data);

export const createRegistrationLink = (expiresInDays, note) =>
  api
    .post("/subadmin/registration-links", { expires_in_days: expiresInDays, note })
    .then((res) => res.data);

export const disableRegistrationLink = (linkId) =>
  api.post(`/subadmin/registration-links/${linkId}/disable`).then((res) => res.data);
