from uvicorn import run

if __name__ == "__main__":
    # Start the PromotionService on port 8108
    run("app.main:app", host="0.0.0.0", port=8108, reload=False)
