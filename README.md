# E Lost & Found

A production-ready web application for reporting and matching lost and found items. Built with FastAPI (Python), MongoDB Atlas, JWT + Email OTP auth, HTML/CSS/JS frontend, AWS S3 (images), and optional AWS SES (email).

## Features

- **Homepage**: Item Lost, Item Found, Total Items Lost stats
- **Report Lost**: College email OTP verify, item details, optional image upload
- **Report Found**: Student (enrollment + OTP) or Administration (admin login)
- **Matching**: Instant matching on submit + hourly background job (APScheduler); MongoDB text search
- **Claims**: Lost person can claim a found item; admin approves/rejects
- **Email**: OTP and match/claim notifications via SMTP or AWS SES

## Stack

- **Backend**: FastAPI (Python 3.10+)
- **Database**: MongoDB Atlas
- **Auth**: JWT + Email OTP
- **Frontend**: HTML/CSS/JS (no framework)
- **Storage**: AWS S3 (images)
- **Email**: SMTP or AWS SES
- **Hosting**: AWS EC2 + Nginx reverse proxy

## Project structure

```
E-Lost&Found/
├── backend/
│   ├── app/
│   │   ├── main.py          # FastAPI app, CORS, routers, APScheduler
│   │   ├── config.py        # Settings from .env
│   │   ├── database.py      # MongoDB connection
│   │   ├── models/          # Pydantic schemas
│   │   ├── routers/         # auth, lost, found, claims, admin, stats
│   │   ├── services/        # otp, email, s3, matcher
│   │   ├── jobs/            # Hourly matching job
│   │   └── utils/           # security (JWT)
│   ├── requirements.txt
│   └── .env.example
├── frontend/
│   ├── index.html, lost.html, found.html, admin.html, claim.html
│   ├── css/style.css
│   └── js/ (api, auth, lost, found, admin, main)
├── nginx/
│   └── e-lost-found.conf
└── README.md
```

## Local setup

### 1. Backend

```bash
cd backend
python -m venv venv
# Windows: venv\Scripts\activate
# Linux/Mac: source venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
# Edit .env: set MONGODB_URI, JWT_SECRET, and optionally AWS/SMTP
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

### 2. Frontend

- Open `frontend/index.html` in a browser (e.g. Live Server on port 5500), or
- Serve the `frontend` folder with any static server (e.g. `npx serve frontend -p 3000`).

### 3. CORS

In backend `.env`, set:

```env
CORS_ORIGINS=http://localhost:5500,http://127.0.0.1:5500,http://localhost:3000
```

If the frontend is on a different port, add it to `CORS_ORIGINS`.

### 4. API base URL (frontend)

By default the frontend calls `http://localhost:8000`. To change (e.g. for production), set in HTML or in a config:

```html
<script>window.API_BASE_URL = 'https://your-api.com';</script>
```

Or serve a small `config.js` that sets `window.API_BASE_URL`.

## Environment variables (.env)

| Variable | Description |
|----------|-------------|
| `MONGODB_URI` | MongoDB Atlas connection string |
| `JWT_SECRET` | Long random string for JWT signing |
| `JWT_ALGORITHM` | Usually `HS256` |
| `ACCESS_TOKEN_EXPIRE_MINUTES` | Token lifetime |
| `OTP_EXPIRE_MINUTES` | OTP validity |
| `AWS_ACCESS_KEY_ID` | IAM user key (S3 + SES) |
| `AWS_SECRET_ACCESS_KEY` | IAM secret |
| `AWS_REGION` | e.g. `ap-south-1` |
| `S3_BUCKET` | Bucket name for uploads |
| `SES_FROM_EMAIL` | Sender email (SES verified) |
| `SMTP_*` | Fallback SMTP (host, port, user, password, from) |
| `CORS_ORIGINS` | Comma-separated frontend origins |
| `ADMIN_EMAILS` | Comma-separated admin emails (get admin role on login) |
| `API_BASE_URL` | Base URL for links in emails (e.g. claim link) |

## MongoDB collections

- **users**: email, enrollment_number, role (student/admin), is_verified, created_at
- **lost_items**: name, college_email, where_lost, when_lost, item_name, description, image_url, status, matched_found_ids
- **found_items**: item_name, date_found, time_found, description, location, image_url, submitted_by, enrollment_number, status, matched_lost_ids
- **claims**: found_item_id, lost_item_id, claimed_by, status (pending/approved/rejected), reviewed_at, reviewed_by
- **otp_store**: key (email/enrollment), otp, expires_at, purpose

Text indexes are created automatically on lost_items and found_items for matching.

## AWS deployment (EC2 + S3 + MongoDB Atlas)

### MongoDB Atlas

1. Create a cluster at [MongoDB Atlas](https://cloud.mongodb.com).
2. Create a database user and get the connection string.
3. Network Access: add your EC2 public IP (or 0.0.0.0/0 for dev only).
4. Set `MONGODB_URI` in `.env` on EC2.

### S3

1. Create a bucket (e.g. `elost-found-uploads`).
2. Create an IAM user with `s3:PutObject`, `s3:GetObject` on this bucket.
3. Create access keys and set `AWS_ACCESS_KEY_ID`, `AWS_SECRET_ACCESS_KEY`, `AWS_REGION`, `S3_BUCKET` in `.env`.
4. (Optional) Make the bucket or object public for image URLs, or use presigned URLs.

### SES (email)

1. Verify your domain or email in AWS SES.
2. IAM user needs `ses:SendEmail` (or add to same user as S3).
3. Set `SES_FROM_EMAIL` in `.env`. For production, move out of SES sandbox if needed.

### EC2

1. Launch Ubuntu 22.04; open ports 22 (SSH), 80 (HTTP), 443 (HTTPS).
2. SSH in: `ssh -i your-key.pem ubuntu@<EC2-public-IP>`.
3. Install: `sudo apt update && sudo apt install -y python3-pip python3-venv nginx`.
4. Clone repo (or upload files) to e.g. `/var/www/elostfound/`.
5. Backend:
   ```bash
   cd /var/www/elostfound/backend
   python3 -m venv venv
   source venv/bin/activate
   pip install -r requirements.txt
   cp .env.example .env
   # Edit .env with production values
   ```
6. Run with Uvicorn (for production use systemd or gunicorn):
   ```bash
   uvicorn app.main:app --host 0.0.0.0 --port 8000
   ```
7. Create systemd service (optional) so the app restarts on reboot:
   - `/etc/systemd/system/elostfound.service` with `ExecStart=/var/www/elostfound/backend/venv/bin/uvicorn app.main:app --host 0.0.0.0 --port 8000`
   - `sudo systemctl enable elostfound && sudo systemctl start elostfound`
8. Nginx: copy `nginx/e-lost-found.conf` to `/etc/nginx/sites-available/`, set `server_name` and `root`, then:
   ```bash
   sudo ln -s /etc/nginx/sites-available/e-lost-found.conf /etc/nginx/sites-enabled/
   sudo nginx -t && sudo systemctl reload nginx
   ```
9. Frontend: set `window.API_BASE_URL` to your domain (e.g. `https://your-domain.com`) if you proxy API under the same host; or point to `https://your-domain.com` and proxy `/stats`, `/auth`, `/lost`, `/found`, `/claims`, `/admin` to `http://127.0.0.1:8000` (see Nginx comment in config).

### Nginx reverse proxy

- **Option A**: Frontend and API on same domain. Nginx serves static files from `root /var/www/elostfound/frontend` and proxies e.g. `/api` to `http://127.0.0.1:8000` with `rewrite ^/api(.*)$ $1 break;`. Then set frontend `API_BASE_URL` to `https://your-domain.com/api` (so requests go to `/api/stats`, `/api/auth`, etc.; backend receives `/stats`, `/auth` if rewrite strips `/api`). **Or** proxy without rewrite so backend serves at `/api` (you’d mount FastAPI at a prefix in that case).
- **Option B**: Simpler: proxy paths like `location /stats`, `location /auth`, etc. to `http://127.0.0.1:8000` without an `/api` prefix. Then frontend `API_BASE_URL = 'https://your-domain.com'` and no rewrite.

The provided `e-lost-found.conf` uses Option A with `rewrite` so backend sees paths without `/api`. Ensure frontend uses `API_BASE_URL = 'https://your-domain.com/api'` so that `api.get('/stats')` becomes `GET https://your-domain.com/api/stats` and Nginx forwards to `http://127.0.0.1:8000/stats`.

## First admin user

Add your email to `ADMIN_EMAILS` in `.env`. The first time you log in via Admin page with that email (OTP), you’ll get the admin role. Alternatively, insert a user document in MongoDB with `role: "admin"` and your email.

## License

Use as needed for your project.
