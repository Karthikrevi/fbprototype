import axios from 'axios';
import AsyncStorage from '@react-native-async-storage/async-storage';
import { API_BASE } from '../constants/api';

let logoutCallback = null;
export const setLogoutCallback = (fn) => { logoutCallback = fn; };

const api = axios.create({ baseURL: API_BASE, timeout: 15000 });

api.interceptors.request.use(async (config) => {
  const token = await AsyncStorage.getItem('jwt_token');
  if (token) config.headers.Authorization = `Bearer ${token}`;
  return config;
});

api.interceptors.response.use(
  (res) => res,
  async (err) => {
    if (err.response?.status === 401) {
      await AsyncStorage.removeItem('jwt_token');
      await AsyncStorage.removeItem('user');
      if (logoutCallback) logoutCallback();
    }
    return Promise.reject(err);
  }
);

export const authAPI = {
  register: (email, password, name) =>
    api.post('/auth/register', { email, password, name }),
  login: (email, password) =>
    api.post('/auth/login', { email, password }),
  me: () => api.get('/auth/me'),
};

export const petsAPI = {
  list: () => api.get('/pets'),
  add: (pet) => api.post('/pets', pet),
  get: (index) => api.get(`/pets/${index}`),
  update: (index, data) => api.put(`/pets/${index}`, data),
  passport: (index) => api.get(`/pets/${index}/passport`),
};

export const groomersAPI = {
  search: (params) => api.get('/groomers', { params }),
};

export const vendorAPI = {
  profile: (id) => api.get(`/vendor/${id}`),
  groomers: (id) => api.get(`/vendor/${id}/groomers`),
  slots: (id, date) => api.get(`/vendor/${id}/slots`, { params: { date } }),
};

export const groomerAPI = {
  profile: (id) => api.get(`/groomer/${id}`),
};

export const bookingsAPI = {
  create: (data) => api.post('/bookings', data),
  list: () => api.get('/bookings'),
  review: (id, data) => api.post(`/bookings/${id}/review`, data),
};

export const marketplaceAPI = {
  search: (params) => api.get('/marketplace', { params }),
  vendor: (id) => api.get(`/marketplace/vendor/${id}`),
};

export const ordersAPI = {
  list: () => api.get('/orders'),
  create: (data) => api.post('/orders', data),
};

export const handlersAPI = {
  list: () => api.get('/handlers'),
  detail: (id) => api.get(`/handlers/${id}`),
  book: (id, data) => api.post(`/handlers/${id}/book`, data),
  bookings: () => api.get('/handler-bookings'),
};

export const communityAPI = {
  posts: () => api.get('/community'),
};

export const strayAPI = {
  list: () => api.get('/stray-tracker'),
  detail: (uid) => api.get(`/stray/${uid}`),
};

export const chatAPI = {
  conversations: () => api.get('/chat/conversations'),
  messages: (id) => api.get(`/chat/${id}`),
  send: (conversation_id, message) =>
    api.post('/chat/send', { conversation_id, message }),
  start: (vendor_id) => api.post('/chat/start', { vendor_id }),
};

export const locationAPI = {
  set: (lat, lon) => api.post('/set-location', { lat, lon }),
  vets: (params) => api.get('/vets', { params }),
  boarding: (params) => api.get('/boarding', { params }),
};

export const miscAPI = {
  languages: () => api.get('/languages'),
};

export default api;
