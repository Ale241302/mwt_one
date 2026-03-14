import axios from 'axios';

// NEXT_PUBLIC_API_URL debe apuntar al backend, e.g. https://consola.mwt.one
// Si no está definida en tiempo de build/runtime, recae en origen relativo.
const BASE_URL = process.env.NEXT_PUBLIC_API_URL ?? '';

const api = axios.create({
    baseURL: BASE_URL,
    withCredentials: true, // Important for session cookies and CSRF
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
            const isAuthMe   = error.config?.url?.includes('/auth/me');
            if (!isLoginPage && !isAuthMe && typeof window !== 'undefined') {
                window.location.href = `${getLangPrefix()}/login`;
            }
        }
        return Promise.reject(error);
    }
);

export default api;
