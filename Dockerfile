FROM python:3.11-slim as builder
WORKDIR /app
RUN apt-get update && apt-get install -y --no-install-recommends chromium && rm -rf /var/lib/apt/lists/*
COPY . .
RUN pip install --no-cache-dir pyyaml jinja2 pillow pypdf
RUN python3 build_pdf.py && python3 build_pdf.py de && python3 build_pdf.py en && python3 build_static.py

FROM nginx:1.27-alpine
COPY --from=builder /app/preview /usr/share/nginx/html/preview
COPY --from=builder /app/public /usr/share/nginx/html/public
COPY --from=builder /app/dist /usr/share/nginx/html/dist
RUN mkdir -p /usr/share/nginx/html/assets && cp /usr/share/nginx/html/dist/*.pdf /usr/share/nginx/html/public/assets/ 2>/dev/null || true
COPY docker/nginx/default.conf /etc/nginx/conf.d/default.conf
EXPOSE 80
CMD ["nginx", "-g", "daemon off;"]
