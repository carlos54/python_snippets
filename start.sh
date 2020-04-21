service redis-server start
cp /app/mailing/wsgi.ini /app/
cd /app/; uwsgi wsgi.ini