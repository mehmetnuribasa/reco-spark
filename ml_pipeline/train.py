from pyspark.sql import SparkSession

def main():
    spark = SparkSession.builder \
        .appName("Reco-Spark-Training") \
        .getOrCreate()
    
    print("Spark session started. Data reading and ALS model training logic will be written here.")
    spark.stop()

if __name__ == "__main__":
    main()
