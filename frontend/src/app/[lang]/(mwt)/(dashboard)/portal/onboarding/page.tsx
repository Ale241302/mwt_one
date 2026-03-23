"use client";

import { useState } from "react";
import { useRouter, useParams } from "next/navigation";
import { Check, ArrowRight, ArrowLeft, Shield, Smartphone, Bell, Rocket } from "lucide-react";
import { cn } from "@/lib/utils";

const STEPS = [
  {
    title: "Seguridad Reforzada",
    description: "Configura la autenticación de dos factores para proteger tus datos financieros.",
    icon: Shield,
    color: "var(--brand-primary)",
  },
  {
    title: "Notificaciones Push",
    description: "Recibe alertas en tiempo real sobre cambios de estado en tus expedientes.",
    icon: Bell,
    color: "var(--brand-accent)",
  },
  {
    title: "MWT Pocket",
    description: "Descarga nuestra app móvil para gestionar tus operaciones desde cualquier lugar.",
    icon: Smartphone,
    color: "var(--brand-ice)",
  }
];

export default function OnboardingPage() {
  const router = useRouter();
  const params = useParams();
  const lang = (params?.lang as string) || "es";
  const [currentStep, setCurrentStep] = useState(0);

  const next = () => {
    if (currentStep < STEPS.length - 1) {
      setCurrentStep(currentStep + 1);
    } else {
      finish();
    }
  };

  const prev = () => {
    if (currentStep > 0) {
      setCurrentStep(currentStep - 1);
    }
  };

  const finish = () => {
    // In a real app, we'd save that the user finished onboarding
    router.push(`/${lang}/portal`);
  };

  const step = STEPS[currentStep];
  const Icon = step.icon;

  return (
    <div className="min-h-screen flex items-center justify-center bg-bg p-4">
      <div className="max-w-xl w-full">
        {/* Progress Bar */}
        <div className="flex gap-2 mb-12">
          {STEPS.map((_, idx) => (
            <div 
              key={idx}
              className={cn(
                "h-1.5 flex-1 rounded-full transition-all duration-500",
                idx <= currentStep ? "bg-brand-primary" : "bg-border-strong"
              )}
            />
          ))}
        </div>

        <div className="card p-10 text-center animate-in fade-in slide-in-from-bottom-4 duration-500">
          <div 
            className="w-20 h-20 rounded-3xl flex items-center justify-center mx-auto mb-8 shadow-lg"
            style={{ backgroundColor: `${step.color}20`, color: step.color }}
          >
            <Icon size={40} />
          </div>

          <h1 className="display-md mb-4">{step.title}</h1>
          <p className="text-text-secondary text-lg mb-10 max-w-sm mx-auto">
            {step.description}
          </p>

          <div className="flex gap-4 items-center justify-between mt-8 pt-8 border-t border-divider">
            <button 
              onClick={prev}
              disabled={currentStep === 0}
              className="btn btn-md btn-ghost disabled:opacity-0"
            >
              <ArrowLeft size={18} /> Atrás
            </button>

            <div className="flex gap-3">
              <button 
                onClick={finish}
                className="btn btn-md btn-ghost text-text-tertiary hover:text-text-primary"
              >
                Omitir
              </button>
              <button 
                onClick={next}
                className="btn btn-md btn-primary"
              >
                {currentStep === STEPS.length - 1 ? (
                  <>Empezar ahora <Rocket size={18} className="ml-2" /></>
                ) : (
                  <>Siguiente <ArrowRight size={18} className="ml-2" /></>
                )}
              </button>
            </div>
          </div>
        </div>

        <p className="text-center mt-8 text-sm text-text-tertiary">
          Paso {currentStep + 1} de {STEPS.length}
        </p>
      </div>
    </div>
  );
}
