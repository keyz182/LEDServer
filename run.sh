#!/bin/bash
uvicorn main:app --host 0.0.0.0 --port 8443 --ssl-keyfile /home/pi/.acme.sh/leds.dbyz.uk/leds.dbyz.uk.key --ssl-certfile /home/pi/.acme.sh/leds.dbyz.uk/leds.dbyz.uk.cer --ssl-ca-certs /home/pi/.acme.sh/leds.dbyz.uk/fullchain.cer --reload --limit-concurrency 5 --workers 1
