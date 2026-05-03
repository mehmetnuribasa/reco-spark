"""
Reco-Spark ALS Model Training Pipeline
=======================================
MovieLens 25M dataset üzerinde PySpark ALS modeli eğitimi.

Adımlar:
  1. Veri Yükleme & Keşif (EDA)
  2. Veri Temizleme
  3. Train / Test Split (%80 / %20)
  4. ALS Model Eğitimi + Hyperparameter Tuning (CrossValidator)
  5. Değerlendirme (RMSE < 1.0 hedefi)
  6. Model Export

Kullanım:
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
    """SparkSession oluştur – 8 GB driver memory."""
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
# 1) Veri Yükleme & EDA
# ═══════════════════════════════════════════════════════════════════════
def load_and_explore(spark: SparkSession):
    """ratings.csv ve movies.csv dosyalarını yükle, temel EDA yap."""

    print("\n" + "=" * 60)
    print("  ADIM 1 – Veri Yükleme & Keşif (EDA)")
    print("=" * 60)

    # ── Schema tanımla (performans için) ──
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

    # ── Yükleme ──
    print(f"\n📂 Ratings yükleniyor: {RATINGS_PATH}")
    ratings = (
        spark.read
        .option("header", "true")
        .schema(ratings_schema)
        .csv(RATINGS_PATH)
    )

    print(f"📂 Movies yükleniyor: {MOVIES_PATH}")
    movies = (
        spark.read
        .option("header", "true")
        .schema(movies_schema)
        .csv(MOVIES_PATH)
    )

    # ── Cache (birden fazla kez kullanılacak) ──
    ratings.cache()
    movies.cache()

    # ── Şema ──
    print("\n📋 Ratings Schema:")
    ratings.printSchema()
    print("📋 Movies Schema:")
    movies.printSchema()

    # ── Boyut ──
    rating_count = ratings.count()
    movie_count = movies.count()
    user_count = ratings.select("userId").distinct().count()
    unique_movies = ratings.select("movieId").distinct().count()

    print(f"\n📊 Toplam rating sayısı     : {rating_count:,}")
    print(f"📊 Benzersiz kullanıcı sayısı: {user_count:,}")
    print(f"📊 Benzersiz film sayısı     : {unique_movies:,}")
    print(f"📊 Movies tablosu satır sayısı: {movie_count:,}")

    # ── Rating dağılımı ──
    print("\n📊 Rating Dağılımı:")
    ratings.groupBy("rating").count().orderBy("rating").show()

    # ── İstatistikler ──
    print("📊 Rating İstatistikleri:")
    ratings.select("rating").describe().show()

    # ── İlk birkaç satır ──
    print("📊 Örnek Ratings:")
    ratings.show(5, truncate=False)

    print("📊 Örnek Movies:")
    movies.show(5, truncate=False)

    return ratings, movies


# ═══════════════════════════════════════════════════════════════════════
# 2) Veri Temizleme
# ═══════════════════════════════════════════════════════════════════════
def clean_data(ratings):
    """Eksik değerleri sil, timestamp sütununu kaldır."""

    print("\n" + "=" * 60)
    print("  ADIM 2 – Veri Temizleme")
    print("=" * 60)

    before = ratings.count()
    ratings_clean = ratings.dropna(subset=["userId", "movieId", "rating"])
    after = ratings_clean.count()

    print(f"  Temizleme öncesi: {before:,} satır")
    print(f"  Temizleme sonrası: {after:,} satır")
    print(f"  Silinen satır:    {before - after:,}")

    # timestamp ALS için gerekli değil – kaldır
    ratings_clean = ratings_clean.select("userId", "movieId", "rating")

    return ratings_clean


# ═══════════════════════════════════════════════════════════════════════
# 3) Train / Test Split
# ═══════════════════════════════════════════════════════════════════════
def split_data(ratings_clean):
    """Veriyi %80 train, %20 test olarak ayır."""

    print("\n" + "=" * 60)
    print("  ADIM 3 – Train / Test Split (%80 / %20)")
    print("=" * 60)

    train, test = ratings_clean.randomSplit([0.8, 0.2], seed=42)
    train.cache()
    test.cache()

    train_count = train.count()
    test_count = test.count()

    print(f"  Train set: {train_count:,} satır")
    print(f"  Test set:  {test_count:,} satır")
    print(f"  Oran:      {train_count / (train_count + test_count) * 100:.1f}% / {test_count / (train_count + test_count) * 100:.1f}%")

    return train, test


# ═══════════════════════════════════════════════════════════════════════
# 4) ALS Model Eğitimi + Hyperparameter Tuning
# ═══════════════════════════════════════════════════════════════════════
def train_als_with_tuning(train, test):
    """ALS modeli eğit ve CrossValidator ile hyperparameter tuning yap."""

    print("\n" + "=" * 60)
    print("  ADIM 4 – ALS Model Eğitimi + Hyperparameter Tuning")
    print("=" * 60)

    # ── ALS Tanımı ──
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

    print(f"  Grid boyutu: {len(param_grid)} kombinasyon")
    print(f"  3-fold Cross Validation ile toplam: {len(param_grid) * 3} model eğitilecek")

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
        parallelism=2,  # Paralel model eğitimi
        seed=42,
    )

    print("\n⏳ CrossValidator başlatılıyor... (Bu uzun sürebilir)")
    start_time = time.time()

    cv_model = cv.fit(train)

    elapsed = time.time() - start_time
    print(f"✅ CrossValidator tamamlandı! Süre: {elapsed / 60:.1f} dakika")

    return cv_model, evaluator


# ═══════════════════════════════════════════════════════════════════════
# 5) Model Değerlendirme
# ═══════════════════════════════════════════════════════════════════════
def evaluate_model(cv_model, test, evaluator):
    """Test seti üzerinde RMSE hesapla ve en iyi parametreleri raporla."""

    print("\n" + "=" * 60)
    print("  ADIM 5 – Model Değerlendirme")
    print("=" * 60)

    best_model = cv_model.bestModel
    predictions = best_model.transform(test)
    rmse = evaluator.evaluate(predictions)

    print(f"\n  📈 Test RMSE: {rmse:.4f}")
    print(f"  🎯 Hedef:     RMSE < 1.0")
    print(f"  {'✅ HEDEF BAŞARILDI!' if rmse < 1.0 else '❌ HEDEF BAŞARILAMADI – Parametreleri gözden geçir.'}")

    # ── En iyi parametreler ──
    print(f"\n  En İyi Parametreler:")
    print(f"    rank     = {best_model.rank}")
    print(f"    maxIter  = {best_model._java_obj.parent().getMaxIter()}")
    print(f"    regParam = {best_model._java_obj.parent().getRegParam()}")

    # ── Cross Validation sonuçları ──
    avg_metrics = cv_model.avgMetrics
    print(f"\n  Cross Validation Ortalamaları (RMSE):")
    for i, metric in enumerate(avg_metrics):
        print(f"    Kombinasyon {i + 1:2d}: RMSE = {metric:.4f}")

    best_idx = avg_metrics.index(min(avg_metrics))
    print(f"\n  En iyi kombinasyon: #{best_idx + 1} (RMSE = {min(avg_metrics):.4f})")

    return best_model, rmse


# ═══════════════════════════════════════════════════════════════════════
# 6) Model Export
# ═══════════════════════════════════════════════════════════════════════
def save_model(best_model, rmse):
    """Modeli diske kaydet."""

    print("\n" + "=" * 60)
    print("  ADIM 6 – Model Export")
    print("=" * 60)

    # Önceki model varsa temizle
    if os.path.exists(MODEL_SAVE_DIR):
        import shutil
        shutil.rmtree(MODEL_SAVE_DIR)
        print(f"  ⚠️  Eski model silindi: {MODEL_SAVE_DIR}")

    best_model.write().overwrite().save(MODEL_SAVE_DIR)
    print(f"  💾 Model kaydedildi: {MODEL_SAVE_DIR}")
    print(f"  📏 Final RMSE: {rmse:.4f}")

    # Metadata dosyası oluştur
    metadata_path = os.path.join(os.path.dirname(MODEL_SAVE_DIR), "model_metadata.txt")
    with open(metadata_path, "w", encoding="utf-8") as f:
        f.write(f"Model: ALS (PySpark)\n")
        f.write(f"Dataset: MovieLens 25M\n")
        f.write(f"RMSE: {rmse:.4f}\n")
        f.write(f"Rank: {best_model.rank}\n")
        f.write(f"Trained at: {time.strftime('%Y-%m-%d %H:%M:%S')}\n")
    print(f"  📝 Metadata kaydedildi: {metadata_path}")


# ═══════════════════════════════════════════════════════════════════════
# Main
# ═══════════════════════════════════════════════════════════════════════
def main():
    print("🚀 Reco-Spark ALS Training Pipeline başlatılıyor...\n")

    # Dosya kontrolleri
    if not os.path.exists(RATINGS_PATH):
        print(f"❌ ratings.csv bulunamadı: {RATINGS_PATH}")
        sys.exit(1)
    if not os.path.exists(MOVIES_PATH):
        print(f"❌ movies.csv bulunamadı: {MOVIES_PATH}")
        sys.exit(1)

    spark = create_spark_session()

    try:
        # 1) Veri Yükleme & EDA
        ratings, movies = load_and_explore(spark)

        # 2) Veri Temizleme
        ratings_clean = clean_data(ratings)

        # 3) Train/Test Split
        train, test = split_data(ratings_clean)

        # 4) ALS + Hyperparameter Tuning
        cv_model, evaluator = train_als_with_tuning(train, test)

        # 5) Değerlendirme
        best_model, rmse = evaluate_model(cv_model, test, evaluator)

        # 6) Model Export
        save_model(best_model, rmse)

        print("\n" + "=" * 60)
        print("  🎉 Pipeline tamamlandı!")
        print("=" * 60)

    finally:
        spark.stop()
        print("\n🔌 Spark oturumu kapatıldı.")


if __name__ == "__main__":
    main()
