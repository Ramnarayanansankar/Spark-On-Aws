# Serverless Spark ETL Pipeline on AWS

## 🎯 Project Overview

### Problem Statement
In traditional data processing workflows, raw data lands in storage and waits for manual intervention by data engineers to clean, transform, and analyze it. This manual process is time-consuming, error-prone, and does not scale efficiently.

### Solution
This project demonstrates a **fully automated, event-driven serverless data pipeline** on AWS that eliminates manual intervention. When raw product review data arrives, the entire ETL (Extract, Transform, Load) process happens automatically.

### Business Value
- **Zero Manual Intervention:** Upload data and get analytics automatically
- **Cost-Effective:** Pay only for what you use (serverless architecture)
- **Scalable:** Handles growing data volumes without infrastructure changes
- **Fast Time-to-Insight:** Analytics available within minutes of data arrival

### Workflow
1. Raw `reviews.csv` file is uploaded to S3 landing bucket
2. S3 event automatically triggers AWS Lambda function
3. Lambda function starts AWS Glue ETL job
4. Glue job (PySpark script) performs:
   - Data cleaning and validation
   - Multiple Spark SQL analytical queries
   - Data aggregation and transformation
5. Processed results saved as Parquet files in S3 processed bucket

## 🏗️ Architecture

**Data Flow:**
`S3 (Upload) -> Lambda (Trigger) -> AWS Glue (Spark Job) -> S3 (Processed Results)`

**Key Components:**
- **S3 Landing Bucket:** Receives raw CSV files
- **Lambda Function:** Event-driven trigger
- **AWS Glue:** Managed Spark ETL processing
- **S3 Processed Bucket:** Stores analytical results
- **IAM Roles:** Security and permissions

## 🛠️ Technology Stack

* **Data Lake:** Amazon S3
* **ETL (Spark):** AWS Glue
* **Serverless Compute:** AWS Lambda
* **Data Scripting:** PySpark (Python + Spark SQL)
* **Security:** AWS IAM (Identity and Access Management)

---

## 🔧 Setup and Deployment

### Prerequisites
- AWS Account (Free Tier sufficient)
- AWS CLI configured (optional but recommended)
- Basic understanding of:
  - Amazon S3
  - AWS Lambda
  - AWS Glue
  - Apache Spark/PySpark
  - IAM roles and policies

### Step 1: Create S3 Buckets

Create two S3 buckets with **globally unique names**:

1. **Landing Bucket:** `phanindra-hands-on-final-landing`
   - Purpose: Receives raw CSV files

2. **Processed Bucket:** `phanindra-hands-on-final-processed`
   - Purpose: Stores processed Parquet results

### Step 2: Create IAM Role for AWS Glue

AWS Glue needs permissions to read from and write to S3.

**Steps:**
1. Navigate to **IAM Console** → **Roles** → **Create role**
2. **Trusted entity type:** AWS service
3. **Use case:** Glue
4. **Attach policies:**
   - `AWSGlueServiceRole` (AWS managed policy)
   - `AmazonS3FullAccess` (for demo)
5. **Role name:** `AWSGlueServiceRole-Reviews`
6. Create the role

### Step 3: Create AWS Glue ETL Job

**Steps:**
1. Navigate to **AWS Glue Console** → **ETL jobs** → **Script editor**
2. Select **Spark script editor**
3. Paste the contents from `GlueETLScript.py`
4. **Important:** Update bucket names in the script if you used custom names
5. Navigate to **Job details** tab:
   - **Name:** `process_reviews_job`
   - **IAM Role:** `AWSGlueServiceRole-Reviews`
   - **Type:** Spark
   - **Glue version:** 4.0 (or latest)
   - **Language:** Python 3
   - **Worker type:** G.1X (or G.2X for faster processing)
   - **Number of workers:** 2 (minimum)
6. **Save** the job

### Step 4: Create Lambda Trigger Function

**Steps:**
1. Navigate to **Lambda Console** → **Create function**
2. **Function name:** `start_glue_job_trigger`
3. **Runtime:** Python 3.10 (or later)
4. **Execution role:** Create a new role with basic Lambda permissions
5. Create the function

#### 4a. Add Lambda Code
1. In the code editor, paste contents from `LambdaFunction.py`
2. **Important:** Verify `GLUE_JOB_NAME = 'process_reviews_job'` matches your Glue job name
3. Deploy the changes

#### 4b. Configure Lambda Permissions
1. Go to **Configuration** → **Permissions**
2. Click on the execution role name
3. In IAM, click **Add permissions** → **Create inline policy**
4. Use JSON editor:
   ```json
   {
     "Version": "2012-10-17",
     "Statement": [
       {
         "Effect": "Allow",
         "Action": "glue:StartJobRun",
         "Resource": "*"
       }
     ]
   }
   ```
5. Name: `Allow-Glue-StartJobRun`
6. Create policy

#### 4c. Add S3 Trigger
1. In Lambda function, click **Add trigger**
2. **Source:** S3
3. **Bucket:** Select your landing bucket
4. **Event type:** All object create events (`s3:ObjectCreated:*`)
5. Acknowledge the recursive invocation warning
6. **Add trigger**

## 🚀 How to Run the Pipeline

Your pipeline is now fully deployed and automated!

1.  Take the sample `reviews.csv` file from the `InputFiles/` directory.
2.  Upload `reviews.csv` to the root of your `phanindra-hands-on-final-landing` S3 bucket.
3.  This will trigger the Lambda, which in turn starts the Glue job.
4.  You can monitor the job's progress in the **AWS Glue** console under the **Monitoring** tab.

## Repository Structure:
```
Spark-on-AWS/
├── InputFiles/
│   └── reviews.csv
├── OutputCSVFiles/
│   ├── AverageRating
│   ├── DailyReviewTrends
│   ├── RatingDistribution
│   └── TopActiveCustomers
├── OutputScreenshots/
├── GlueETLScript.py
├── LambdaFunction.py
└── README.md
```

## 📊 Results and Screenshots

### Screenshot 1: Lambda Function Triggered
<img width="780" height="620" alt="AWSLambdaOutputLogs" src="https://github.com/user-attachments/assets/9c873b93-6795-408d-9375-96cad80c95db" />

### Screenshot 2: Glue Job Script
<img width="780" height="620" alt="AWSGlueScript" src="https://github.com/user-attachments/assets/fbb557f2-96fa-4587-b511-a9ee3ea4a2ff" />

### Screenshot 3: Glue Job Completed Successfully
<img width="780" height="620" alt="AWSGlueRun" src="https://github.com/user-attachments/assets/9ffb6976-52b2-49bd-95ed-061237303888" />

### Screenshot 4: Cloud Watch Logs
<img width="780" height="620" alt="AWSCloudWatch" src="https://github.com/user-attachments/assets/c90b5fd5-c3a1-4358-b871-637ff0a6c2f6" />

### Screenshot 5: Output Parquet Files in S3
<img width="780" height="620" alt="S3OutputFolderPitcure2" src="https://github.com/user-attachments/assets/648c23ab-4bb2-459f-8677-98d39215b0b3" />

## 🎓 Approach and Methodology

### Design Decisions

1. **Serverless Architecture:**
   - Chose Lambda for cost-effectiveness and auto-scaling
   - No server management required

2. **Parquet Format:**
   - Columnar storage for efficient analytics
   - Better compression than CSV
   - Faster query performance

3. **Event-Driven Design:**
   - Immediate processing upon data arrival
   - No scheduled jobs or manual triggers

4. **Separation of Concerns:**
   - Landing bucket for raw data
   - Processed bucket for analytics
   - Clear data lineage

## 📝 Conclusion

### Key Takeaways

1. **Automation:** Serverless architectures eliminate manual data processing
2. **Scalability:** Components scale automatically with data volume
3. **Cost-Efficiency:** Pay-per-use model reduces operational costs
4. **Event-Driven:** Real-time processing as data arrives
