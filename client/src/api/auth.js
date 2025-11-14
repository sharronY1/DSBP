/**
 * DSBP Authentication API
 */
import http from './http';

const register = (data) => http.post('/auth/register', data);
const login = (data) => http.post('/auth/login', data);
const getCurrentUser = () => http.get('/auth/me');

export default {
  register,
  login,
  getCurrentUser,
};

