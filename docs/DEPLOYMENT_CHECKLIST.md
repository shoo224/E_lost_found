# Production Deployment Checklist

Complete this checklist before deploying to Render to ensure your backend runs smoothly in production.

## Security & Configuration

- [ ] Generate a strong JWT_SECRET: `python -c "import secrets; print(secrets.token_urlsafe(32))"`
  - Do NOT use the default "change-me-in-production" value
  - Store securely in Render Environment Variables

- [ ] Set ADMIN_PANEL_PASSWORD to a strong password
  - Do NOT commit to git
  - Store in Render Environment Variables

- [ ] Ensure CORS_ORIGINS is set to your frontend domain(s)
  - Example: `https://yourdomain.onrender.com`
  - Do NOT use wildcard `*` in production

- [ ] Never commit `.env` files to git
  - `.env` files are in `.gitignore`
  - Always use Render Dashboard for environment variables

## Database & Storage

- [ ] MongoDB Atlas cluster is running and accessible
  - Connection string format: `mongodb+srv://user:pass@cluster.net/?retryWrites=true&w=majority`
  - Whitelist your Render instance IP or use network access without IP restrictions
  - Test connection locally: `python health_check.py`

- [ ] Database backup strategy in place
  - Enable MongoDB Atlas automated backups
  - Test restore procedure

- [ ] AWS S3 bucket created and configured (if using image uploads)
  - [ ] IAM user created with S3 access only
  - [ ] Access key and secret stored in Render Environment Variables
  - [ ] Bucket name matches S3_BUCKET env var

## Email Configuration

- [ ] Email provider configured (Gmail, AWS SES, or SMTP)
  - [ ] SMTP credentials working (test locally)
  - [ ] From address whitelisted if required

- [ ] Email templates reviewed and tested
  - [ ] Claim approval email content
  - [ ] Claim rejection email content
  - [ ] OTP email format

## Backend Configuration

- [ ] `requirements.txt` contains all production dependencies
  - [ ] Includes `gunicorn`
  - [ ] Pinned versions (no `*` or `>=` without upper bounds for security)

- [ ] `Procfile` exists in backend/ directory
  - [ ] Correct start command: `gunicorn -w 4 -k uvicorn.workers.UvicornWorker -b 0.0.0.0:$PORT app.main:app`

- [ ] `render.yaml` at project root with correct build commands
  - [ ] Build command: `pip install -r requirements.txt`
  - [ ] All critical env vars documented

- [ ] `app/main.py` updated to support dynamic PORT
  - [ ] `PORT = os.environ.get("PORT", 8000)` 
  - [ ] Uses port, not hardcoded 8000

- [ ] Health check endpoint works
  - [ ] `GET /health` returns `{"status": "ok"}`
  - [ ] Test locally: `curl http://localhost:8000/health`

## Testing

- [ ] Run `python health_check.py` - all checks pass
- [ ] FastAPI docs accessible: `http://localhost:8000/docs`
- [ ] Test key endpoints locally:
  - [ ] `GET /stats` - returns item counts
  - [ ] `GET /health` - returns ok status
  - [ ] Auth endpoints work
  - [ ] Claim creation works
  - [ ] Admin endpoints require auth

- [ ] Test with production-like environment:
  ```bash
  cp .env.production .env
  # Edit .env with real credentials
  python -m uvicorn app.main:app --host 0.0.0.0 --port 8000
  ```

## Frontend Integration

- [ ] Frontend `API_BASE_URL` points to backend
  - [ ] Local dev: `http://localhost:8000`
  - [ ] Production: `https://your-backend-domain.onrender.com`

- [ ] CORS errors not occurring in browser console
  - [ ] If CORS error: update CORS_ORIGINS in Render

- [ ] Authentication flow works end-to-end
  - [ ] Login succeeds
  - [ ] Token stored in localStorage
  - [ ] Protected endpoints accessible with token

## Deployment Steps

1. **Commit and push to git:**
   ```bash
   git add .
   git commit -m "Configure FastAPI for Render deployment"
   git push origin main
   ```

2. **Create Render Web Service:**
   - Go to https://dashboard.render.com
   - Click "New +" → "Web Service"
   - Select your GitHub repository
   - Render will auto-detect `render.yaml`

3. **Add Environment Variables in Render Dashboard:**
   - Navigate to Service Settings → Environment
   - Add all critical variables (see `backend/.env.production`)

4. **Monitor Initial Deployment:**
   - Check logs in Render Dashboard
   - Verify `/health` endpoint returns ok
   - Check `/docs` (Swagger UI) is accessible

5. **Test Production Endpoints:**
   ```bash
   curl https://your-backend-domain.onrender.com/health
   curl https://your-backend-domain.onrender.com/stats
   ```

## Post-Deployment

- [ ] Set up monitoring and alerts in Render Dashboard
- [ ] Configure auto-restart on failure (in Render settings)
- [ ] Enable auto-deploy on git push
- [ ] Test production functionality end-to-end
- [ ] Document your Render app URL and domain
- [ ] Set up backup strategy for MongoDB

## Troubleshooting

**App won't start? Check these:**
- [ ] `MONGODB_URI` is correct and Render has network access
- [ ] `JWT_SECRET` is not the default placeholder
- [ ] All required environment variables are set
- [ ] View build logs in Render Dashboard for errors

**Too many errors? Check these:**
- [ ] Database connection is stable
- [ ] AWS credentials (if used) are correct
- [ ] Email configuration works
- [ ] CORS origins are correct

**Performance issues? Consider:**
- [ ] Upgrade Render plan (free tier may be slow)
- [ ] Optimize database queries
- [ ] Enable MongoDB indexing for `claim_requests` collection
- [ ] Cache frequently accessed data
