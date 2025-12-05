# Install Python dependencies
install:
	pip install --upgrade pip &&\
		pip install -r requirements.txt
		
# Clean temporary files
clean:
	rm -rf __pycache__ */__pycache__ *.pyc

# format code with black
format:
	black src/*.py
	black src/ingestion/*.py
	black src/analysis/*.py
	black tests/*.py

# Run linter (flake8 for Python files)
lint:
	flake8 --ignore=W503,C,N src/*.py
	flake8 --ignore=W503,C,N src/ingestion/*.py
	flake8 --ignore=W503,C,N src/analysis/*.py
	flake8 --ignore=W503,C,N tests/*.py

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
	@echo "Installation & Setup:"
	@echo "  make install            - Install dependencies"
	@echo "  make clean              - Clean build/data files"
	@echo ""
	@echo "Data Pipeline:"
	@echo "  make download           - Download Gutenberg books"
	@echo "  make extract-metadata   - Extract metadata from books"
	@echo "  make clean-metadata     - Clean metadata"
	@echo ""
	@echo "Streaming:"
	@echo "  make start-producer     - Start Wikipedia producer"
	@echo "  make start-consumer     - Start Wikipedia consumer"
	@echo "  make run-dashboard      - Start Streamlit dashboard"
	@echo ""
	@echo "Text Normalization:"
	@echo "  make normalize-shakespeare - Normalize Shakespeare text"
	@echo "  make train-normalizer      - Train normalizer model"
	@echo ""
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
	@echo ""
	@echo "Docker:"
	@echo "  make docker-up          - Start Docker containers"
	@echo "  make docker-down        - Stop Docker containers"

all: install format lint test
	@echo "✓ Full build complete!"

.PHONY: install clean format lint download extract-metadata clean-metadata \
	start-producer start-consumer run-dashboard normalize-shakespeare \
	train-normalizer stats examples stats-full test test-stats test-normalize \
	test-all docker-up docker-down help all