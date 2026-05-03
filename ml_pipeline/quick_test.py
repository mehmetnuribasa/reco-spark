"""
Hızlı doğrulama scripti: Veri yükleme ve EDA'yı test et.
Tam pipeline'ı çalıştırmadan önce her şeyin düzgün çalıştığını doğrular.
"""
import os
import sys
from pathlib import Path

# train.py'deki fonksiyonları import et
sys.path.insert(0, str(Path(__file__).resolve().parent))
from train import (
    create_spark_session,
    load_and_explore,
    clean_data,
    split_data,
    RATINGS_PATH,
    MOVIES_PATH,
)


def main():
    print("🔍 Hızlı doğrulama başlatılıyor...\n")

    # Dosya kontrolleri
    for path, name in [(RATINGS_PATH, "ratings.csv"), (MOVIES_PATH, "movies.csv")]:
        if os.path.exists(path):
            size_mb = os.path.getsize(path) / (1024 * 1024)
            print(f"  ✅ {name} mevcut ({size_mb:.1f} MB)")
        else:
            print(f"  ❌ {name} bulunamadı: {path}")
            sys.exit(1)

    spark = create_spark_session()

    try:
        # EDA
        ratings, movies = load_and_explore(spark)

        # Temizleme
        ratings_clean = clean_data(ratings)

        # Split
        train, test = split_data(ratings_clean)

        # Küçük bir ALS testi (tek parametre seti)
        print("\n" + "=" * 60)
        print("  HIZLI ALS TESTİ (rank=10, regParam=0.1, maxIter=5)")
        print("=" * 60)

        from pyspark.ml.recommendation import ALS
        from pyspark.ml.evaluation import RegressionEvaluator

        als = ALS(
            rank=10,
            maxIter=5,
            regParam=0.1,
            userCol="userId",
            itemCol="movieId",
            ratingCol="rating",
            nonnegative=True,
            coldStartStrategy="drop",
        )

        model = als.fit(train)
        predictions = model.transform(test)

        evaluator = RegressionEvaluator(
            metricName="rmse",
            labelCol="rating",
            predictionCol="prediction",
        )
        rmse = evaluator.evaluate(predictions)

        print(f"\n  📈 Hızlı Test RMSE: {rmse:.4f}")
        print(f"  {'✅ RMSE < 1.0 ✓' if rmse < 1.0 else '⚠️ RMSE >= 1.0'}")

        # Örnek öneriler
        print("\n  📊 Kullanıcı 1 için Top-5 Öneri:")
        user_recs = model.recommendForAllUsers(5)
        user1_recs = user_recs.filter(user_recs.userId == 1).collect()
        if user1_recs:
            for rec in user1_recs[0].recommendations:
                # movies tablosundan film adını bul
                movie_row = movies.filter(movies.movieId == rec.movieId).collect()
                title = movie_row[0].title if movie_row else "Bilinmeyen"
                print(f"    🎬 {title} (movieId={rec.movieId}, score={rec.rating:.2f})")

        print("\n✅ Doğrulama tamamlandı! Tam pipeline çalıştırılabilir.")

    finally:
        spark.stop()
        print("\n🔌 Spark oturumu kapatıldı.")


if __name__ == "__main__":
    main()
