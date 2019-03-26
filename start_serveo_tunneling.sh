#!/usr/bin/env bash

serveo () {
	port=$1
	domain="serveo.floriankempenich.com"

	echo "If serveo forwarding is not working, ensure the correct SSH key/fingerprint"
	echo "is being used"
	echo "More info: 'Custom Domain' -> https://serveo.net/"
	echo ""

	ssh -R ${domain}:80:localhost:${port} serveo.net
}

FLASK_PORT=5000
serveo ${FLASK_PORT}
