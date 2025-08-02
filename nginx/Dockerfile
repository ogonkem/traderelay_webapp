FROM nginx:1.19.0-alpine

# Create directories for static and media files
RUN mkdir -p /app/static /app/media

COPY ./default.conf /etc/nginx/conf.d/default.conf