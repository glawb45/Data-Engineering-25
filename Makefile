# Install Python dependencies
install:
	python -m pip install --upgrade pip && \
	python -m pip install -r requirements.txt

		
# Clean temporary files
clean:
	rm -rf __pycache__ */__pycache__ *.pyc
	rm -rf logs/*

# Data ingestion tasks
download:
	python src/ingestion/gutenberg_downloader.py

extract-metadata:
	python src/metadata/metadata_extractor.py

clean-metadata:
	python src/metadata/metadata_cleaner.py

# Streaming tasks
start-producer:
	python src/streaming/wiki_producer.py

start-consumer:
	python src/streaming/wiki_consumer.py

# NLP tasks
normalize-shakespeare:
	python src/normalize_spelling.py --input data/FullShakespeare.txt --output data/FullShakespeare.normalized.txt

train-normalizer:
	python src/train_and_test.py --input data/FullShakespeare.txt --split 0.8

# Streamlit dashboard
streamlit:
	streamlit run src/streaming/dashboard.py

# Docker Compose commands
docker-up:
	cd docker && docker-compose up -d

docker-down:
	cd docker && docker-compose down

docker-logs:
	cd docker && docker-compose logs -f

docker-rebuild:
	cd docker && docker-compose down && docker-compose build --no-cache && docker-compose up -d

# Airflow commands
airflow-up:
	cd docker && docker-compose up -d airflow-postgres airflow-webserver airflow-scheduler

airflow-down:
	cd docker && docker-compose stop airflow-webserver airflow-scheduler airflow-postgres

airflow-restart:
	cd docker && docker-compose restart airflow-webserver airflow-scheduler

airflow-logs:
	cd docker && docker-compose logs -f airflow-webserver airflow-scheduler

airflow-shell:
	cd docker && docker-compose exec airflow-webserver bash

airflow-init:
	cd docker && docker-compose up -d airflow-postgres
	cd docker && docker-compose run --rm airflow-webserver airflow db init
	cd docker && docker-compose run --rm airflow-webserver airflow users create \
		--username admin \
		--password admin \
		--firstname Admin \
		--lastname User \
		--role Admin \
		--email admin@example.com

# Testing
test:
	pytest tests/ -v

test-coverage:
	pytest --cov=src tests/

# format code with black
format:
	black src/*.py
	black src/ingestion/*.py
	black src/analysis/*.py
	black tests/*.py

# Run linter (flake8 for Python files)
lint:
	flake8 src/*.py
	flake8 src/ingestion/*.py
	flake8 src/analysis/*.py
	flake8 tests/*.py

# Data ingestion
download:
	python src/ingestion/gutenberg_downloader.py

extract-metadata:
	python src/metadata/metadata_extractor.py

clean-metadata:
	python src/metadata/metadata_cleaner.py

# Streaming pipeline
start-producer:
	python src/streaming/wiki_producer.py

start-consumer:
	python src/streaming/wiki_consumer.py

run-dashboard:
	streamlit run src/streaming/dashboard.py

# Text normalization
normalize-shakespeare:
	python src/normalize_spelling.py --input data/FullShakespeare.txt \
	    --output data/FullShakespeare.normalized.txt

train-normalizer:
	python src/train_and_test.py --input data/FullShakespeare.txt --split 0.8

# Testing
test:
	pytest tests/ -v

# Analysis
analyze-gutenberg:
	@echo "Fetching Gutenberg metadata..."
	python src/analysis/gutenberg_metadata_fetcher.py

analyze-polars:
	@echo "Running Polars analysis..."
	python src/analysis/gutenberg_polars_analysis.py

normalize-stats:
	@echo "Running normalization statistical analysis..."
	python src/analysis/normalize_spelling_stats.py

analyze-all: analyze-gutenberg analyze-polars normalize-stats
	@echo ""
	@echo "✓ All analyses complete!"
	@echo "✓ Check src/analysis/ for output files"

# Docker
docker-up:
	cd docker && docker-compose up -d

docker-down:
	cd docker && docker-compose down

# Show help
help:
	@echo "Available commands:"
	@echo ""
	@echo "Installation:"
	@echo "  make install            - Install Python dependencies"
	@echo "  make clean              - Clean temporary files"
	@echo ""
	@echo "Data Ingestion:"
	@echo "  make download           - Download books from Project Gutenberg"
	@echo "  make extract-metadata   - Extract metadata using AWS Bedrock"
	@echo "  make clean-metadata     - Clean and deduplicate metadata"
	@echo ""
	@echo "Streaming Pipeline:"
	@echo "  make start-producer     - Start Kafka producer (Wikipedia pageviews)"
	@echo "  make start-consumer     - Start Kafka consumer (save to PostgreSQL)"
	@echo ""
	@echo "NLP Tasks:"
	@echo "  make normalize-shakespeare - Normalize Shakespeare text"
	@echo "  make train-normalizer      - Train spelling normalizer"
	@echo ""
	@echo "Visualization:"
	@echo "  make streamlit          - Start Streamlit dashboard"
	@echo ""
	@echo "Docker Commands:"
	@echo "  make docker-up          - Start all Docker services"
	@echo "  make docker-down        - Stop all Docker services"
	@echo "  make docker-logs        - View Docker logs"
	@echo "  make docker-rebuild     - Rebuild and restart Docker services"
	@echo ""
	@echo "Airflow Commands:"
	@echo "  make airflow-up         - Start Airflow services"
	@echo "  make airflow-down       - Stop Airflow services"
	@echo "  make airflow-restart    - Restart Airflow services"
	@echo "  make airflow-logs       - View Airflow logs"
	@echo "  make airflow-shell      - Open Airflow shell"
	@echo "  make airflow-init       - Initialize Airflow database and create admin user"
	@echo ""
	@echo "Testing:"
	@echo "  make test               - Run all tests"
	@echo "  make test-coverage      - Run tests with coverage report"

all:
	install format
	@echo "Analysis:"
	@echo "  make analyze-gutenberg  - Fetch Gutenberg metadata"
	@echo "  make analyze-polars     - Run Polars analysis"
	@echo "  make normalize-stats    - Run normalization stats"
	@echo "  make analyze-all        - Run all analyses"
	@echo ""
	@echo "Testing:"
	@echo "  make test               - Run all tests"
	@echo "  make test-stats         - Run statistical tests only"
	@echo "  make test-normalize     - Run normalization tests only"
	@echo "  make test-all           - Run all tests with summary"
	@echo ""
	@echo "Code Quality:"
	@echo "  make format             - Format code with black"
	@echo "  make lint               - Run linter (flake8)"


all: install format lint test
	@echo "✓ Full build complete!"

.PHONY: install clean format lint download extract-metadata clean-metadata \
	start-producer start-consumer run-dashboard normalize-shakespeare \
	train-normalizer stats examples stats-full test test-stats test-normalize \
	test-all docker-up docker-down help all
