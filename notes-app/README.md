# Notes App — 3-Tier (Frontend / Backend / Database)

مفيش Dockerfiles في المشروع ده بتاتًا — دي مهمتك في الـ 3 containers.
الجزء ده بيديك كل اللي محتاجه: الـ env vars، أوامر التشغيل، والـ ports.

---

## هيكل المشروع

```
notes-app/
├── backend/
│   ├── app.py
│   └── requirements.txt
├── frontend/
│   ├── index.html
│   ├── style.css
│   ├── script.js
│   ├── config.js.template   # يتحول لـ config.js وقت الـ runtime
│   └── entrypoint.sh        # بيعمل envsubst -- استدعيه من ENTRYPOINT
└── README.md
```

---

## 1) Database container

استخدم الـ **official postgres image** مباشرة (`postgres:16-alpine` مثلاً)،
مفيش داعي تعمله Dockerfile مخصوص.

### Environment Variables (المتوقع الـ postgres image الرسمي ياخدها)

| المتغير | مثال | الوصف |
|---|---|---|
| `POSTGRES_USER` | `notes_user` | لازم يطابق `DB_USER` بتاع الـ backend |
| `POSTGRES_PASSWORD` | `notes_pass` | لازم يطابق `DB_PASSWORD` بتاع الـ backend |
| `POSTGRES_DB` | `notes_db` | لازم يطابق `DB_NAME` بتاع الـ backend |

### Volume
لازم تعمل mount على `/var/lib/postgresql/data` عشان الداتا تبقى persistent.

### Port
`5432` (الافتراضي بتاع postgres)

---

## 2) Backend container (Flask API)

### Base image المقترح
`python:3.13-slim`

### أمر التشغيل (CMD)
```
gunicorn -w 4 -b 0.0.0.0:5000 app:app
```

### Environment Variables

| المتغير | الافتراضي | الوصف |
|---|---|---|
| `DB_HOST` | `db` | اسم الـ service/container بتاع الداتابيز (لو هتستخدم docker-compose أو Docker network، الاسم ده هيبقى اسم الـ service) |
| `DB_PORT` | `5432` | بورت الـ postgres |
| `DB_USER` | `notes_user` | لازم يطابق `POSTGRES_USER` |
| `DB_PASSWORD` | `notes_pass` | لازم يطابق `POSTGRES_PASSWORD` |
| `DB_NAME` | `notes_db` | لازم يطابق `POSTGRES_DB` |
| `DATABASE_URL` | *(اختياري)* | لو حطيته بيتجاهل الـ 5 متغيرات اللي فوق ويستخدم القيمة دي مباشرة، الصيغة: `postgresql://user:pass@host:port/dbname` |
| `CORS_ORIGIN` | `*` | الـ origin بتاع الـ frontend (مثلاً `http://localhost:8080`) — مهم جدًا تحدده صح في الإنتاج بدل `*` |
| `PORT` | `5000` | البورت اللي Flask/gunicorn شغالين عليه |
| `DB_CONNECT_RETRIES` | `10` | عدد محاولات الاتصال بالـ DB وقت الـ startup (مفيدة لو الـ db container لسه بيقوم) |
| `DB_CONNECT_RETRY_DELAY` | `3` | عدد الثواني بين كل محاولة اتصال |

### Port
`5000`

### ملحوظة مهمة (Startup Order)
الكود فيه retry logic بيحاول يتصل بالـ DB لحد `DB_CONNECT_RETRIES` مرة قبل
ما يعمل crash. رغم كده الأفضل إنك تستخدم `depends_on` مع `condition:
service_healthy` لو هتعمل docker-compose، وتحط `HEALTHCHECK` على الـ db
container.

---

## 3) Frontend container (Static files عبر nginx)

### Base image المقترح
`nginx:alpine`

### الملفات اللي تتنسخ لمجلد nginx (`/usr/share/nginx/html`)
كل حاجة في `frontend/` بما فيها `config.js.template`.

### الـ ENTRYPOINT
لازم تستخدم `entrypoint.sh` الموجود في المجلد (مش Dockerfile، هو مجرد سكريبت):
- انسخه لمكان زي `/entrypoint.sh` جوه الـ image
- اديله صلاحية تنفيذ (`chmod +x`)
- خليه هو الـ `ENTRYPOINT`، والـ `CMD` يبقى `["nginx", "-g", "daemon off;"]`

هو بيستخدم `envsubst` (موجودة جوه صورة nginx الرسمية أصلاً) عشان يحول
`config.js.template` لـ `config.js` فعلي باستخدام قيمة `API_BASE_URL`
وقت ما الـ container يشتغل، مش وقت الـ build.

### Environment Variables

| المتغير | مثال | الوصف |
|---|---|---|
| `API_BASE_URL` | `http://localhost:5000` | العنوان اللي المتصفح (browser) هيستخدمه عشان يوصل للـ backend. **ملحوظة:** ده لازم يكون عنوان يقدر المتصفح بتاع المستخدم يوصله فعليًا (يعني مش اسم الـ container زي `backend`، غالبًا `localhost:PORT_MAPPED` أو domain حقيقي)، لأن الطلبات بتتبعت من جوه المتصفح مش من جوه شبكة الـ Docker |

### Port
`80` (جوه الـ container) — اعمله map لأي port على جهازك (مثلاً `8080:80`)

---

## خلاصة سريعة لكل الـ Ports والـ Volumes

| Service | Container Port | يحتاج Volume؟ |
|---|---|---|
| database | 5432 | ✅ `/var/lib/postgresql/data` |
| backend | 5000 | ❌ |
| frontend | 80 | ❌ |

---

## تجربة محلية من غير Docker (اختياري، لو عايز تتأكد الكود شغال)

```bash
# 1) شغل postgres عندك محليًا أو في container منفصل
# 2) الـ backend
cd backend
pip install -r requirements.txt
export DB_HOST=localhost DB_USER=notes_user DB_PASSWORD=notes_pass DB_NAME=notes_db
python app.py

# 3) الـ frontend -- سيرفر بسيط لأي static files
cd frontend
cp config.js.template config.js
sed -i 's/${API_BASE_URL}/http:\/\/localhost:5000/' config.js
python -m http.server 8080
```

باقي عليك بقى: تكتب الـ 3 Dockerfiles، وتربطهم ببعض عن طريق docker
network أو docker-compose. لو عايز تتأكد من ترتيب الخطوات صح أو واجهتك
error، ابعتلي. 💪
