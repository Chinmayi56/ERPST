import api from "./axios";

export const listNotifications = () =>
  api.get("/superadmin/notifications").then((res) => res.data);

export const markNotificationRead = (notificationId) =>
  api.patch(`/superadmin/notifications/${notificationId}/read`).then((res) => res.data);
