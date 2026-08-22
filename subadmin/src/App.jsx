import React from "react";
import { Routes, Route, Navigate } from "react-router-dom";
import { AuthProvider } from "./context/AuthContext";
import ProtectedRoute from "./components/ProtectedRoute";
import DashboardLayout from "./layouts/DashboardLayout";

import Login from "./pages/Login";
import Dashboard from "./pages/Dashboard";
import EmployeeManagement from "./pages/EmployeeManagement";
import EmployeeApplications from "./pages/EmployeeApplications";
import ApplicationDetail from "./pages/ApplicationDetail";
import Employees from "./pages/Employees";
import EmployeeDetail from "./pages/EmployeeDetail";
import RegistrationForms from "./pages/RegistrationForms";
import Notifications from "./pages/Notifications";
import Reports from "./pages/Reports";
import Profile from "./pages/Profile";
import Settings from "./pages/Settings";
import UserRoleManagement from "./pages/UserRoleManagement";
import ERPManagement from "./pages/ERPManagement";
import NotFound from "./pages/NotFound";

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
        <Route path="/login" element={<Login />} />

        <Route path="/dashboard" element={<Protected><Dashboard /></Protected>} />
        <Route path="/employee-management" element={<Protected><EmployeeManagement /></Protected>} />
        <Route path="/employee-applications" element={<Protected><EmployeeApplications /></Protected>} />
        <Route
          path="/employee-applications/:applicationId"
          element={<Protected><ApplicationDetail /></Protected>}
        />
        <Route path="/employees" element={<Protected><Employees /></Protected>} />
        <Route path="/employees/:employeeId" element={<Protected><EmployeeDetail /></Protected>} />
        <Route path="/registration-forms" element={<Protected><RegistrationForms /></Protected>} />
        <Route path="/clients" element={<Protected><ERPManagement module="clients" /></Protected>} />
        <Route path="/projects" element={<Protected><ERPManagement module="projects" /></Protected>} />
        <Route path="/tasks" element={<Protected><ERPManagement module="tasks" /></Protected>} />
        <Route path="/leave-requests" element={<Protected><ERPManagement module="leaves" /></Protected>} />
        <Route path="/attendance" element={<Protected><ERPManagement module="attendance" /></Protected>} />
        <Route path="/services" element={<Protected><ERPManagement module="services" /></Protected>} />
        <Route path="/services-bookings" element={<Protected><ERPManagement module="bookings" /></Protected>} />
        <Route path="/documents" element={<Protected><ERPManagement module="documents" /></Protected>} />
<Route path="/notifications" element={<Protected><Notifications /></Protected>} />
        <Route path="/reports" element={<Protected><Reports /></Protected>} />
        <Route path="/user-role-management" element={<Protected><UserRoleManagement /></Protected>} />
        <Route path="/profile" element={<Protected><Profile /></Protected>} />
        <Route path="/settings" element={<Protected><Settings /></Protected>} />

        <Route path="/" element={<Navigate to="/dashboard" replace />} />
        <Route path="*" element={<NotFound />} />
      </Routes>
    </AuthProvider>
  );
}
