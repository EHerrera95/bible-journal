web: python manage.py migrate --noinput && python manage.py setup_initial_data && python manage.py collectstatic --noinput && gunicorn biblejournal.wsgi --bind 0.0.0.0:$PORT --log-file -
