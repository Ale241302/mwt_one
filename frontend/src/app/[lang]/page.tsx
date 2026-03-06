import { useTranslations } from 'next-intl';
import LanguageToggle from '@/components/LanguageToggle';

export default function RanaWalkHome() {
    const t = useTranslations('Index');

    return (
        <div className="min-h-screen flex flex-col items-center justify-center bg-gray-50 p-6">
            <header className="absolute top-0 w-full p-6 flex justify-end">
                <LanguageToggle />
            </header>
            <main className="text-center max-w-2xl">
                <h1 className="text-5xl font-extrabold text-blue-900 mb-6 font-mono tracking-tighter">
                    RANA WALK
                </h1>
                <h2 className="text-2xl font-semibold text-gray-800 mb-4 font-body">
                    {t('title')}
                </h2>
                <p className="text-lg text-gray-600 font-body">
                    {t('description')}
                </p>
            </main>
        </div>
    );
}
