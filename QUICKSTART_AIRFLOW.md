# Airflow Quick Start

## 1. Start Airflow (First Time)

```bash
# Start all services including Airflow
make docker-up
```

Wait 30-60 seconds for Airflow to initialize.

## 2. Access Airflow UI

Open in browser: **http://localhost:8080**

**Login:**
- Username: `admin`
- Password: `admin`

## 3. Available DAGs

You'll see 3 DAGs in the UI:

### 📚 gutenberg_ingestion_pipeline
**What it does:** Downloads books from Project Gutenberg, extracts metadata, and cleans data

**Schedule:** Weekly (Sundays at 2 AM UTC)

**How to run:** Click the DAG → Click ▶️ (Play button) → "Trigger DAG"

---

### 📊 wikipedia_streaming_monitor
**What it does:** Monitors your Kafka streaming pipeline health

**Schedule:** Hourly

**How to run:** Automatically runs every hour, or trigger manually

---

### 📝 nlp_normalization_pipeline
**What it does:** Trains and applies spelling normalization on Shakespeare texts

**Schedule:** Weekly (Saturdays at 3 AM UTC)

**How to run:** Click the DAG → Click ▶️ (Play button) → "Trigger DAG"

## 4. Enable DAGs

By default, DAGs are paused. To enable them:

1. Find the toggle switch next to each DAG name
2. Click to turn it ON (blue)
3. The DAG will now run on its schedule

## 5. Common Commands

```bash
# Start Airflow
make airflow-up

# Stop Airflow
make airflow-down

# View logs
make airflow-logs

# Restart Airflow
make airflow-restart

# Access Airflow shell
make airflow-shell
```

## 6. Monitor Task Execution

1. Click on a DAG name
2. View the graph or tree view
3. Click on a task to see logs and status
4. Green = Success, Red = Failed, Yellow = Running

## 7. Troubleshooting

**DAGs not showing up?**
```bash
make airflow-restart
```

**Tasks failing?**
- Click the failed task → "Log" button to see error details

**Need help?**
- See [AIRFLOW_SETUP.md](AIRFLOW_SETUP.md) for detailed documentation

## 8. Next Steps

Once Airflow is running:

1. **Enable the monitoring DAG** to track your streaming pipeline
2. **Trigger the ingestion DAG** if you need fresh data from Gutenberg
3. **Check the Graph View** to understand task dependencies
4. **Explore the logs** to see what each task is doing

That's it! Your Airflow setup is ready to orchestrate your data pipelines. 🚀
