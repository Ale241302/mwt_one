"use client";

import React, { createContext, useContext, useState, useEffect, useCallback, ReactNode } from 'react';
import api from '@/lib/api';
import { useRouter } from 'next/navigation';

export interface User {
    id: number;
    username: string;
    role: string;
}

interface AuthContextType {
    user: User | null;
    loading: boolean;
    login: (user: User) => void;
    logout: () => Promise<void>;
    checkAuth: () => Promise<void>;
}

const AuthContext = createContext<AuthContextType | undefined>(undefined);

export function AuthProvider({ children }: { children: ReactNode }) {
    const [user, setUser] = useState<User | null>(null);
    const [loading, setLoading] = useState(true);
    const router = useRouter();

    const checkAuth = useCallback(async () => {
        try {
            const response = await api.get('/core/auth/me/');
            setUser(response.data.user);
        } catch {
            setUser(null);
        } finally {
            setLoading(false);
        }
    }, []);

    // ✅ Solo corre UNA VEZ al montar, no en cada cambio de ruta
    useEffect(() => {
        checkAuth();
    }, [checkAuth]);

    const login = (newUser: User) => {
        setUser(newUser);
        router.push('/');
    };

    const logout = async () => {
        try {
            await api.post('/core/auth/logout/');
        } catch (e) {
            console.error('Logout failed', e);
        } finally {
            setUser(null);
            router.push('/login');
        }
    };

    return (
        <AuthContext.Provider value={{ user, loading, login, logout, checkAuth }}>
            {children}
        </AuthContext.Provider>
    );
}

export function useAuth() {
    const context = useContext(AuthContext);
    if (context === undefined) {
        throw new Error('useAuth must be used within an AuthProvider');
    }
    return context;
}
