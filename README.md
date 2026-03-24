# ICT Agent — Smart Money Chart Analyzer

A Django web app that analyzes trading charts using ICT (Inner Circle Trader) methodology powered by Claude AI vision.

## Features
- Upload any trading chart (screenshot/photo)
- Full ICT analysis: market structure, OBs, FVGs, liquidity, killzones
- Three outputs: TRADE SETUP (entry/SL/TP/R:R), WAIT & WATCH, or NO TRADE
- Analysis history / trade journal
- Dark terminal UI with Tailwind CSS

## Setup

1. Clone/download the project
2. Install dependencies:
   pip install -r requirements.txt
3. Copy .env.example to .env and add your Anthropic API key:
   cp .env.example .env
   # Edit .env and add ANTHROPIC_API_KEY=sk-ant-...
4. Run migrations:
   python manage.py migrate
5. Start the server:
   python manage.py runserver
6. Open http://127.0.0.1:8000

## Getting your API Key
Get your Anthropic API key at: https://console.anthropic.com

## ICT Concepts Analyzed
- Market structure (BOS, CHoCH, HH/HL/LH/LL)
- Liquidity pools (BSL, SSL, EQH, EQL, sweeps)
- Order Blocks (bullish, bearish, breakers, mitigation)
- Fair Value Gaps (FVG, IFVG)
- Power of 3 / AMD model
- Session analysis & killzones (London, NY, Asian)
- OTE (62-79% Fibonacci retracement)
- Premium/Discount zones
- PDH/PDL/PWH/PWL reference levels
- Market Maker Models (bullish/bearish)
