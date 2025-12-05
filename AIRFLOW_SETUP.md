# Airflow Setup Guide

## Overview

Apache Airflow has been configured to orchestrate the data pipelines in this project. The setup includes three main DAGs:

1. **Gutenberg Ingestion Pipeline** - Downloads and processes classic literature
2. **Wikipedia Streaming Monitor** - Monitors the real-time streaming pipeline
3. **NLP Normalization Pipeline** - Trains and applies spelling normalization

## Architecture

```
┌─────────────────────────────────────────────────────────┐
│                   Airflow Components                     │
├─────────────────────────────────────────────────────────┤
│                                                           │
│  ┌──────────────┐  ┌──────────────┐  ┌───────────────┐ │
│  │   Webserver  │  │   Scheduler  │  │   PostgreSQL  │ │
│  │   :8080      │  │              │  │   (Metadata)  │ │
│  └──────────────┘  └──────────────┘  └───────────────┘ │
│                                                           │
└─────────────────────────────────────────────────────────┘
                          │
                          ▼
        ┌──────────────────────────────────────┐
        │           DAG Directory               │
        ├──────────────────────────────────────┤
        │  • gutenberg_ingestion_dag.py        │
        │  • wikipedia_streaming_dag.py        │
        │  • nlp_normalization_dag.py          │
        └──────────────────────────────────────┘
```

## Quick Start

### 1. Start Airflow Services

```bash
# Start all services including Airflow
make docker-up

# Or start only Airflow services
make airflow-up
```

### 2. Access Airflow Web UI

Open your browser and navigate to:
```
http://localhost:8080
```

**Login credentials:**
- Username: `admin`
- Password: `admin`

### 3. Enable DAGs

Once logged in:
1. Navigate to the DAGs page
2. Toggle the DAG switches to enable them:
   - `gutenberg_ingestion_pipeline`
   - `wikipedia_streaming_monitor`
   - `nlp_normalization_pipeline`

### 4. Trigger DAGs Manually

You can trigger DAGs manually from the UI:
1. Click on the DAG name
2. Click the "Play" button (▶️) in the top right
3. Select "Trigger DAG"

## DAG Details

### 1. Gutenberg Ingestion Pipeline

**DAG ID:** `gutenberg_ingestion_pipeline`

**Schedule:** Weekly on Sundays at 2 AM UTC

**Tasks:**
1. `download_gutenberg_books` - Downloads 600+ books from Project Gutenberg
2. `extract_metadata` - Extracts metadata using AWS Bedrock
3. `clean_metadata` - Cleans and deduplicates metadata
4. `verify_completion` - Verification step

**Execution Time:** ~3-4 hours

**Trigger manually:**
```bash
# From Airflow shell
make airflow-shell
airflow dags trigger gutenberg_ingestion_pipeline
```

### 2. Wikipedia Streaming Monitor

**DAG ID:** `wikipedia_streaming_monitor`

**Schedule:** Hourly

**Tasks:**
1. `check_kafka_health` - Verifies Kafka is running
2. `check_postgres_health` - Verifies PostgreSQL connection
3. `collect_streaming_metrics` - Gathers pipeline metrics
4. `check_data_staleness` - Alerts if data is stale
5. `generate_summary_report` - Creates summary report

**Execution Time:** ~2-5 minutes

**Purpose:** Monitors the health of the streaming pipeline without actually running the producer/consumer (those run as separate long-running services).

### 3. NLP Normalization Pipeline

**DAG ID:** `nlp_normalization_pipeline`

**Schedule:** Weekly on Saturdays at 3 AM UTC

**Tasks:**
1. `train_normalizer` - Trains the Bayesian spelling normalizer
2. `evaluate_normalizer` - Evaluates model accuracy
3. `normalize_sample_texts` - Normalizes sample texts
4. `generate_report` - Creates completion report

**Execution Time:** ~30-45 minutes

## Makefile Commands

```bash
# Start/Stop Airflow
make airflow-up              # Start Airflow services
make airflow-down            # Stop Airflow services
make airflow-restart         # Restart Airflow services

# Monitoring
make airflow-logs            # View Airflow logs

# Debugging
make airflow-shell           # Open shell in Airflow container

# Initialization (first time only)
make airflow-init            # Initialize database and create admin user
```

## Configuration

### Environment Variables

Airflow services have access to these environment variables:

```bash
# Database connection (for data warehouse)
DATABASE_URL=postgresql://books_user:books_password@postgres:5432/books_db

# Kafka connection
KAFKA_BOOTSTRAP_SERVERS=kafka:9092

# AWS configuration
AWS_DEFAULT_REGION=us-east-1
```

### Airflow Configuration

Key Airflow settings (configured via environment variables):

```bash
AIRFLOW__CORE__EXECUTOR=LocalExecutor
AIRFLOW__CORE__SQL_ALCHEMY_CONN=postgresql+psycopg2://airflow:airflow@airflow-postgres/airflow
AIRFLOW__CORE__DAGS_ARE_PAUSED_AT_CREATION=true
AIRFLOW__CORE__LOAD_EXAMPLES=false
```

## Directory Structure

```
nlp_final_project/
├── dags/                           # Airflow DAG definitions
│   ├── gutenberg_ingestion_dag.py
│   ├── wikipedia_streaming_dag.py
│   └── nlp_normalization_dag.py
├── logs/                           # Airflow logs (auto-generated)
├── plugins/                        # Custom Airflow plugins (optional)
├── src/                            # Source code (mounted in containers)
│   ├── ingestion/
│   ├── metadata/
│   ├── streaming/
│   └── *.py
└── docker/
    └── docker-compose.yml          # Docker services configuration
```

## Monitoring and Debugging

### View Task Logs

From the Airflow UI:
1. Click on a DAG
2. Click on a specific task instance
3. Click "Log" button

### View Real-time Logs

```bash
# All Airflow logs
make airflow-logs

# Specific service logs
cd docker && docker-compose logs -f airflow-webserver
cd docker && docker-compose logs -f airflow-scheduler
```

### Access Airflow Shell

```bash
make airflow-shell

# Inside container
airflow dags list
airflow tasks list gutenberg_ingestion_pipeline
airflow dags trigger gutenberg_ingestion_pipeline
```

### Check DAG Status

```bash
# From Airflow shell
airflow dags state gutenberg_ingestion_pipeline <execution_date>
```

## Troubleshooting

### DAGs not appearing in UI

1. Check DAG syntax:
```bash
make airflow-shell
python /opt/airflow/dags/gutenberg_ingestion_dag.py
```

2. Check scheduler logs:
```bash
cd docker && docker-compose logs airflow-scheduler
```

### Tasks failing

1. Check task logs in UI (most detailed)
2. Verify dependencies are installed in the container
3. Check environment variables are set correctly
4. Ensure source code is mounted correctly

### Database connection issues

1. Verify PostgreSQL is running:
```bash
cd docker && docker-compose ps postgres
```

2. Check connection string in docker-compose.yml
3. Restart services:
```bash
make airflow-restart
```

### Kafka connection issues

1. Verify Kafka is healthy:
```bash
cd docker && docker-compose ps kafka
```

2. Check topic exists:
```bash
cd docker && docker-compose exec kafka kafka-topics --list --bootstrap-server localhost:9092
```

## Best Practices

1. **Test DAGs before deployment:**
   ```bash
   make airflow-shell
   airflow dags test gutenberg_ingestion_pipeline 2024-12-01
   ```

2. **Monitor resource usage:**
   - Airflow webserver: ~200MB RAM
   - Airflow scheduler: ~150MB RAM
   - Tasks: Varies by workload (download task: ~1GB)

3. **Adjust schedules based on needs:**
   - Edit schedule_interval in DAG files
   - Restart scheduler after changes

4. **Use XCom for task communication:**
   - See `wikipedia_streaming_dag.py` for examples
   - Push/pull data between tasks

## Production Considerations

For production deployments:

1. **Use CeleryExecutor** for distributed task execution
2. **Set up email alerts** (configure SMTP settings)
3. **Use secrets backend** (AWS Secrets Manager, Vault)
4. **Enable authentication** (OAuth, LDAP)
5. **Configure logging** to external storage (S3, CloudWatch)
6. **Set up monitoring** (Prometheus, Grafana)
7. **Use connection pooling** for database connections

## Additional Resources

- [Apache Airflow Documentation](https://airflow.apache.org/docs/)
- [Airflow Best Practices](https://airflow.apache.org/docs/apache-airflow/stable/best-practices.html)
- [DAG Writing Best Practices](https://airflow.apache.org/docs/apache-airflow/stable/best-practices.html#writing-a-dag)

## Support

For issues or questions:
1. Check the [troubleshooting section](#troubleshooting)
2. Review Airflow logs: `make airflow-logs`
3. Open an issue in the project repository
