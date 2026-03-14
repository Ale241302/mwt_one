import axios from 'axios';

// Todas las peticiones van a /api/... relativo al origen.
// Next.js hace el proxy hacia mwt-django:8000 via rewrites en next.config.mjs.
// Así evitamos CORS y problemas de cookies en producción.
const api = axios.create({
    baseURL: '/api/',
    withCredentials: true,
    headers: {
        'Content-Type': 'application/json',
        'Accept': 'application/json',
    },
});

// CSRF Interceptor
api.interceptors.request.use((config) => {
    if (typeof document !== 'undefined') {
        const value = `; ${document.cookie}`;
        const parts = value.split(`; csrftoken=`);
        if (parts.length === 2) {
            const csrfToken = parts.pop()?.split(';').shift();
            if (csrfToken) {
                config.headers['X-CSRFToken'] = csrfToken;
            }
        }
    }
    return config;
});

// Helper: extract /xx language prefix from current path
function getLangPrefix(): string {
    if (typeof window === 'undefined') return '/es';
    const match = window.location.pathname.match(/^\/([a-z]{2})(?:\/|$)/);
    return match ? `/${match[1]}` : '/es';
}

// 401 Interceptor – redirect preserving language prefix
api.interceptors.response.use(
    (response) => response,
    (error) => {
        if (error.response && error.response.status === 401) {
            const isLoginPage = typeof window !== 'undefined' && window.location.pathname.includes('/login');
            const isAuthMe   = error.config?.url?.includes('auth/me');
            if (!isLoginPage && !isAuthMe && typeof window !== 'undefined') {
                window.location.href = `${getLangPrefix()}/login`;
            }
        }
        return Promise.reject(error);
    }
);

export default api;
