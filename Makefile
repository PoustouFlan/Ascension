crypto_drink:
	cd src; python3 ascension.py

clear_cache:
	rm -f src/data/db.sqlite3*
	rm src/data/tmp/*
