import { useTranslations } from 'next-intl';
import TechCard from './TechCard';
import LanguageToggle from './LanguageToggle';

export type InsideProductProps = {
    productName: string;
    primaryColor: string;
    accentColor: string;
    textColor?: string;
    techs: string[];
    seal: string | null;
    archProfiles: string[] | null;
};

export default function InsideProduct({
    productName,
    primaryColor,
    accentColor,
    textColor = '#FFFFFF',
    techs,
    seal,
    archProfiles
}: InsideProductProps) {
    const t = useTranslations('Product');

    return (
        <div className="min-h-screen transition-colors duration-500" style={{ backgroundColor: primaryColor }}>
            <header className="absolute top-0 w-full p-6 flex justify-end">
                <div className="bg-white/90 backdrop-blur px-4 py-2 rounded-full shadow-lg">
                    <LanguageToggle />
                </div>
            </header>
            <div className="max-w-5xl mx-auto px-6 py-24">
                <header className="text-center mb-20 relative">
                    <h2 className="text-sm tracking-[0.3em] font-semibold uppercase mb-4 font-mono opacity-80" style={{ color: textColor }}>
                        {t('inside')}
                    </h2>
                    <h1 className="text-7xl md:text-9xl font-black tracking-tighter drop-shadow-lg" style={{ color: accentColor }}>
                        {productName}
                    </h1>
                    {seal && (
                        <div className="mt-8 inline-block border-2 rounded-full px-6 py-2 shadow-2xl backdrop-blur-md" style={{ borderColor: accentColor, backgroundColor: `${accentColor}1A` }}>
                            <span className="font-mono text-sm uppercase tracking-widest font-bold" style={{ color: textColor }}>
                                {t('seal')} {seal}
                            </span>
                        </div>
                    )}
                </header>

                <section className="mt-20 relative z-10">
                    <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-8">
                        {techs.map((tech) => (
                            <TechCard key={tech} techKey={tech} />
                        ))}
                    </div>
                </section>

                {archProfiles && (
                    <section className="mt-24 text-center">
                        <h3 className="uppercase tracking-widest text-sm mb-6 font-mono font-bold opacity-70" style={{ color: textColor }}>
                            {t('arch_profiles')}
                        </h3>
                        <div className="flex gap-4 justify-center flex-wrap">
                            {archProfiles.map((arch) => (
                                <div key={arch} className="px-6 py-3 rounded-xl text-sm font-bold shadow-lg" style={{ backgroundColor: accentColor, color: primaryColor === '#FFFFFF' ? '#FFFFFF' : primaryColor }}>
                                    {arch}
                                </div>
                            ))}
                        </div>
                    </section>
                )}
            </div>
        </div>
    );
}
