# nlp_final_project
## Project Brainstorming & Proposal – Data Engineering Plan

1. Project Title & Description
Title: Data Engineering Pipeline for Historical Spelling Normalization
Description: This project will design and implement a robust data engineering pipeline to support an NLP system that normalizes Early Modern English spelling variants (1500–1700) into modern English equivalents. The pipeline will manage large-scale historical corpora (e.g., Early English Books Online) and synthetic data derived from rule-based transformations of modern text. Key tasks include data ingestion, preprocessing (tokenization, filtering, normalization), feature extraction, and model-ready dataset generation for both probabilistic and neural models. The engineering focus is to ensure scalable, reproducible, and clean data workflows that enable fair comparison between linguistic and deep learning approaches.

2. Preliminary Data Sources
    - Primary: Early English Books Online (EEBO) TCP Corpus
    https://textcreationpartnership.org/tcp-texts/eebo-tcp-early-english-books-online/
    Contains digitized Early Modern English texts from the 16th–17th centuries, annotated with XML metadata.
    - Synthetic Data:
    Generated from modern English corpora (e.g., Project Gutenberg texts) by applying reversible historical spelling rules (e.g., v/u interchange, -eth → -s, y → i substitutions). This will create aligned source-target pairs for supervised learning.
    - Supplementary:
        - British National Corpus (BNC) for modern English reference
        - Existing normalization datasets (if publicly available, e.g., VARD corpus or CEEC)

3. Preliminary Architecture and Steps
    - Step 1: Data Acquisition
        - Scrape or download EEBO TCP texts (XML format)
        - Collect modern English reference texts for rule generation


    - Step 2: Data Cleaning & Standardization
        - Parse XML to extract plain text
        - Transform XML file data to plain text
        - Normalize punctuation and remove metadata
        - Convert encoding to UTF-8 and unify case


    - Step 3: Synthetic Data Generation
        - Apply rule-based historical spelling transformations to modern texts
        - Bayes classifiers
        - Perceptron model
        - Store paired data as (historical_variant, modern_equivalent) in structured format (e.g., Parquet or CSV)
