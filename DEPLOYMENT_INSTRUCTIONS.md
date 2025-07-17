# 🚀 Deployment Instructions

## Part 1: Create GitHub Repository

### Step 1: Create GitHub Repository
1. Go to [GitHub.com](https://github.com) and sign in
2. Click the "+" icon in the top right corner
3. Select "New repository"
4. Fill in the details:
   - **Repository name**: `one-piece-character-tracker`
   - **Description**: `A web application that tracks One Piece character values over time with interactive charts`
   - **Visibility**: Public (recommended) or Private
   - **DO NOT** initialize with README, .gitignore, or license (we already have these)
5. Click "Create repository"

### Step 2: Push Code to GitHub
After creating the repository, run these commands in your terminal:

```bash
# Add the GitHub repository as remote origin
git remote add origin https://github.com/YOUR_USERNAME/one-piece-character-tracker.git

# Push the code to GitHub
git branch -M main
git push -u origin main
```

Replace `YOUR_USERNAME` with your actual GitHub username.

---

## Part 2: Deploy to Render

### Step 1: Create Render Account
1. Go to [Render.com](https://render.com)
2. Sign up for a free account
3. You can sign up with GitHub for easier integration

### Step 2: Connect GitHub Repository
1. In your Render dashboard, click "New +"
2. Select "Web Service"
3. Choose "Build and deploy from a Git repository"
4. Click "Connect" next to GitHub
5. Authorize Render to access your GitHub repositories
6. Find and select your `one-piece-character-tracker` repository

### Step 3: Configure Deployment Settings
Fill in the deployment configuration:

**Basic Settings:**
- **Name**: `one-piece-character-tracker` (or your preferred name)
- **Region**: Choose the region closest to your users
- **Branch**: `main`
- **Root Directory**: Leave blank
- **Runtime**: `Python 3`

**Build & Deploy Settings:**
- **Build Command**: `pip install -r requirements.txt`
- **Start Command**: `python app.py`

**Environment Variables:**
Click "Advanced" and add these environment variables:
- `FLASK_ENV` = `production`
- `HOST` = `0.0.0.0`
- `PORT` = `10000`
- `DATABASE_PATH` = `one_piece_tracker.db`
- `SECRET_KEY` = `your-secret-key-here` (generate a random string)

### Step 4: Deploy
1. Click "Create Web Service"
2. Render will automatically:
   - Clone your repository
   - Install dependencies
   - Build and deploy your application
3. Wait for the deployment to complete (usually 2-5 minutes)

### Step 5: Access Your Application
Once deployed, Render will provide you with a URL like:
`https://one-piece-character-tracker.onrender.com`

---

## 🔧 Render Configuration Details

### Free Tier Limitations
- **Sleep Mode**: Free services sleep after 15 minutes of inactivity
- **Cold Starts**: First request after sleeping takes 30+ seconds
- **Monthly Hours**: 750 hours per month (enough for most personal projects)

### Upgrading to Paid Plan
For production use, consider upgrading to a paid plan ($7/month) for:
- No sleep mode
- Faster cold starts
- More resources
- Custom domains

### Database Persistence
The SQLite database is included in your repository and will persist across deployments.

---

## 🛠️ Troubleshooting

### Common Issues

**1. Build Fails**
- Check that `requirements.txt` is in the root directory
- Ensure all dependencies are listed correctly
- Check the build logs in Render dashboard

**2. Application Won't Start**
- Verify the start command is `python app.py`
- Check that `PORT` environment variable is set to `10000`
- Review application logs in Render dashboard

**3. Database Issues**
- Ensure `one_piece_tracker.db` is committed to your repository
- Check that `DATABASE_PATH` environment variable is set correctly

**4. Static Files Not Loading**
- Verify the `static/` directory is in your repository
- Check that Flask is serving static files correctly

### Viewing Logs
1. Go to your Render dashboard
2. Click on your service
3. Go to "Logs" tab to see real-time application logs

### Manual Deployment
If automatic deployment fails:
1. Go to your service dashboard
2. Click "Manual Deploy"
3. Select "Deploy latest commit"

---

## 🔄 Updating Your Application

### Making Changes
1. Make changes to your code locally
2. Test changes locally: `python app.py`
3. Commit changes: `git add . && git commit -m "Your change description"`
4. Push to GitHub: `git push origin main`
5. Render will automatically redeploy (if auto-deploy is enabled)

### Manual Redeploy
If auto-deploy is disabled:
1. Go to Render dashboard
2. Click "Manual Deploy"
3. Select the latest commit

---

## 🌟 Optional Enhancements

### Custom Domain
1. Purchase a domain name
2. In Render dashboard, go to "Settings"
3. Add your custom domain
4. Update DNS records as instructed

### Environment-Specific Configurations
Create different branches for different environments:
- `main` - Production
- `staging` - Staging environment
- `development` - Development environment

### Monitoring
Set up monitoring and alerts:
1. Enable health checks in Render
2. Set up uptime monitoring (UptimeRobot, etc.)
3. Configure error tracking (Sentry, etc.)

---

## 📞 Support

If you encounter issues:
1. Check Render's [documentation](https://render.com/docs)
2. Review the application logs
3. Check GitHub repository issues
4. Contact Render support for platform-specific issues

---

**🎉 Congratulations!** Your One Piece Character Tracker is now live on the internet! 🏴‍☠️