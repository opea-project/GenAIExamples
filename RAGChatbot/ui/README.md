# RAG Chatbot UI

A clean and elegant React-based user interface for the RAG Chatbot application.

## Features

- PDF file upload with drag-and-drop support
- Real-time chat interface
- Modern, responsive design with Tailwind CSS
- Built with Vite for fast development
- Live status updates
- Mobile-friendly

## Quick Start

The UI runs automatically when using Docker Compose. See the main project README for setup instructions.

The UI will be available at `http://localhost:3000`

## Development

This UI runs as part of the Docker Compose setup. For local development without Docker, you can use the scripts below, but Docker Compose is the recommended approach.

### Available Scripts (Local Development Only)

```bash
# Start development server with hot reload
npm run dev

# Build for production
npm run build

# Preview production build
npm run preview

# Lint code
npm run lint
```

### Project Structure

```
ui/
├── src/
│   ├── components/
│   │   ├── Header.jsx          # App header
│   │   ├── StatusBar.jsx       # Document status display
│   │   ├── PDFUploader.jsx     # PDF upload component
│   │   └── ChatInterface.jsx   # Chat UI
│   ├── services/
│   │   └── api.js              # API client
│   ├── App.jsx                 # Main app component
│   ├── main.jsx                # Entry point
│   └── index.css               # Global styles
├── public/                     # Static assets
├── index.html                  # HTML template
├── vite.config.js             # Vite configuration
├── tailwind.config.js         # Tailwind CSS config
└── package.json               # Dependencies
```

## Configuration

When running with Docker Compose, the UI automatically connects to the backend. Configuration is handled through the docker-compose.yml file.

## Usage

1. **Start the application** using Docker Compose (from the `rag-chatbot` directory):

   ```bash
   docker compose up --build
   ```

2. **Upload a PDF**:

   - Drag and drop a PDF file, or
   - Click "Browse Files" to select a file
   - Wait for processing to complete

4. **Start chatting**:
   - Type your question in the input field
   - Press Enter or click Send
   - Get AI-powered answers based on your document

## Features in Detail

### PDF Upload

- Drag-and-drop support
- File validation (PDF only, max 50MB)
- Upload progress indicator
- Success/error notifications

### Chat Interface

- Real-time messaging
- Message history
- Typing indicators
- Timestamp display
- Error handling

### Status Bar

- Document upload status
- Progress tracking
- Quick reset functionality

## Building for Production

```bash
# Build the production bundle
npm run build

# The built files will be in the dist/ directory
# Serve with any static file server
```

### Deploy with Docker Compose

The UI is automatically deployed when using Docker Compose from the root `rag-chatbot` directory. The Dockerfile in this directory is used by the docker-compose.yml configuration.

## Customization

### Styling

The UI uses Tailwind CSS. Customize colors and theme in `tailwind.config.js`:

```javascript
theme: {
  extend: {
    colors: {
      primary: {
        // Your custom colors
      }
    }
  }
}
```

### Backend Integration

The UI communicates with the backend through `src/services/api.js`. When running with Docker Compose, the backend is automatically available.

## Troubleshooting

### Build Issues

**Problem**: Build fails with dependency errors

**Solution**:

```bash
# Clear node_modules and reinstall
rm -rf node_modules package-lock.json
npm install
```

### Styling Issues

**Problem**: Styles not applying

**Solution**:

```bash
# Rebuild Tailwind CSS
npm run dev
```

## Browser Support

- Chrome/Edge (latest)
- Firefox (latest)
- Safari (latest)
- Mobile browsers (iOS Safari, Chrome Mobile)

## Performance

- Optimized bundle size with Vite
- Code splitting for faster loads
- Lazy loading of components
- Efficient re-renders with React

## License

MIT

---

**Built with**: React, Vite, Tailwind CSS, Axios, and Lucide Icons
