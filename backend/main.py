from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from contextlib import asynccontextmanager
from pathlib import Path
import pandas as pd
import logging
import os
import sys
import json

# ── Windows / Hadoop & PySpark Worker Fix ────────────────────────────────────
HADOOP_HOME_PATH = "C:\\hadoop"
os.environ["HADOOP_HOME"] = HADOOP_HOME_PATH
os.environ["PATH"] = f"{HADOOP_HOME_PATH}\\bin;" + os.environ.get("PATH", "")

os.environ["PYSPARK_PYTHON"] = sys.executable
os.environ["PYSPARK_DRIVER_PYTHON"] = sys.executable
os.environ["SPARK_LOCAL_IP"] = "127.0.0.1"
os.environ["PYTHONPATH"] = os.pathsep.join(sys.path)

from pyspark.sql import SparkSession
from pyspark.ml.recommendation import ALSModel
from pyspark.sql.functions import explode, col

logger = logging.getLogger("recospark")
logging.basicConfig(level=logging.INFO)

spark     = None
model     = None
movies_df = None

PROJECT_ROOT = Path(__file__).resolve().parent.parent
MODEL_PATH   = str(PROJECT_ROOT / "ml_pipeline" / "models" / "als_model")
MOVIES_CSV   = str(PROJECT_ROOT / "data" / "movies.csv")


@asynccontextmanager
async def lifespan(app: FastAPI):
    global spark, model, movies_df

    TEMP_DIR = "C:/temp/spark"
    os.makedirs(TEMP_DIR, exist_ok=True)

    try:
        spark = (
            SparkSession.builder
            .appName("RecoSpark-Serving")
            .master("local[1]")
            .config("spark.driver.memory", "4g")
            .config("spark.executor.memory", "4g")
            .config("spark.python.worker.reuse", "true")
            .config("spark.driver.bindAddress", "127.0.0.1")
            .config("spark.local.dir", TEMP_DIR)
            .config("spark.authenticate", "false")
            .getOrCreate()
        )
        spark.sparkContext.setLogLevel("WARN")
        logger.info("SparkSession started successfully.")
    except Exception as e:
        logger.error(f"SparkSession could not be started: {e}")
        spark = None

    if spark is not None:
        try:
            model = ALSModel.load(MODEL_PATH)
            logger.info(f"ALS model successfully loaded from {MODEL_PATH}")
        except Exception as e:
            logger.error(f"ALS model could not be loaded: {e}")
            model = None

    try:
        movies_df = pd.read_csv(MOVIES_CSV)
        movies_df["movieId"] = movies_df["movieId"].astype(int)
        logger.info(f"Loaded {len(movies_df):,} movies from {MOVIES_CSV}")
    except Exception as e:
        logger.error(f"movies.csv could not be loaded: {e}")
        movies_df = pd.DataFrame(columns=["movieId", "title", "genres"])

    yield

    if spark:
        spark.stop()


app = FastAPI(title="RecoSpark API", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

class RecommendationRequest(BaseModel):
    userId: int
    topN: int = 10


@app.get("/health")
def health_check():
    return {
        "status": "ok",
        "spark_ready": spark is not None,
        "model_ready": model is not None,
    }


@app.post("/recommendations")
def get_recommendations(request: RecommendationRequest):
    if model is None or spark is None:
        raise HTTPException(status_code=503, detail="Model is not available.")

    try:
        # ── PURE JVM HACK: Python RDD Yaratmayı Tamamen Engelliyoruz ──
        # Dataframe'i createDataFrame ile değil, SQL ile doğrudan JVM'de oluşturuyoruz.
        # Böylece Python Worker zafiyeti oluşmuyor.
        user_id_safe = int(request.userId)
        user_df = spark.sql(f"SELECT CAST({user_id_safe} AS INT) AS userId")
        
        # İşlemler tamamen JVM (Java/Scala) üzerinde koşuyor
        raw_recs = model.recommendForUserSubset(user_df, request.topN)

        flat_recs_df = raw_recs.select(
            explode("recommendations").alias("rec")
        ).select(
            col("rec.movieId").alias("movieId"),
            col("rec.rating").alias("rating")
        )

        # JVM'den veriyi JSON metinleri olarak çekiyoruz (Worker'sız veri transferi)
        json_recs = flat_recs_df.toJSON().collect()

        if not json_recs:
            raise HTTPException(status_code=404, detail=f"No recommendations found for user {request.userId}.")

        recs_list = [json.loads(row_str) for row_str in json_recs]

    except Exception as e:
        logger.error(f"Spark job failed: {e}")
        raise HTTPException(status_code=500, detail=f"Error generating recommendations: {str(e)}")

    results = []
    for row in recs_list:
        movie_id         = int(row["movieId"])
        predicted_rating = round(float(row["rating"]), 2)

        movie_meta = movies_df[movies_df["movieId"] == movie_id]
        title  = str(movie_meta.iloc[0]["title"])  if not movie_meta.empty else "Unknown"
        genres = str(movie_meta.iloc[0]["genres"]) if not movie_meta.empty else "Unknown"

        results.append({
            "movieId":        movie_id,
            "title":          title,
            "genres":         genres,
            "predictedRating": predicted_rating,
        })

    return {"userId": request.userId, "recommendations": results}