import api from "./axios";

export const listNotifications = () =>
  api.get("/subadmin/notifications").then((res) => res.data);

export const markNotificationRead = (notificationId) =>
  api.patch(`/subadmin/notifications/${notificationId}/read`).then((res) => res.data);
