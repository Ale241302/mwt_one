FROM nginx:alpine
# Copy main config
COPY nginx/mwt.conf /etc/nginx/conf.d/default.conf
# Copy site-specific config (Sprint 6 Audit Item 7)
COPY Infra/nginx/go-ranawalk.conf /etc/nginx/conf.d/go-ranawalk.conf
