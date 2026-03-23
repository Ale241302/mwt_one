"use client";

import { useState } from "react";
import { useAuth } from "@/contexts/AuthContext";
import Image from "next/image";
import { Eye, EyeOff } from "lucide-react";

export default function LoginPage() {
    const [username, setUsername] = useState("");
    const [password, setPassword] = useState("");
    const [showPassword, setShowPassword] = useState(false);
    const [error, setError] = useState("");
    const [loading, setLoading] = useState(false);
    const { login } = useAuth();

    // We handle the API call manually here to show errors properly
    const handleLogin = async (e: React.FormEvent) => {
        e.preventDefault();
        setError("");
        setLoading(true);

        try {
            const response = await fetch('/api/core/auth/login/', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({ username, password }),
            });

            let data;
            const contentType = response.headers.get("content-type");
            if (contentType && contentType.indexOf("application/json") !== -1) {
                data = await response.json();
            } else {
                const text = await response.text();
                console.error("Non-JSON API response:", text);
                throw new Error('Error en el servidor. Por favor intente más tarde.');
            }

            if (!response.ok) {
                throw new Error(data.error || 'Autenticación fallida');
            }

            login(data.user);
        } catch (err: unknown) {
            console.error("Login catch error:", err);
            if (err instanceof Error) {
                setError(err.message);
            } else {
                setError("Ocurrió un error inesperado.");
            }
        } finally {
            setLoading(false);
        }
    };

    return (
        <div className="min-h-screen flex items-center justify-center bg-gradient-to-br from-navy to-navy-dark relative overflow-hidden">
            {/* Ambient glassmorphism blobs */}
            <div className="absolute top-0 left-0 w-96 h-96 bg-mint/20 rounded-full blur-3xl -translate-x-1/2 -translate-y-1/2 pointer-events-none"></div>
            <div className="absolute bottom-0 right-0 w-96 h-96 bg-blue-500/20 rounded-full blur-3xl translate-x-1/3 translate-y-1/3 pointer-events-none"></div>

            <div
                className="w-full max-w-md p-8 rounded-2xl shadow-2xl relative z-10"
                style={{
                    background: "var(--surface-glass-bg)",
                    backdropFilter: "var(--surface-glass-blur)",
                    WebkitBackdropFilter: "var(--surface-glass-blur)",
                    border: "var(--surface-glass-border)"
                }}
            >

                <div className="mb-8 text-center">
                    <div className="flex justify-center">
                        <Image
                            src="/recurso-1logo_foot.png"
                            alt="MWT.ONE"
                            width={220}
                            height={60}
                            priority
                        />
                    </div>
                    <p className="text-text-secondary mt-2" style={{ color: "#fff!important" }}>Ingresa tus credenciales para continuar</p>
                </div>

                {error && (
                    <div className="mb-6 p-4 bg-coral-soft border border-coral text-coral rounded-lg text-sm">
                        {error}
                    </div>
                )}

                <form onSubmit={handleLogin} className="space-y-5">
                    <div>
                        <label className="block text-sm font-medium text-text-secondary mb-1">
                            Usuario
                        </label>
                        <input
                            type="text"
                            value={username}
                            onChange={(e) => setUsername(e.target.value)}
                            required
                            disabled={loading}
                            className="w-full px-4 py-2 bg-bg border border-border rounded-lg text-text-primary focus:outline-none focus:border-mint focus:ring-2 focus:ring-mint-soft transition-all-custom"
                            placeholder="admin"
                        />
                    </div>

                    <div>
                        <label className="block text-sm font-medium text-text-secondary mb-1">
                            Contraseña
                        </label>
                        <div className="relative">
                            <input
                                type={showPassword ? "text" : "password"}
                                value={password}
                                onChange={(e) => setPassword(e.target.value)}
                                required
                                disabled={loading}
                                className="w-full px-4 py-2 bg-bg border border-border rounded-lg text-text-primary focus:outline-none focus:border-mint focus:ring-2 focus:ring-mint-soft transition-all-custom pr-10"
                                placeholder="••••••••"
                            />
                            <button
                                type="button"
                                onClick={() => setShowPassword(!showPassword)}
                                className="absolute right-3 top-1/2 -translate-y-1/2 text-text-secondary hover:text-mint transition-colors"
                                tabIndex={-1}
                            >
                                {showPassword ? (
                                    <EyeOff size={20} />
                                ) : (
                                    <Eye size={20} />
                                )}
                            </button>
                        </div>
                    </div>

                    <button
                        type="submit"
                        disabled={loading}
                        className="w-full py-2.5 bg-mint hover:bg-mint-dark text-navy font-semibold rounded-lg shadow-sm transition-all-custom disabled:opacity-50 flex justify-center items-center"
                    >
                        {loading ? (
                            <svg className="animate-spin h-5 w-5 text-navy" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
                                <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
                                <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
                            </svg>
                        ) : (
                            "Ingresar a la plataforma"
                        )}
                    </button>
                </form>
            </div>
        </div>
    );
}
