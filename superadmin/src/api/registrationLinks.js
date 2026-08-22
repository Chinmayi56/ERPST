import api from "./axios";

export const listRegistrationLinks = () =>
  api.get("/superadmin/registration-links").then((res) => res.data);

export const createRegistrationLink = (expiresInDays, note) =>
  api
    .post("/superadmin/registration-links", { expires_in_days: expiresInDays, note })
    .then((res) => res.data);

export const disableRegistrationLink = (linkId) =>
  api.post(`/superadmin/registration-links/${linkId}/disable`).then((res) => res.data);
