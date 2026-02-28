import axios from 'axios';

const api = axios.create({
    baseURL: process.env.NEXT_PUBLIC_API_URL || '/api',
    withCredentials: true, // Important for session cookies and CSRF
    headers: {
        'Content-Type': 'application/json',
        'Accept': 'application/json',
    },
});

// CSRF Interceptor
api.interceptors.request.use((config) => {
    // Try to get csrftoken from cookies
    const value = `; ${document.cookie}`;
    const parts = value.split(`; csrftoken=`);
    if (parts.length === 2) {
        const csrfToken = parts.pop()?.split(';').shift();
        if (csrfToken) {
            config.headers['X-CSRFToken'] = csrfToken;
        }
    }
    return config;
});

// 401 Interceptor
api.interceptors.response.use(
    (response) => response,
    (error) => {
        if (error.response && error.response.status === 401) {
            // Don't redirect if we are already on login page or just checking /me
            if (
                typeof window !== 'undefined' &&
                !window.location.pathname.includes('/login') &&
                !error.config.url?.includes('/auth/me')
            ) {
                window.location.href = '/login';
            }
        }
        return Promise.reject(error);
    }
);

export default api;
