'use client';

import { useLocale } from 'next-intl';
import { useRouter, usePathname } from '@/i18n/routing';

export default function LanguageToggle() {
    const locale = useLocale();
    const router = useRouter();
    const pathname = usePathname();

    const handleLanguageChange = (newLocale: string) => {
        router.replace(pathname, { locale: newLocale });
    };

    return (
        <div className="flex gap-4 items-center">
            {['en', 'es', 'pt'].map((l) => (
                <button
                    key={l}
                    onClick={() => handleLanguageChange(l)}
                    className={`uppercase text-sm tracking-widest ${locale === l ? 'font-bold text-blue-600 border-b-2 border-blue-600' : 'text-gray-500 hover:text-gray-900'
                        }`}
                >
                    {l}
                </button>
            ))}
        </div>
    );
}
