import createMiddleware from 'next-intl/middleware';
import { routing } from './i18n/routing';
import { NextRequest } from 'next/server';

const intlMiddleware = createMiddleware(routing);

export default function middleware(req: NextRequest) {
    const host = req.headers.get('host') || '';
    const { pathname } = req.nextUrl;

    // Detect domain
    const isMwtDomain = host.includes('consola.mwt.one') || host.includes('mwt.one');

    // If it's MWT domain and hitting root, internally route to dashboard
    if (isMwtDomain && pathname === '/') {
        req.nextUrl.pathname = '/dashboard';
    }

    return intlMiddleware(req);
}

export const config = {
    // Match all routes except api, _next, and static files
    matcher: ['/((?!api|_next|.*\\..*).*)']
};
