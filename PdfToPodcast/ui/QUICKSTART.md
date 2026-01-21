# Frontend Quick Start Guide

Get the React frontend running in 3 minutes!

## Prerequisites

- Node.js 18 or higher
- npm or yarn

## Quick Start

### 1. Install Dependencies

```bash
cd frontend
npm install
```

This will install all required packages including:
- React, React DOM, React Router
- Redux Toolkit, React Redux
- Axios, React Dropzone
- WaveSurfer.js
- Tailwind CSS
- And more...

### 2. Start Development Server

```bash
npm run dev
```

The app will start at: **http://localhost:5173**

### 3. Open in Browser

Navigate to http://localhost:5173 and you should see the landing page!

---

## Available Scripts

```bash
# Development
npm run dev          # Start dev server with hot reload

# Build
npm run build        # Build for production

# Preview
npm run preview      # Preview production build

# Lint
npm run lint         # Run ESLint
```

---

## Project Structure Overview

```
src/
├── components/      # Reusable components
│   ├── ui/         # UI components (Button, Card, etc.)
│   ├── layout/     # Layout components (Header, Footer)
│   └── features/   # Feature components (PDFUploader, etc.)
├── pages/          # Page components (Home, Generate, etc.)
├── store/          # Redux store and slices
├── services/       # API integration
├── hooks/          # Custom React hooks
└── utils/          # Helper functions
```

---

## Configuration

### Environment Variables

Create a `.env` file in the frontend directory:

```env
VITE_API_URL=http://localhost:8000
```

### Path Aliases

The following path aliases are configured in `vite.config.js`:

```javascript
import Component from '@components/ui/Button'
import { uploadPDF } from '@services/api'
import { usePolling } from '@hooks/usePolling'
import store from '@store/store'
```

---

## Testing the Application

### 1. Home Page
- Should display landing page with features
- Click "Get Started Free" to navigate to Generate page

### 2. Generate Page
- **Step 1:** Upload a PDF file (drag-drop or click)
- **Step 2:** Select host and guest voices
- **Step 3:** Review and edit the generated script
- **Step 4:** Download the podcast audio

### 3. Projects Page
- View list of past projects
- Download or delete projects

### 4. Settings Page
- Configure API key
- Set voice preferences

---

## Common Issues

### Port 5173 Already in Use
```bash
# Change port in vite.config.js
server: {
  port: 3000  // Change to any available port
}
```

### Module Not Found
```bash
# Clear node_modules and reinstall
rm -rf node_modules package-lock.json
npm install
```

### API Connection Issues
- Make sure backend is running on port 8000
- Check `VITE_API_URL` in .env file
- Verify CORS is configured on backend

---

## Development Tips

### Hot Reload
- Save any file to see changes instantly
- No need to refresh browser

### Redux DevTools
- Install Redux DevTools browser extension
- Open DevTools to inspect state changes

### Network Tab
- Open browser DevTools → Network tab
- Monitor all API calls in real-time

### Console
- Check browser console for errors
- All API responses are logged during development

---

## Building for Production

### Create Production Build

```bash
npm run build
```

Output will be in `dist/` folder.

### Preview Production Build

```bash
npm run preview
```

### Deploy

The `dist/` folder can be deployed to:
- Vercel: `vercel deploy`
- Netlify: Drag & drop dist folder
- AWS S3: `aws s3 sync dist/ s3://bucket-name`
- GitHub Pages: Push dist to gh-pages branch

---

## Customization

### Change Colors

Edit `tailwind.config.js`:

```javascript
colors: {
  primary: {
    500: '#YOUR_COLOR',  // Change primary color
  }
}
```

### Add New Page

1. Create `src/pages/NewPage.jsx`
2. Add route in `src/App.jsx`:
   ```jsx
   <Route path="new-page" element={<NewPage />} />
   ```

### Add New Component

1. Create component in appropriate folder
2. Export from index.js
3. Import where needed

---

## Next Steps

1. ✅ Install dependencies
2. ✅ Start dev server
3. ✅ Test all features
4. 📖 Read full documentation in `README.md`
5. 🎨 Customize to your needs
6. 🚀 Deploy to production

---

## Support

- 📚 Full docs: `frontend/README.md`
- 🐛 Issues: Create GitHub issue
- 💬 Questions: Check documentation

---

**Happy coding!** 🎉
