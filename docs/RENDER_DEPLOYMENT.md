# Render Deployment Guide for E Lost & Found Backend

This guide walks through deploying the FastAPI backend to [Render.com](https://render.com), a free/paid cloud hosting platform.

## Prerequisites

1. **Git Repository**: Push your code to GitHub, GitLab, or Bitbucket
2. **Render Account**: Sign up at [render.com](https://render.com)
3. **MongoDB Atlas**: Set up a free MongoDB database at [mongodb.com/cloud/atlas](https://mongodb.com/cloud/atlas)
4. **AWS Account** (optional): For S3 image uploads and SES email

---

## Step 1: Prepare MongoDB Atlas

1. Go to [MongoDB Atlas](https://mongodb.com/cloud/atlas)
2. Create a free cluster
3. Create a database user with username/password
4. Get the connection string:
   ```
   mongodb+srv://USERNAME:PASSWORD@cluster0.xxxxx.mongodb.net/?retryWrites=true&w=majority
   ```
5. Keep this connection string safe—you'll need it in Render

---

## Step 2: Deploy to Render

### Option A: Using render.yaml (Recommended)

1. Ensure `render.yaml` is in your **project root** (not backend/):
   ```
   E-Lost-Found/
   ├── render.yaml                 # ← At root level
   ├── backend/
   │   ├── Procfile
   │   ├── requirements.txt
   │   └── app/
   ├── frontend/
   └── docs/
   ```

2. Push to GitHub:
   ```bash
   git add render.yaml backend/Procfile backend/requirements.txt
   git commit -m "Add Render deployment config"
   git push
   ```

3. Go to [Render Dashboard](https://dashboard.render.com)
4. Click **New +** → **Web Service**
5. Select your GitHub repository
6. Render will auto-detect `render.yaml` and deploy

### Option B: Manual Setup (Without render.yaml)

1. Go to [Render Dashboard](https://dashboard.render.com)
2. Click **New +** → **Web Service**
3. Connect your GitHub account and select the repository
4. Configure:
   - **Name**: `elostfound-backend`
   - **Environment**: `Python 3`
   - **Build Command**: `pip install -r backend/requirements.txt`
   - **Start Command**: `cd backend && gunicorn -w 4 -k uvicorn.workers.UvicornWorker -b 0.0.0.0:$PORT app.main:app`
   - **Root Directory**: `backend` (optional, helps with build times)

---

## Step 3: Configure Environment Variables

After creating the service, go to **Settings** → **Environment**:

Add these environment variables:

```
MONGODB_URI=mongodb+srv://USERNAME:PASSWORD@cluster0.xxxxx.mongodb.net/?retryWrites=true&w=majority
JWT_SECRET=<generate-with: python -c "import secrets; print(secrets.token_urlsafe(32))">
ADMIN_EMAILS=admin@college.edu,superadmin@college.edu
ADMIN_PANEL_PASSWORD=<your-secure-password>
CORS_ORIGINS=https://your-frontend-domain.onrender.com
API_BASE_URL=https://your-backend-domain.onrender.com
AWS_ACCESS_KEY_ID=<your-aws-key>
AWS_SECRET_ACCESS_KEY=<your-aws-secret>
S3_BUCKET=elost-found-uploads
AWS_REGION=ap-south-1
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USER=your-email@gmail.com
SMTP_PASSWORD=<your-gmail-app-password>
SMTP_FROM=noreply@yourdomain.com
SES_FROM_EMAIL=noreply@yourdomain.com
```

**⚠️ Security Note**: Never commit `.env` files to git. Always set sensitive values in Render Dashboard.

---

## Step 4: Deploy Frontend (Optional)

Your frontend can also be hosted on Render or Vercel:

### Option 1: Render Static Site
1. Create a new **Static Site** service
2. Point to the `frontend/` directory
3. Build command: leave empty (no build step needed for static HTML)

### Option 2: Vercel
1. `npm install -g vercel`
2. `cd frontend && vercel`
3. Follow the prompts

---

## Step 5: Monitor Logs & Health Check

1. After deployment, Render will show **live logs**
2. Your API will be available at: `https://your-backend-domain.onrender.com`
3. Test health endpoint:
   ```bash
   curl https://your-backend-domain.onrender.com/health
   # Response: {"status": "ok"}
   ```

4. View API docs: `https://your-backend-domain.onrender.com/docs`

---

## Common Issues & Solutions

### Error: "MONGODB_URI is still placeholder"
**Solution**: Ensure `MONGODB_URI` is set correctly in Render Environment Variables (not in git)

### Error: "Port 8000 already in use"
**Solution**: Render dynamically assigns `$PORT`—don't hardcode port 8000. The updated `main.py` reads from `PORT` env var.

### Error: "ModuleNotFoundError: No module named 'gunicorn'"
**Solution**: Ensure `gunicorn` is in `requirements.txt` (already added)

### Slow Cold Starts
**Solution**: This is normal on free tier. Paid plans have faster cold starts.

### CORS errors on frontend
**Solution**: Update `CORS_ORIGINS` in Render Environment Variables to match your frontend domain

---

## Useful Render Commands (via Render CLI)

```bash
# Install Render CLI
npm install -g render

# Login to Render
render login

# Deploy from command line
render deploy --service-id=<your-service-id>

# View logs
render logs --service-id=<your-service-id> --tail
```

---

## Local Testing Before Deploy

Test locally to ensure everything works:

```bash
cd backend

# Create local .env
cp .env.example .env
# Edit .env with your MongoDB URI

# Install dependencies
pip install -r requirements.txt

# Run locally
python -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

# Visit: http://localhost:8000/docs
```

---

## Next Steps

1. ✅ Deploy backend to Render
2. ✅ Deploy frontend (Render Static or Vercel)
3. ✅ Update frontend `API_BASE_URL` to point to Render backend
4. ✅ Set up monitoring alerts in Render Dashboard
5. ✅ Enable backups for MongoDB Atlas

---

## Support

- **Render Docs**: https://render.com/docs
- **FastAPI Docs**: https://fastapi.tiangolo.com
- **MongoDB Atlas**: https://docs.atlas.mongodb.com
