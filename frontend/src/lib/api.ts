/* Developed by FireSeed - Fueling Innovation */
import axios from 'axios';

export const api = axios.create({
  baseURL: 'http://localhost:8000/api',
  withCredentials: true, // Crucial for sending JWT cookies
});

// Response interceptor to handle token refresh automatically
api.interceptors.response.use(
  (response) => response,
  async (error) => {
    const originalRequest = error.config;
    
    if (error.response?.status === 401 && !originalRequest._retry) {
      originalRequest._retry = true;
      try {
        // Call the refresh endpoint. dj-rest-auth will read the refresh cookie and issue a new access cookie
        await axios.post('http://localhost:8000/api/auth/token/refresh/', {}, { withCredentials: true });
        // Retry the original request
        return api(originalRequest);
      } catch (refreshError) {
        console.error('Session expired. Please log in again.');
        // window.location.href = '/';
        // Optionally trigger a logout event here
        return Promise.reject(refreshError);
      }
    }
    return Promise.reject(error);
  }
);
