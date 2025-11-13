# Install Python dependencies
install:
	pip install -r requirements.txt

# Clean temporary files
clean:
	rm -rf __pycache__ */__pycache__ *.pyc

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