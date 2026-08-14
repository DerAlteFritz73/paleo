FROM php:8.3-fpm-alpine

WORKDIR /var/www/feedback
COPY send.php .

# Écoute sur toutes les interfaces du réseau Docker interne (nginx s'y
# connecte via le nom de service "mail", jamais exposé hors du conteneur).
RUN sed -i 's/^listen = .*/listen = 0.0.0.0:9000/' /usr/local/etc/php-fpm.d/www.conf

EXPOSE 9000
