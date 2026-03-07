import createMiddleware from 'next-intl/middleware';
import { routing } from './i18n/routing';

const intlMiddleware = createMiddleware(routing);

import { NextRequest } from 'next/server';

export default function middleware(req: NextRequest) {
    return intlMiddleware(req);
}

export const config = {
    // Matchea solo /en, /es, /pt y omitimos static files o configuraciones del sistema (/api)
    matcher: ['/', '/(en|es|pt)/:path*']
};
