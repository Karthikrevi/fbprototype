import React, { createContext, useState, useEffect, useContext } from 'react';
import AsyncStorage from '@react-native-async-storage/async-storage';
import { authAPI, setLogoutCallback } from '../services/api';

const AuthContext = createContext(null);

export const AuthProvider = ({ children }) => {
  const [user, setUser] = useState(null);
  const [token, setToken] = useState(null);
  const [isLoading, setIsLoading] = useState(true);

  useEffect(() => {
    checkAuth();
  }, []);

  const checkAuth = async () => {
    try {
      const stored = await AsyncStorage.getItem('jwt_token');
      if (stored) {
        setToken(stored);
        const res = await authAPI.me();
        if (res.data.success) {
          setUser(res.data.user);
        } else {
          await AsyncStorage.removeItem('jwt_token');
          setToken(null);
        }
      }
    } catch {
      await AsyncStorage.removeItem('jwt_token');
      setToken(null);
    } finally {
      setIsLoading(false);
    }
  };

  const login = async (email, password) => {
    const res = await authAPI.login(email, password);
    if (res.data.success) {
      await AsyncStorage.setItem('jwt_token', res.data.token);
      setToken(res.data.token);
      setUser(res.data.user);
      return { success: true };
    }
    return { success: false, error: res.data.error };
  };

  const register = async (email, password, name) => {
    const res = await authAPI.register(email, password, name);
    if (res.data.success) {
      await AsyncStorage.setItem('jwt_token', res.data.token);
      setToken(res.data.token);
      setUser(res.data.user);
      return { success: true };
    }
    return { success: false, error: res.data.error };
  };

  const logout = async () => {
    await AsyncStorage.removeItem('jwt_token');
    await AsyncStorage.removeItem('user');
    setToken(null);
    setUser(null);
  };

  useEffect(() => {
    setLogoutCallback(logout);
  }, []);

  return (
    <AuthContext.Provider value={{ user, token, isLoading, login, register, logout }}>
      {children}
    </AuthContext.Provider>
  );
};

export const useAuth = () => useContext(AuthContext);
export default AuthContext;
