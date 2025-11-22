#!/bin/bash

# Full ClinicalTrials.gov Ingestion Script
# Scheduled for 1am EST, Nov 23, 2025

cd /Users/mananshah/Dev/pilldreams

# Activate virtual environment
source venv/bin/activate

# Log start time
echo "========================================" >> full_ingestion.log
echo "Full ingestion started at $(date)" >> full_ingestion.log
echo "========================================" >> full_ingestion.log

# Run ingestion WITHOUT --max-trials limit (fetch ALL trials)
python3 ingestion/clinicaltrials.py 2>&1 | tee -a full_ingestion.log

# Log completion
echo "========================================" >> full_ingestion.log
echo "Full ingestion completed at $(date)" >> full_ingestion.log
echo "========================================" >> full_ingestion.log

# Send notification (optional - using say command on macOS)
say "Clinical trials ingestion complete"
