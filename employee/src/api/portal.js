import api from "./axios";

export const getMyDashboard = () => api.get("/employee/dashboard").then((res) => res.data);

export const getMyProfile = () => api.get("/employee/profile").then((res) => res.data);

export const listMyNotifications = () => api.get("/employee/notifications").then((res) => res.data);

export const markMyNotificationRead = (notificationId) =>
  api.patch(`/employee/notifications/${notificationId}/read`).then((res) => res.data);

export const markAllMyNotificationsRead = () =>
  api.patch("/employee/notifications/read-all").then((res) => res.data);
