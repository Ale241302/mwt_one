import { useTranslations } from 'next-intl';

type TechCardProps = {
    techKey: string;
};

export default function TechCard({ techKey }: TechCardProps) {
    const t = useTranslations('Techs');

    return (
        <div className="bg-white p-6 rounded-2xl shadow-xl shadow-black/5 border border-gray-100 flex flex-col gap-3 transition-transform hover:-translate-y-1 duration-300">
            <h3 className="text-xl font-bold font-mono text-gray-900">{t(`${techKey}.name`)}</h3>
            <h4 className="text-md font-semibold text-gray-700">{t(`${techKey}.headline`)}</h4>
            <p className="text-gray-600 leading-relaxed font-body text-sm bg-gray-50/50 p-4 rounded-xl border border-gray-50/80">{t(`${techKey}.body`)}</p>
            <div className="mt-auto pt-4 border-t border-gray-100">
                <span className="text-xs font-bold uppercase tracking-wider text-blue-600">{t(`${techKey}.stat`)}</span>
            </div>
        </div>
    );
}
