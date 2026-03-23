"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import { CheckCircle, ChevronRight, SkipForward } from "lucide-react";

export default function OnboardingPage() {
  const [step, setStep] = useState(1);
  const router = useRouter();

  const handleNext = () => {
    if (step < 3) setStep(step + 1);
    else router.push("/dashboard");
  };

  const handleSkip = () => {
    router.push("/dashboard");
  };

  return (
    <div className="min-h-screen flex items-center justify-center bg-gradient-to-br from-navy to-navy-dark relative overflow-hidden">
        {/* Ambient blobs */}
        <div className="absolute top-0 right-0 w-96 h-96 bg-mint/20 rounded-full blur-3xl translate-x-1/2 -translate-y-1/4 pointer-events-none"></div>
        <div className="absolute bottom-0 left-0 w-96 h-96 bg-blue-500/20 rounded-full blur-3xl -translate-x-1/3 translate-y-1/3 pointer-events-none"></div>
        
        <div 
          className="w-full max-w-xl p-10 rounded-2xl shadow-2xl relative z-10 mx-4" 
          style={{
            background: "var(--surface-glass-bg)",
            backdropFilter: "var(--surface-glass-blur)",
            WebkitBackdropFilter: "var(--surface-glass-blur)",
            border: "var(--surface-glass-border)",
            color: "white"
          }}
        >
          {/* Progress Indicator */}
          <div className="flex gap-2 mb-8">
            {[1, 2, 3].map((i) => (
              <div 
                key={i} 
                className="h-1.5 flex-1 rounded-full transition-all duration-300"
                style={{ background: i <= step ? "var(--mint)" : "rgba(255,255,255,0.2)" }}
              />
            ))}
          </div>

          <div className="min-h-[200px] flex flex-col justify-center text-center">
            {step === 1 && (
              <div className="animate-in fade-in slide-in-from-bottom-4 duration-500">
                <h1 className="text-3xl font-bold mb-4">Bienvenido al Portal MWT</h1>
                <p className="text-gray-300 text-lg">Tu nueva plataforma para gestionar importaciones, despachos y catálogos de forma centralizada.</p>
              </div>
            )}
            
            {step === 2 && (
              <div className="animate-in fade-in slide-in-from-bottom-4 duration-500">
                <h1 className="text-3xl font-bold mb-4">Visibilidad Total</h1>
                <p className="text-gray-300 text-lg">Haz seguimiento en tiempo real de todos tus expedientes, desde el pago hasta la llegada a destino.</p>
              </div>
            )}
            
            {step === 3 && (
              <div className="animate-in fade-in slide-in-from-bottom-4 duration-500">
                <h1 className="text-3xl font-bold mb-4">Comienza ahora</h1>
                <p className="text-gray-300 text-lg">Configura tus preferencias y mantén tus notificaciones bajo control.</p>
                <div className="mt-8">
                  <CheckCircle size={56} className="mx-auto" style={{ color: "var(--mint)" }} />
                </div>
              </div>
            )}
          </div>

          <div className="flex items-center justify-between mt-10 pt-8" style={{ borderTop: "1px solid rgba(255,255,255,0.1)" }}>
            <button 
              onClick={handleSkip}
              className="flex items-center gap-2 px-4 py-2 rounded-lg text-sm font-medium transition-colors hover:bg-white/10 text-gray-300"
            >
              Saltar tutorial <SkipForward size={14} />
            </button>
            <button 
              onClick={handleNext}
              className="flex items-center gap-2 px-6 py-3 rounded-lg text-sm font-bold transition-all shadow-[0_0_15px_rgba(25,200,165,0.3)] hover:shadow-[0_0_25px_rgba(25,200,165,0.5)] bg-mint text-navy"
            >
              {step === 3 ? "Ir al Dashboard" : "Siguiente"} <ChevronRight size={18} />
            </button>
          </div>
        </div>
    </div>
  );
}
