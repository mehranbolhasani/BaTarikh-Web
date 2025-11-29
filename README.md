# BaTarikh-Web

A modern web application for displaying historical content from a Telegram channel, built with Next.js, React, and Supabase.

## Overview

BaTarikh-Web is a Persian/Farsi web application that aggregates and displays historical posts from a Telegram channel. The application features:

- **Media Support**: Images, videos, audio files, and documents
- **Filtering**: Filter posts by media type (image, video, audio, document, text)
- **Pagination**: Browse through posts with efficient pagination
- **RTL Support**: Full right-to-left layout support for Persian content
- **SEO Optimized**: Structured data, sitemap, and robots.txt
- **Performance**: Optimized images, lazy loading, and efficient data fetching

## Project Structure

```
BaTarikh-Web/
├── web/                 # Next.js web application
│   ├── src/
│   │   ├── app/         # Next.js app directory (pages, routes)
│   │   ├── components/  # React components
│   │   ├── lib/         # Utility functions and constants
│   │   └── types/       # TypeScript type definitions
│   └── public/          # Static assets
└── worker/              # Python worker for ingesting Telegram content
    └── ingest.py        # Telegram bot worker
```

## Prerequisites

- Node.js 18+ and npm
- Python 3.8+ (for worker)
- Supabase account and project
- Telegram API credentials (for worker)

## Getting Started

### Web Application Setup

1. **Install dependencies**:
   ```bash
   cd web
   npm install
   ```

2. **Set up environment variables**:
   Copy `.env.example` to `.env.local` and fill in the required values:
   ```bash
   cp .env.example .env.local
   ```

3. **Run the development server**:
   ```bash
   npm run dev
   ```

   Open [http://localhost:3000](http://localhost:3000) in your browser.

### Worker Setup

1. **Install Python dependencies**:
   ```bash
   cd worker
   pip install -r requirements.txt
   ```

2. **Set up environment variables**:
   Create a `.env` file in the `worker` directory with the required variables (see `.env.example`).

3. **Run the worker**:
   ```bash
   python ingest.py
   ```

## Environment Variables

### Web Application

See `web/.env.example` for all required environment variables:

- `NEXT_PUBLIC_SITE_URL` - Your site's public URL
- `NEXT_PUBLIC_SUPABASE_URL` - Supabase project URL
- `NEXT_PUBLIC_SUPABASE_ANON_KEY` - Supabase anonymous key
- `NEXT_PUBLIC_TELEGRAM_CHANNEL` - Telegram channel username
- `NEXT_PUBLIC_MEDIA_HOST` - Media CDN hostname

### Worker

See `worker/.env.example` for worker-specific environment variables.

## Development

### Available Scripts

- `npm run dev` - Start development server
- `npm run build` - Build for production
- `npm run start` - Start production server
- `npm run lint` - Run ESLint

### Code Structure

- **Components**: Reusable React components in `src/components/`
- **Pages**: Next.js pages and routes in `src/app/`
- **Utilities**: Helper functions in `src/lib/`
- **Types**: TypeScript definitions in `src/types/`

## Features

### Media Types

- **Image**: Displayed with optimized Next.js Image component
- **Video**: Embedded using Vidstack player
- **Audio**: Embedded using Vidstack audio player
- **Document**: PDF download links
- **Text**: Text-only posts

### Filtering & Pagination

- Filter posts by media type
- Pagination with page numbers and navigation
- Persian number formatting

### SEO

- Structured data (JSON-LD)
- Dynamic metadata generation
- Sitemap generation
- Robots.txt configuration

## Deployment

### Vercel (Recommended)

1. Push your code to GitHub
2. Import the project in Vercel
3. Add environment variables in Vercel dashboard
4. Deploy

### Other Platforms

The application can be deployed to any platform that supports Next.js:
- Netlify
- AWS Amplify
- Railway
- Self-hosted with Node.js

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Submit a pull request

## License

See LICENSE file for details.

## Acknowledgments

- Built with [Next.js](https://nextjs.org/)
- UI components from [shadcn/ui](https://ui.shadcn.com/)
- Media player by [Vidstack](https://vidstack.io/)
- Database by [Supabase](https://supabase.com/)
