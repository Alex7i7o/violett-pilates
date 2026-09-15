import axios from 'axios';

const baseUrl = import.meta.env.BASE_URL || '/';
const apiBase = baseUrl.endsWith('/app/') ? baseUrl.replace('/app/', '/api/') : '/api';

export const api = axios.create({
  baseURL: apiBase,
  withCredentials: true,
});

let isRefreshing = false;
let failedQueue: any[] = [];

const processQueue = (error: any, token: string | null = null) => {
  failedQueue.forEach(prom => {
    if (error) {
      prom.reject(error);
    } else {
      prom.resolve(token);
    }
  });
  failedQueue = [];
};

api.interceptors.response.use(
  (response) => response,
  async (error) => {
    const originalRequest = error.config;

    // Si es un error 401 y no es ya un intento de refresh
    if (error.response?.status === 401 && originalRequest && !originalRequest._retry) {
      // Evitar loops infinitos si falla el login o el refresh mismo
      if (originalRequest.url.includes('/auth/login') || originalRequest.url.includes('/auth/token/refresh')) {
        return Promise.reject(error);
      }

      if (isRefreshing) {
        return new Promise(function(resolve, reject) {
          failedQueue.push({resolve, reject});
        }).then(token => {
          return api(originalRequest);
        }).catch(err => {
          return Promise.reject(err);
        });
      }

      originalRequest._retry = true;
      isRefreshing = true;

      try {
        await api.post('/auth/token/refresh/');
        processQueue(null, 'refreshed');
        return api(originalRequest);
      } catch (err) {
        processQueue(err, null);
        if (!window.location.pathname.includes('/login')) {
          const loginPath = baseUrl.endsWith('/') ? baseUrl + 'login' : baseUrl + '/login';
          window.location.replace(loginPath);
        }
        return Promise.reject(err);
      } finally {
        isRefreshing = false;
      }
    }

    if (error.response?.status === 401) {
      if (!window.location.pathname.includes('/login')) {
        const loginPath = baseUrl.endsWith('/') ? baseUrl + 'login' : baseUrl + '/login';
        window.location.replace(loginPath);
      }
    }
    
    return Promise.reject(error);
  }
);
