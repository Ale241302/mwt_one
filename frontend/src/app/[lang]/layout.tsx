import type { Metadata } from 'next';
import { NextIntlClientProvider } from 'next-intl';
import { getMessages } from 'next-intl/server';
import { notFound } from 'next/navigation';
import { routing } from '@/i18n/routing';
import { Plus_Jakarta_Sans, JetBrains_Mono } from 'next/font/google';
import '../(mwt)/globals.css';

const jakarta = Plus_Jakarta_Sans({
    subsets: ['latin'],
    variable: '--font-body',
});

const jetbrains = JetBrains_Mono({
    subsets: ['latin'],
    variable: '--font-mono',
});

export const metadata: Metadata = {
    title: 'Rana Walk | American Technology Inside',
    description: 'Premium Technology orthotic solutions',
};

export default async function LocaleLayout({
    children,
    params,
}: {
    children: React.ReactNode;
    params: Promise<{ lang: string }>;
}) {
    const { lang } = await params;
    if (!routing.locales.includes(lang as any)) {
        notFound();
    }

    const messages = await getMessages();

    return (
        <html lang={lang} data-theme="light">
            <body className={`${jakarta.variable} ${jetbrains.variable} font-body antialiased bg-bg text-text-primary`}>
                <NextIntlClientProvider messages={messages}>
                    {children}
                </NextIntlClientProvider>
            </body>
        </html>
    );
}
