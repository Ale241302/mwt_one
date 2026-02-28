"use client";

import { Toaster } from "react-hot-toast";

export default function ToastProvider() {
    return (
        <Toaster
            position="bottom-right"
            toastOptions={{
                duration: 5000,
                style: {
                    background: "var(--surface)",
                    color: "var(--text-primary)",
                    border: "1px solid var(--border)",
                    boxShadow: "var(--shadow-md)",
                    borderRadius: "var(--radius-lg)",
                },
                success: {
                    iconTheme: { primary: "var(--mint-dark)", secondary: "white" },
                    style: { borderLeft: "4px solid var(--mint-dark)" }
                },
                error: {
                    duration: Infinity, // persistent per spec, user dismisses
                    iconTheme: { primary: "var(--coral)", secondary: "white" },
                    style: { borderLeft: "4px solid var(--coral)", background: "var(--coral-soft)" }
                }
            }}
        />
    );
}
