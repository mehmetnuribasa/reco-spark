"""
Reco-Spark ALS Model Training Pipeline
=======================================
PySpark ALS model training on the MovieLens 25M dataset.

Steps:
  1. Data Loading & Exploratory Data Analysis (EDA)
  2. Data Cleaning
  3. Train / Test Split (80% / 20%)
  4. ALS Model Training + Hyperparameter Tuning (CrossValidator)
  5. Evaluation (Target: RMSE < 1.0)
  6. Model Export

Usage:
  .venv/Scripts/python.exe ml_pipeline/train.py
"""

import os
import sys
import time
from pathlib import Path

from pyspark.sql import SparkSession
from pyspark.sql import functions as F
from pyspark.sql.types import StructType, StructField, IntegerType, FloatType, LongType, StringType
from pyspark.ml.recommendation import ALS
from pyspark.ml.evaluation import RegressionEvaluator
from pyspark.ml.tuning import ParamGridBuilder, CrossValidator


# ── Paths ──────────────────────────────────────────────────────────────
PROJECT_ROOT = Path(__file__).resolve().parent.parent
DATA_DIR = PROJECT_ROOT / "data" / "ml-25m"
RATINGS_PATH = str(DATA_DIR / "ratings.csv")
MOVIES_PATH = str(DATA_DIR / "movies.csv")
MODEL_SAVE_DIR = str(PROJECT_ROOT / "ml_pipeline" / "models" / "als_model")


def create_spark_session() -> SparkSession:
    """Create SparkSession with 8 GB driver memory."""
    spark = (
        SparkSession.builder
        .appName("Reco-Spark-ALS-Training")
        .master("local[*]")
        .config("spark.driver.memory", "8g")
        .config("spark.sql.shuffle.partitions", "200")
        .config("spark.serializer", "org.apache.spark.serializer.KryoSerializer")
        .getOrCreate()
    )
    spark.sparkContext.setLogLevel("WARN")
    return spark


# ═══════════════════════════════════════════════════════════════════════
# 1) Data Loading & EDA
# ═══════════════════════════════════════════════════════════════════════
def load_and_explore(spark: SparkSession):
    """Load ratings.csv and movies.csv, perform basic EDA."""

    print("\n" + "=" * 60)
    print("  STEP 1 – Data Loading & EDA")
    print("=" * 60)

    # ── Define Schema (for performance) ──
    ratings_schema = StructType([
        StructField("userId", IntegerType(), False),
        StructField("movieId", IntegerType(), False),
        StructField("rating", FloatType(), False),
        StructField("timestamp", LongType(), True),
    ])

    movies_schema = StructType([
        StructField("movieId", IntegerType(), False),
        StructField("title", StringType(), False),
        StructField("genres", StringType(), True),
    ])

    # ── Loading ──
    print(f"\n📂 Loading Ratings: {RATINGS_PATH}")
    ratings = (
        spark.read
        .option("header", "true")
        .schema(ratings_schema)
        .csv(RATINGS_PATH)
    )

    print(f"📂 Loading Movies: {MOVIES_PATH}")
    movies = (
        spark.read
        .option("header", "true")
        .schema(movies_schema)
        .csv(MOVIES_PATH)
    )

    # ── Cache (since they will be used multiple times) ──
    ratings.cache()
    movies.cache()

    # ── Schema ──
    print("\n📋 Ratings Schema:")
    ratings.printSchema()
    print("📋 Movies Schema:")
    movies.printSchema()

    # ── Size ──
    rating_count = ratings.count()
    movie_count = movies.count()
    user_count = ratings.select("userId").distinct().count()
    unique_movies = ratings.select("movieId").distinct().count()

    print(f"\n📊 Total ratings        : {rating_count:,}")
    print(f"📊 Unique users         : {user_count:,}")
    print(f"📊 Unique movies        : {unique_movies:,}")
    print(f"📊 Total movie rows     : {movie_count:,}")

    # ── Rating Distribution ──
    print("\n📊 Rating Distribution:")
    ratings.groupBy("rating").count().orderBy("rating").show()

    # ── Statistics ──
    print("📊 Rating Statistics:")
    ratings.select("rating").describe().show()

    # ── First few rows ──
    print("📊 Sample Ratings:")
    ratings.show(5, truncate=False)

    print("📊 Sample Movies:")
    movies.show(5, truncate=False)

    return ratings, movies


# ═══════════════════════════════════════════════════════════════════════
# 2) Data Cleaning
# ═══════════════════════════════════════════════════════════════════════
def clean_data(ratings):
    """Drop missing values and remove the timestamp column."""

    print("\n" + "=" * 60)
    print("  STEP 2 – Data Cleaning")
    print("=" * 60)

    before = ratings.count()
    ratings_clean = ratings.dropna(subset=["userId", "movieId", "rating"])
    after = ratings_clean.count()

    print(f"  Rows before cleaning: {before:,}")
    print(f"  Rows after cleaning:  {after:,}")
    print(f"  Rows dropped:         {before - after:,}")

    # timestamp is not needed for ALS – drop it
    ratings_clean = ratings_clean.select("userId", "movieId", "rating")

    return ratings_clean


# ═══════════════════════════════════════════════════════════════════════
# 3) Train / Test Split
# ═══════════════════════════════════════════════════════════════════════
def split_data(ratings_clean):
    """Split data into 80% train and 20% test."""

    print("\n" + "=" * 60)
    print("  STEP 3 – Train / Test Split (80% / 20%)")
    print("=" * 60)

    train, test = ratings_clean.randomSplit([0.8, 0.2], seed=42)
    train.cache()
    test.cache()

    train_count = train.count()
    test_count = test.count()

    print(f"  Train set: {train_count:,} rows")
    print(f"  Test set:  {test_count:,} rows")
    print(f"  Ratio:     {train_count / (train_count + test_count) * 100:.1f}% / {test_count / (train_count + test_count) * 100:.1f}%")

    return train, test


# ═══════════════════════════════════════════════════════════════════════
# 4) ALS Model Training + Hyperparameter Tuning
# ═══════════════════════════════════════════════════════════════════════
def train_als_with_tuning(train, test):
    """Train ALS model and perform hyperparameter tuning with CrossValidator."""

    print("\n" + "=" * 60)
    print("  STEP 4 – ALS Model Training + Hyperparameter Tuning")
    print("=" * 60)

    # ── ALS Definition ──
    als = ALS(
        userCol="userId",
        itemCol="movieId",
        ratingCol="rating",
        nonnegative=True,
        coldStartStrategy="drop",
    )

    # ── Hyperparameter Grid ──
    param_grid = (
        ParamGridBuilder()
        .addGrid(als.rank, [10, 50, 100])
        .addGrid(als.regParam, [0.01, 0.1, 1.0])
        .addGrid(als.maxIter, [5, 10, 20])
        .build()
    )

    print(f"  Grid size: {len(param_grid)} combinations")
    print(f"  Total models to train (3-fold CV): {len(param_grid) * 3}")

    # ── Evaluator ──
    evaluator = RegressionEvaluator(
        metricName="rmse",
        labelCol="rating",
        predictionCol="prediction",
    )

    # ── CrossValidator ──
    cv = CrossValidator(
        estimator=als,
        estimatorParamMaps=param_grid,
        evaluator=evaluator,
        numFolds=3,
        parallelism=2,  # Parallel model training
        seed=42,
    )

    print("\n⏳ Starting CrossValidator... (This might take a while)")
    start_time = time.time()

    cv_model = cv.fit(train)

    elapsed = time.time() - start_time
    print(f"✅ CrossValidator completed! Elapsed time: {elapsed / 60:.1f} minutes")

    return cv_model, evaluator


# ═══════════════════════════════════════════════════════════════════════
# 5) Model Evaluation
# ═══════════════════════════════════════════════════════════════════════
def evaluate_model(cv_model, test, evaluator):
    """Calculate RMSE on the test set and report best parameters."""

    print("\n" + "=" * 60)
    print("  STEP 5 – Model Evaluation")
    print("=" * 60)

    best_model = cv_model.bestModel
    predictions = best_model.transform(test)
    rmse = evaluator.evaluate(predictions)

    print(f"\n  📈 Test RMSE: {rmse:.4f}")
    print(f"  🎯 Target:    RMSE < 1.0")
    print(f"  {'✅ TARGET ACHIEVED!' if rmse < 1.0 else '❌ TARGET FAILED – Review parameters.'}")

    # ── Best parameters ──
    print(f"\n  Best Parameters:")
    print(f"    rank     = {best_model.rank}")
    print(f"    maxIter  = {best_model._java_obj.parent().getMaxIter()}")
    print(f"    regParam = {best_model._java_obj.parent().getRegParam()}")

    # ── Cross Validation results ──
    avg_metrics = cv_model.avgMetrics
    print(f"\n  Cross Validation Averages (RMSE):")
    for i, metric in enumerate(avg_metrics):
        print(f"    Combination {i + 1:2d}: RMSE = {metric:.4f}")

    best_idx = avg_metrics.index(min(avg_metrics))
    print(f"\n  Best combination: #{best_idx + 1} (RMSE = {min(avg_metrics):.4f})")

    return best_model, rmse


# ═══════════════════════════════════════════════════════════════════════
# 6) Model Export
# ═══════════════════════════════════════════════════════════════════════
def save_model(best_model, rmse):
    """Save the model to disk."""

    print("\n" + "=" * 60)
    print("  STEP 6 – Model Export")
    print("=" * 60)

    # Clear old model if it exists
    if os.path.exists(MODEL_SAVE_DIR):
        import shutil
        shutil.rmtree(MODEL_SAVE_DIR)
        print(f"  ⚠️  Deleted old model: {MODEL_SAVE_DIR}")

    best_model.write().overwrite().save(MODEL_SAVE_DIR)
    print(f"  💾 Model saved to: {MODEL_SAVE_DIR}")
    print(f"  📏 Final RMSE: {rmse:.4f}")

    # Create metadata file
    metadata_path = os.path.join(os.path.dirname(MODEL_SAVE_DIR), "model_metadata.txt")
    with open(metadata_path, "w", encoding="utf-8") as f:
        f.write(f"Model: ALS (PySpark)\n")
        f.write(f"Dataset: MovieLens 25M\n")
        f.write(f"RMSE: {rmse:.4f}\n")
        f.write(f"Rank: {best_model.rank}\n")
        f.write(f"Trained at: {time.strftime('%Y-%m-%d %H:%M:%S')}\n")
    print(f"  📝 Metadata saved to: {metadata_path}")


# ═══════════════════════════════════════════════════════════════════════
# Main
# ═══════════════════════════════════════════════════════════════════════
def main():
    print("🚀 Starting Reco-Spark ALS Training Pipeline...\n")

    # File checks
    if not os.path.exists(RATINGS_PATH):
        print(f"❌ ratings.csv not found: {RATINGS_PATH}")
        sys.exit(1)
    if not os.path.exists(MOVIES_PATH):
        print(f"❌ movies.csv not found: {MOVIES_PATH}")
        sys.exit(1)

    spark = create_spark_session()

    try:
        # 1) Data Loading & EDA
        ratings, movies = load_and_explore(spark)

        # 2) Data Cleaning
        ratings_clean = clean_data(ratings)

        # 3) Train/Test Split
        train, test = split_data(ratings_clean)

        # 4) ALS + Hyperparameter Tuning
        cv_model, evaluator = train_als_with_tuning(train, test)

        # 5) Evaluation
        best_model, rmse = evaluate_model(cv_model, test, evaluator)

        # 6) Model Export
        save_model(best_model, rmse)

        print("\n" + "=" * 60)
        print("  🎉 Pipeline completed successfully!")
        print("=" * 60)

    finally:
        spark.stop()
        print("\n🔌 Spark session closed.")


if __name__ == "__main__":
    main()
