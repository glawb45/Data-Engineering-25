# Install Python dependencies
install:
	pip install -r requirements.txt

# Clean temporary files
clean:
	rm -rf __pycache__ */__pycache__ *.pyc

# format code with black
format:
	black src/*.py
	black src/ingestion/*.py

# Run linter (flake8 for Python files)
lint:
	flake8 --ignore=W503,C,N src/*.py
	flake8 --ignore=W503,C,N src/ingestion*.py
# Show help
help:
	@echo "Available commands:"
	@echo "  make install     - Install dependencies"
	@echo "  make ingest      - Run ingestion step"
	@echo "  make transform   - Run transform step"
	@echo "  make regression  - Run regression"
	@echo "  make pipeline    - Run full pipeline"
	@echo "  make streamlit   - Start Streamlit app"
	@echo "  make airflow     - Start Airflow (via docker)"
	@echo "  make clean       - Clean build/data files"