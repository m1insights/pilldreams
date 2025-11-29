# Pilldreams - Epigenetics Oncology Intelligence Platform

A specialized intelligence platform for evaluating experimental assets targeting epigenetic mechanisms in cancer. Built with Next.js and Aceternity UI components.

## Features

- 🧬 Epigenetic target landscape (HDAC, BET, DNMT, HMT, etc.)
- 📊 Weighted scoring system (BioScore + ChemScore + TractabilityScore)
- 💊 Pipeline asset tracking with clinical trial data
- 🏢 Company-level intelligence and watchlist
- 📈 Interactive data tables with sorting and filtering
- 🎨 Modern UI with steel/silver gradient design system
- 📱 Fully responsive design
- ⚡ Fast page loads with Next.js

## Tech Stack

- [Next.js 14](https://nextjs.org/) - React framework
- [Tailwind CSS](https://tailwindcss.com/) - Styling
- [Aceternity UI](https://ui.aceternity.com/) - UI components
- [TypeScript](https://www.typescriptlang.org/) - Type safety
- [Framer Motion](https://www.framer.com/motion/) - Animations
- [FastAPI](https://fastapi.tiangolo.com/) - Backend API
- [Supabase](https://supabase.com/) - Database

## Getting Started

1. Install dependencies:

```bash
npm install
```

2. Run the development server:

```bash
npm run dev
```

3. Open [http://localhost:3000](http://localhost:3000) in your browser.

## Scoring System

Assets are scored 0-100 based on three weighted components:

- **BioScore (50%)**: Biological rationale from Open Targets
- **ChemScore (30%)**: Chemistry quality from ChEMBL
- **TractabilityScore (20%)**: Target druggability assessment

```
TotalScore = 0.5 × Bio + 0.3 × Chem + 0.2 × Tract
```
