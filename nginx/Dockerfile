FROM nginx:alpine

# Install openssl for self-signed certs (Sprint 6 Audit Item 7 / Fix 522)
RUN apk add --no-cache openssl

# Copy configs from root context
COPY nginx/mwt.conf /etc/nginx/conf.d/default.conf
COPY Infra/nginx/go-ranawalk.conf /etc/nginx/conf.d/go-ranawalk.conf

# Copy entrypoint for cert generation
COPY nginx/entrypoint.sh /entrypoint.sh
RUN sed -i 's/\r$//' /entrypoint.sh && chmod +x /entrypoint.sh

ENTRYPOINT ["/entrypoint.sh"]
