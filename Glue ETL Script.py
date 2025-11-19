import sys
from awsglue.transforms import *
from awsglue.utils import getResolvedOptions
from pyspark.context import SparkContext
from awsglue.context import GlueContext
from awsglue.job import Job
from pyspark.sql.functions import col, to_date, upper, coalesce, lit
from awsglue.dynamicframe import DynamicFrame

## Initialize contexts
sc = SparkContext()
glueContext = GlueContext(sc)
spark = glueContext.spark_session
job = Job(glueContext)

# --- Define S3 Paths (Updated with your new names) ---
s3_input_path = "s3://handsonfinallanding-ramnarayanan/"
s3_processed_path = "s3://handsonfinalprocessed-ramnarayanan/processed-data/"
s3_analytics_path = "s3://handsonfinalprocessed-ramnarayanan/Athena Results/"

# --- Read the data from the S3 landing zone ---
dynamic_frame = glueContext.create_dynamic_frame.from_options(
    connection_type="s3",
    connection_options={"paths": [s3_input_path], "recurse": True},
    format="csv",
    format_options={"withHeader": True, "inferSchema": True},
)

# Convert to a standard Spark DataFrame for easier transformation
df = dynamic_frame.toDF()

# --- Perform Transformations ---
# 1. Cast 'rating' to integer and fill null values with 0
df_transformed = df.withColumn("rating", coalesce(col("rating").cast("integer"), lit(0)))

# 2. Convert 'review_date' string to a proper date type
df_transformed = df_transformed.withColumn("review_date", to_date(col("review_date"), "yyyy-MM-dd"))

# 3. Fill null review_text with a default string
df_transformed = df_transformed.withColumn("review_text",
    coalesce(col("review_text"), lit("No review text")))

# 4. Convert product_id to uppercase for consistency
df_transformed = df_transformed.withColumn("product_id_upper", upper(col("product_id")))


# --- Write the full transformed data to S3 (Good practice) ---
# This saves the clean, complete dataset to the 'processed-data' folder
glue_processed_frame = DynamicFrame.fromDF(df_transformed, glueContext, "transformed_df")
glueContext.write_dynamic_frame.from_options(
    frame=glue_processed_frame,
    connection_type="s3",
    connection_options={"path": s3_processed_path},
    format="csv"
)

# --- Run Spark SQL Query within the Job ---

# 1. Create a temporary view in Spark's memory
df_transformed.createOrReplaceTempView("product_reviews")

# 2. Run your SQL query
df_analytics_result = spark.sql("""
    SELECT 
        product_id_upper, 
        AVG(rating) as average_rating,
        COUNT(*) as review_count
    FROM product_reviews
    GROUP BY product_id_upper
    ORDER BY average_rating DESC
""")

# 3. Write the query's result DataFrame to your 'Athena Results' path
print(f"Writing analytics results to {s3_analytics_path}...")

# repartition(1) writes the result as a single file
analytics_result_frame = DynamicFrame.fromDF(df_analytics_result.repartition(1), glueContext, "analytics_df")
glueContext.write_dynamic_frame.from_options(
    frame=analytics_result_frame,
    connection_type="s3",
    connection_options={"path": s3_analytics_path},
    format="csv"
)

# 2. Date wise review count: his query calculates the total number of reviews submitted per day.
print("Running Query 2: Date-wise Review Count...")
df_analytics_2 = spark.sql("""
    SELECT 
        review_date, 
        COUNT(*) as daily_review_count
    FROM product_reviews
    WHERE review_date IS NOT NULL
    GROUP BY review_date
    ORDER BY review_date ASC
""")

# Write Query 2 result
query2_path = s3_analytics_path + "daily_review_trends/"
print(f"Writing Query 2 results to {query2_path}...")
analytics_result_2_frame = DynamicFrame.fromDF(df_analytics_2.repartition(1), glueContext, "analytics_df_2")
glueContext.write_dynamic_frame.from_options(
    frame=analytics_result_2_frame,
    connection_type="s3",
    connection_options={"path": query2_path},
    format="csv"
)

# 3. Top 5 Most Active Customers: This query identifies your "power users" by finding the customers who have submitted the most reviews.
print("Running Query 3: Top 5 Most Active Customers...")
df_analytics_3 = spark.sql("""
    SELECT 
        customer_id, 
        COUNT(*) as total_reviews_submitted
    FROM product_reviews
    -- Exclude anonymous users from the 'Top Customers' list
    WHERE customer_id != 'ANONYMOUS_USER'
    GROUP BY customer_id
    ORDER BY total_reviews_submitted DESC
    LIMIT 5
""")

# Write Query 3 result
query3_path = s3_analytics_path + "top_active_customers/"
print(f"Writing Query 3 results to {query3_path}...")
analytics_result_3_frame = DynamicFrame.fromDF(df_analytics_3.repartition(1), glueContext, "analytics_df_3")
glueContext.write_dynamic_frame.from_options(
    frame=analytics_result_3_frame,
    connection_type="s3",
    connection_options={"path": query3_path},
    format="csv"
)

# 4. Overall Rating Distribution: This query shows the count for each star rating (1-star, 2-star, etc.)
print("Running Query 4: Overall Rating Distribution...")
df_analytics_4 = spark.sql("""
    SELECT 
        rating, 
        COUNT(*) as rating_count,
        -- Calculate percentage of total reviews (Optional, but useful)
        (COUNT(*) * 100.0 / (SELECT COUNT(*) FROM product_reviews WHERE rating > 0)) as percentage
    FROM product_reviews
    -- Filter out the 0s we used to fill NULLs, as they aren't real ratings
    WHERE rating >= 1 AND rating <= 5
    GROUP BY rating
    ORDER BY rating ASC
""")

# Write Query 4 result
query4_path = s3_analytics_path + "rating_distribution/"
print(f"Writing Query 4 results to {query4_path}...")
analytics_result_4_frame = DynamicFrame.fromDF(df_analytics_4.repartition(1), glueContext, "analytics_df_4")
glueContext.write_dynamic_frame.from_options(
    frame=analytics_result_4_frame,
    connection_type="s3",
    connection_options={"path": query4_path},
    format="csv"
)

job.commit()