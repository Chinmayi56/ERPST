import React from "react";
import { Routes, Route, Navigate } from "react-router-dom";
import { AuthProvider } from "./context/AuthContext";
import ProtectedRoute from "./components/ProtectedRoute";
import DashboardLayout from "./layouts/DashboardLayout";

import Register from "./pages/Register.jsx";
import Login from "./pages/Login.jsx";
import Dashboard from "./pages/Dashboard.jsx";
import Profile from "./pages/Profile.jsx";
import MyTasks from "./pages/MyTasks.jsx";
import MyProjects from "./pages/MyProjects.jsx";
import MyClients from "./pages/MyClients.jsx";
import Attendance from "./pages/Attendance.jsx";
import LeaveManagement from "./pages/LeaveManagement.jsx";
import Documents from "./pages/Documents.jsx";
import Payslips from "./pages/Payslips.jsx";
import Notifications from "./pages/Notifications.jsx";
import NotFound from "./pages/NotFound.jsx";

function Protected({ children }) {
  return (
    <ProtectedRoute>
      <DashboardLayout>{children}</DashboardLayout>
    </ProtectedRoute>
  );
}

export default function App() {
  return (
    <AuthProvider>
      <Routes>
        <Route path="/register" element={<Register />} />
        <Route path="/login" element={<Login />} />

        <Route path="/dashboard" element={<Protected><Dashboard /></Protected>} />
        <Route path="/profile" element={<Protected><Profile /></Protected>} />
        <Route path="/tasks" element={<Protected><MyTasks /></Protected>} />
        <Route path="/projects" element={<Protected><MyProjects /></Protected>} />
        <Route path="/clients" element={<Protected><MyClients /></Protected>} />
        <Route path="/attendance" element={<Protected><Attendance /></Protected>} />
        <Route path="/leave" element={<Protected><LeaveManagement /></Protected>} />
        <Route path="/documents" element={<Protected><Documents /></Protected>} />
        <Route path="/payslips" element={<Protected><Payslips /></Protected>} />
        <Route path="/notifications" element={<Protected><Notifications /></Protected>} />

        <Route path="/" element={<Navigate to="/login" replace />} />
        <Route path="*" element={<NotFound />} />
      </Routes>
    </AuthProvider>
  );
}
