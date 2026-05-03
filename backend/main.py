from fastapi import FastAPI

app = FastAPI(title="Reco-Spark API")

@app.get("/")
def read_root():
    return {"message": "Reco-Spark Backend is running!"}

# Model loading and the /recommendations POST endpoint will be added here later.
