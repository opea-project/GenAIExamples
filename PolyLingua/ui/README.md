# PolyLingua UI

A modern, single-page translation interface built with Next.js 14, React, and shadcn/ui components.

## Features

- 🌐 Clean and intuitive translation interface
- 🎨 Beautiful UI using shadcn/ui components and Tailwind CSS
- 📱 Fully responsive design
- 🌍 Support for 15 languages (Spanish, French, German, Italian, Portuguese, Russian, Japanese, Korean, Chinese, Arabic, Hindi, Dutch, Polish, Turkish, Swedish)
- ⚡ Real-time character count
- 🔄 Loading states and smooth animations

## Tech Stack

- **Framework**: Next.js 14 (App Router)
- **UI Components**: shadcn/ui (Radix UI + Tailwind CSS)
- **Styling**: Tailwind CSS
- **Icons**: Lucide React
- **Language**: TypeScript

## Getting Started

### Prerequisites

- Node.js 18.x or higher
- npm, yarn, or pnpm

### Installation

1. Navigate to the ui directory:

```bash
cd ui
```

2. Install dependencies:

```bash
npm install
# or
yarn install
# or
pnpm install
```

3. Run the development server:

```bash
npm run dev
# or
yarn dev
# or
pnpm dev
```

4. Open YOUR_HOST_IP:3000 in your browser to see the application.

## Project Structure

```
ui/
├── app/
│   ├── globals.css          # Global styles and Tailwind configuration
│   ├── layout.tsx            # Root layout component
│   └── page.tsx              # Main page (home)
├── components/
│   ├── ui/                   # shadcn/ui components
│   │   ├── button.tsx
│   │   ├── card.tsx
│   │   ├── label.tsx
│   │   ├── select.tsx
│   │   └── textarea.tsx
│   └── polylingua-form.tsx   # Main translation form component
├── lib/
│   └── utils.ts              # Utility functions
├── package.json
├── tailwind.config.ts
├── tsconfig.json
└── next.config.js
```

## Usage

1. **Enter Text**: Type or paste the text you want to translate in the source text area
2. **Select Language**: Choose your target language from the dropdown menu
3. **Translate**: Click the "Translate" button to see the translation

## Backend Integration

Currently, the app uses a mock translation function. To connect to a real translation backend:

1. Update the `handleTranslate` function in `components/polylingua-form.tsx`:

```typescript
const handleTranslate = async () => {
  if (!sourceText.trim()) return;

  setIsLoading(true);

  try {
    const response = await fetch("/api/translate", {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify({
        text: sourceText,
        targetLanguage: targetLanguage,
      }),
    });

    const data = await response.json();
    setTranslatedText(data.translatedText);
  } catch (error) {
    console.error("Translation error:", error);
    setTranslatedText("Error: Translation failed. Please try again.");
  } finally {
    setIsLoading(false);
  }
};
```

2. Create an API route at `app/api/translate/route.ts` to handle the backend connection.

## Build for Production

```bash
npm run build
npm start
```

## Customization

### Adding More Languages

Edit the `languages` array in `components/polylingua-form.tsx`:

```typescript
const languages = [
  { code: "es", name: "Spanish" },
  { code: "fr", name: "French" },
  // Add more languages here
];
```

### Styling

- Global styles: `app/globals.css`
- Tailwind configuration: `tailwind.config.ts`
- Component-specific styles: Use Tailwind utility classes

## License

MIT
