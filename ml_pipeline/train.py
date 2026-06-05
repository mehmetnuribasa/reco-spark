"""
Reco-Spark — ALS Model Training Pipeline
CSE458 Big Data Analytics

Trains an ALS collaborative filtering model on the MovieLens 25M dataset
and saves the model to ml_pipeline/saved_model/als_model.

Run from project root:
    python ml_pipeline/train.py
"""

import time
from pathlib import Path
from pyspark.sql import SparkSession
from pyspark.sql.functions import col
from pyspark.ml.recommendation import ALS
from pyspark.ml.evaluation import RegressionEvaluator
from pyspark.ml.tuning import CrossValidator, ParamGridBuilder

# ── Paths ────────────────────────────────────────────────────────────────────
PROJECT_ROOT = Path(__file__).resolve().parent.parent
RATINGS_CSV  = str(PROJECT_ROOT / "data" / "ratings.csv")
MODEL_OUT    = str(PROJECT_ROOT / "ml_pipeline" / "saved_model" / "als_model")

# ── Config ───────────────────────────────────────────────────────────────────
SAMPLE_FRAC      = 1.0    # 1.0 = full dataset; lower for quick local tests (e.g. 0.01)
TEST_SPLIT       = 0.2
RANDOM_SEED      = 42
RUN_GRID_SEARCH  = False  # Set True to run cross-validation grid search (slow)


def build_spark() -> SparkSession:
    return (
        SparkSession.builder
        .appName("RecoSpark-Training")
        .config("spark.driver.memory", "4g")
        .config("spark.executor.memory", "4g")
        .getOrCreate()
    )


def load_ratings(spark: SparkSession):
    print(f"\n[1/4] Loading ratings from: {RATINGS_CSV}")
    df = (
        spark.read
        .option("header", "true")
        .option("inferSchema", "true")
        .csv(RATINGS_CSV)
        .select(
            col("userId").cast("integer"),
            col("movieId").cast("integer"),
            col("rating").cast("float"),
        )
        .dropna()
    )

    total = df.count()
    print(f"      Loaded {total:,} ratings.")

    if SAMPLE_FRAC < 1.0:
        df = df.sample(fraction=SAMPLE_FRAC, seed=RANDOM_SEED)
        sampled = df.count()
        print(f"      Sampled {sampled:,} ratings ({SAMPLE_FRAC*100:.1f}%).")

    return df


def train_model(train_df):
    """Train ALS with best-practice hyperparameters or grid search."""

    als = ALS(
        maxIter=10,
        rank=50,
        regParam=0.1,
        userCol="userId",
        itemCol="movieId",
        ratingCol="rating",
        coldStartStrategy="drop",   # drops NaN predictions (cold-start users/items)
        nonnegative=True,           # prevents negative rating predictions
        seed=RANDOM_SEED,
    )

    if RUN_GRID_SEARCH:
        print("[3/4] Running cross-validation grid search (this may take a while)...")
        param_grid = (
            ParamGridBuilder()
            .addGrid(als.rank,     [10, 50, 100])
            .addGrid(als.regParam, [0.01, 0.1, 1.0])
            .addGrid(als.maxIter,  [5, 10, 20])
            .build()
        )
        evaluator = RegressionEvaluator(
            metricName="rmse",
            labelCol="rating",
            predictionCol="prediction",
        )
        cv = CrossValidator(
            estimator=als,
            estimatorParamMaps=param_grid,
            evaluator=evaluator,
            numFolds=3,
            seed=RANDOM_SEED,
        )
        cv_model = cv.fit(train_df)
        return cv_model.bestModel
    else:
        print("[3/4] Training ALS model with fixed hyperparameters...")
        return als.fit(train_df)


def evaluate(model, test_df) -> float:
    predictions = model.transform(test_df).dropna(subset=["prediction"])
    evaluator = RegressionEvaluator(
        metricName="rmse",
        labelCol="rating",
        predictionCol="prediction",
    )
    return evaluator.evaluate(predictions)


def main():
    spark = build_spark()
    spark.sparkContext.setLogLevel("WARN")

    # 1. Load data
    ratings_df = load_ratings(spark)

    # 2. Split
    print(f"\n[2/4] Splitting data — train: {1-TEST_SPLIT:.0%} / test: {TEST_SPLIT:.0%}")
    train_df, test_df = ratings_df.randomSplit(
        [1 - TEST_SPLIT, TEST_SPLIT], seed=RANDOM_SEED
    )
    print(f"      Train: {train_df.count():,}  |  Test: {test_df.count():,}")

    # 3. Train
    t0 = time.time()
    model = train_model(train_df)
    elapsed = time.time() - t0
    print(f"      Training completed in {elapsed:.2f} seconds.")

    # 4. Evaluate
    rmse = evaluate(model, test_df)
    print(f"\n[4/4] Evaluation")
    print(f"      RMSE on test set: {rmse:.4f}")
    if rmse <= 1.0:
        print("      ✓ Target achieved (RMSE ≤ 1.0)")
    else:
        print("      ✗ Target not yet achieved — consider tuning or using full dataset.")

    # 5. Save model
    print(f"\n      Saving model to: {MODEL_OUT}")
    model.write().overwrite().save(MODEL_OUT)
    print("      Model saved successfully.\n")

    spark.stop()


if __name__ == "__main__":
    main()