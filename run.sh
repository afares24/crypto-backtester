# kills both servers
trap 'kill $(jobs -p)' EXIT

uvicorn fastapi_app:app --reload &
streamlit run trading_engine_app.py &

wait