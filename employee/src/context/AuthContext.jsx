import React, { createContext, useContext, useState, useEffect, useCallback } from "react";
import { getMe, logout as apiLogout } from "../api/auth";

const AuthContext = createContext(null);

export function AuthProvider({ children }) {
  const [user, setUser] = useState(null);
  const [loading, setLoading] = useState(true);

  const loadUser = useCallback(async () => {
    const token = localStorage.getItem("strivenest_employee_token");
    if (!token) {
      setUser(null);
      setLoading(false);
      return;
    }
    try {
      const me = await getMe();
      setUser(me);
    } catch (err) {
      localStorage.removeItem("strivenest_employee_token");
      localStorage.removeItem("strivenest_employee_user");
      setUser(null);
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    loadUser();
  }, [loadUser]);

  const login = (accessToken, userData) => {
    localStorage.setItem("strivenest_employee_token", accessToken);
    localStorage.setItem("strivenest_employee_user", JSON.stringify(userData));
    setUser(userData);
  };

  const logout = async () => {
    try {
      await apiLogout();
    } catch (err) {
      // ignore network errors on logout, clear client state regardless
    }
    localStorage.removeItem("strivenest_employee_token");
    localStorage.removeItem("strivenest_employee_user");
    setUser(null);
  };

  return (
    <AuthContext.Provider value={{ user, loading, login, logout, refreshUser: loadUser }}>
      {children}
    </AuthContext.Provider>
  );
}

export function useAuth() {
  const ctx = useContext(AuthContext);
  if (!ctx) throw new Error("useAuth must be used within AuthProvider");
  return ctx;
}
