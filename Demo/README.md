# 🎬 ReelReason Demo - Frontend UI

This is the frontend demo for our LLM-Driven Conversational Movie Recommendation system. It provides a web interface showcasing personalized recommendations, explainability features, and the "Taste Wrapped" visualization.

## Tech Stack

- **React 19** + TypeScript
- **Vite** - Build tool and dev server
- **Tailwind CSS v4** - Styling
- **React Router v7** - Navigation
- **Lucide React** - Icons

---

## 🚀 Quick Start

### Prerequisites

- **Node.js** v18 or higher
- **npm** v9 or higher

Check your versions:
```bash
node --version
npm --version
```

### Setup

1. **Navigate to the demo folder:**
   ```bash
   cd Demo/movie-rec-demo
   ```

2. **Install dependencies:**
   ```bash
   npm install
   ```

3. **Start the development server:**
   ```bash
   npm run dev
   ```

4. **Open in browser:**
   The terminal will show a local URL (usually http://localhost:5173). Open it in your browser.

---

## 📁 Project Structure

```
movie-rec-demo/
├── src/
│   ├── main.tsx                 # React entry point
│   ├── App.tsx                  # Router setup with all routes
│   ├── index.css                # Tailwind imports + base styles
│   │
│   ├── components/
│   │   └── layout/
│   │       ├── Header.tsx       # Top navigation bar
│   │       └── PageLayout.tsx   # Page wrapper with header
│   │
│   └── pages/
│       ├── AuthPage.tsx         # Sign in / Sign up
│       ├── HomePage.tsx         # Recommendations + Chat
│       ├── ReviewsPage.tsx      # Manual review entry
│       ├── VisualizationPage.tsx # Taste Wrapped visualizations
│       └── ProfilePage.tsx      # User settings
│
├── index.html
├── package.json
├── vite.config.ts
├── postcss.config.js
└── tailwind.config.js (optional - using v4 defaults)
```

---

## 📄 Pages Overview

| Route | Page | Description |
|-------|------|-------------|
| `/` | Home | Recommendation carousels with explanations, floating chatbot |
| `/auth` | Auth | Login/signup with email + OAuth (Google, IMDB) |
| `/reviews` | Reviews | Search movies, write reviews, view history |
| `/visualization` | Taste Wrapped | Embedding charts, genre radar, yearly summary |
| `/profile` | Profile | Account settings, connected services |

---

## 🛠 Available Scripts

| Command | Description |
|---------|-------------|
| `npm run dev` | Start dev server with hot reload |
| `npm run build` | Build for production |
| `npm run preview` | Preview production build locally |
| `npm run lint` | Run ESLint |

---

## 🔌 Backend Integration

The demo is designed to work standalone with mock data, but can connect to:

- **RecommenderBackend** - For real recommendations (`/RecommenderBackend`)
- **AgenticFlow** - For chatbot responses (`/AgenticFlow`)

Environment variables (create `.env` file if needed):
```env
VITE_API_URL=http://localhost:8000
VITE_CHAT_API_URL=http://localhost:8001
```

---

## 🎨 Styling Notes

We're using **Tailwind CSS v4**, which has a simplified setup:
- No `tailwind.config.js` needed for basic usage
- Just `@import "tailwindcss";` in `index.css`
- Uses the `@tailwindcss/postcss` plugin

Dark theme colors we're using:
- Background: `bg-gray-950` (darkest), `bg-gray-900` (cards)
- Text: `text-white`, `text-gray-400` (secondary)
- Accent: `text-red-600`, `bg-red-600` (buttons, highlights)

---

## 🤝 Contributing

1. Create a feature branch: `git checkout -b feature/your-feature`
2. Make your changes
3. Test locally with `npm run dev`
4. Push and create a PR

### Adding New Components

Components go in `src/components/` organized by feature:
- `layout/` - Header, Footer, PageLayout
- `movies/` - MovieCard, MovieCarousel, MovieModal
- `chat/` - ChatWindow, ChatMessage, ChatInput
- `visualization/` - Charts and Taste Wrapped components

### Adding New Pages

1. Create the page in `src/pages/YourPage.tsx`
2. Add the route in `src/App.tsx`
3. Add nav link in `src/components/layout/Header.tsx` if needed

---

## 📝 TODO

- [ ] MovieCard component with poster and rating
- [ ] MovieCarousel with horizontal scrolling
- [ ] MovieModal with explanation + review form
- [ ] Chat components (ChatWindow, ChatToggle)
- [ ] Auth forms (login, signup, OAuth buttons)
- [ ] Review form and history
- [ ] Visualization charts (scatter plot, radar)
- [ ] Mock data files
- [ ] Connect to RecommenderBackend API
- [ ] Connect to AgenticFlow chatbot

---

## ❓ Troubleshooting

**Port already in use:**
```bash
npm run dev -- --port 3000
```

**Dependencies issues:**
```bash
rm -rf node_modules package-lock.json
npm install
```

**Tailwind not working:**
Make sure `@tailwindcss/postcss` is installed and `postcss.config.js` exists.
