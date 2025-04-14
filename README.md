# Trading Engine

This project is a web-based trading engine designed to backtest and evaluate trading strategies using customizable technical indicators. Built with FastAPI, HTMX, Tailwind CSS, and Streamlit, it offers an interactive user interface and flexible backend for analyzing performance and ROI.

## Features

- 📈 Strategy backtesting
- 🧠 Technical indicators (moving averages, RSI, MACD, Bollinger Bands, etc.)
- 💹 ROI computation and result analysis
- 🧰 Streamlit-based trading engine interface
- 🥇 Leaderboard for strategy comparison
- 🔒 Google Auth signup (Firebase) (in-progress)
- ⚙️ Customization options (stop loss / take profit)


## Project Structure

```
.
├── data/               # Historical data & inputs
├── models/             # Strategy & result models
├── routers/            # FastAPI endpoints
├── static/             # Static assets (CSS, JS)
├── streamlit_app/      # Streamlit trading engine UI
├── templates/          # Jinja2 HTML templates
├── util/               # Utility functions
├── main.py             # FastAPI entrypoint
```
## Getting Started

1. **Make `run.sh` executable**  
   ```bash
   chmod +x run.sh
   ```

2. **Run the script**  
   ```bash
   ./run.sh
   ```

3. **Build and run the Rust backtester**  
   Open a new terminal, navigate to the Rust project directory, and run:
   ```bash
   cd axum/backtester
   cargo build
   cargo run
   ```

## License

MIT License