#!/bin/bash

# variables
domains=(worldatlas.org www.worldatlas.org)
rsa_key_size=4096
data_path="./infrastructure/certbot"
email=SECRET_EMAIL_FOR_TLS_CERT_GENERATOR
staging=0 # 1=staging 0=production

echo "Domains are $domains. Lets encrypt flag=$staging (staging=1, production=0)"

# Copy in default TLS paramaters if they are not present in the certbot folder
echo "### Copying recommended TLS parameters ..."
mkdir -p "$data_path/conf"
cp "./infrastructure/tls/options-ssl-nginx.conf" "$data_path/conf/options-ssl-nginx.conf"
sudo cp "./infrastructure/tls/ssl-dhparams.pem" "$data_path/conf/ssl-dhparams.pem"
echo


echo "### Creating dummy certificate for $domains ..."
path="/etc/letsencrypt/live/$domains"
mkdir -p "$data_path/conf/live/$domains"
docker-compose run --rm --entrypoint "\
  openssl req -x509 -nodes -newkey rsa:$rsa_key_size -days 1\
    -keyout '$path/privkey.pem' \
    -out '$path/fullchain.pem' \
    -subj '/CN=localhost'" certbot
echo

# Nginx running in SSL mode needs certs to exist (hence previous step)
echo "### Starting nginx ..."
docker-compose up --force-recreate -d nginx
#echo

# Remove all dummy cert associated stuff
echo "### Deleting dummy certificate for $domains ..."
docker-compose run --rm --entrypoint "\
  rm -Rf /etc/letsencrypt/live/$domains && \
  rm -Rf /etc/letsencrypt/archive/$domains && \
  rm -Rf /etc/letsencrypt/renewal/$domains.conf" certbot
echo

#Join $domains to -d args
domain_args=""
for domain in "${domains[@]}"; do
  domain_args="$domain_args -d $domain"
done

# Select appropriate email arg
case "$email" in
  "") email_arg="--register-unsafely-without-email" ;;
  *) email_arg="--email $email" ;;
esac

# Enable staging mode if needed
if [ $staging != "0" ]; then staging_arg="--staging"; fi

# Run certbot and place certs in /etc/letsencrypt/... area for NGINX to load
echo "### Requesting Let's Encrypt certificate for $domains ..."
docker-compose run --rm --entrypoint "\
  certbot certonly --non-interactive --agree-tos --webroot -w /var/www/certbot \
    $staging_arg \
    $email_arg \
    $domain_args \
    --rsa-key-size $rsa_key_size \
    --agree-tos \
    --force-renewal" certbot
echo

# Live reload NGINX
echo "### Reloading nginx ..."
docker-compose exec nginx nginx -s reload

# bring everything up
sudo docker-compose up -d
