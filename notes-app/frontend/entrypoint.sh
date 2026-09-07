#!/bin/sh
# السكريبت ده مش Dockerfile -- ده entrypoint script هتستدعيه إنت من
# جوه ENTRYPOINT instruction في الـ Dockerfile بتاعك.
#
# وظيفته: ياخد environment variable اسمها API_BASE_URL وقت تشغيل
# الـ container (runtime) ويحقنها في config.js، عشان الـ frontend
# (اللي هو static files) يعرف يعمل fetch للـ backend الصح.
set -e

envsubst '${API_BASE_URL}' < /usr/share/nginx/html/config.js.template > /usr/share/nginx/html/config.js

exec "$@"
