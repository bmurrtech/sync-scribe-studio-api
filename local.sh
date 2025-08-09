#!/bin/bash

# Sync Scribe Studio API - Local Development Script

# Stop all running Docker containers
echo "Stopping Sync Scribe Studio API containers..."
docker stop $(docker ps -a --filter ancestor=bmurrtech/sync-scribe-studio:testing --format="{{.ID}}")

# Build the Docker image
echo "Building Sync Scribe Studio API image..."
docker build -t bmurrtech/sync-scribe-studio:testing .

# Read variables from .variables file
echo "Reading environment variables..."
VARS=$(cat .env_variables.json)

# Function to escape JSON strings for bash
escape_json() {
    echo "$1" | sed 's/"/\\"/g'
}

# Build the docker run command with environment variables
CMD="docker run -p 8080:8080"

# Add environment variables from JSON
for key in $(echo "$VARS" | jq -r 'keys[]'); do
    value=$(echo "$VARS" | jq -r --arg k "$key" '.[$k]')
    
    # Handle nested JSON (specifically for GCP_SA_CREDENTIALS)
    if [[ "$key" == "GCP_SA_CREDENTIALS" ]]; then
        value=$(echo "$VARS" | jq -r --arg k "$key" '.[$k]')
        value=$(escape_json "$value")
    fi
    
    CMD="$CMD -e $key=\"$value\""
done

# Complete the command
CMD="$CMD bmurrtech/sync-scribe-studio:testing"

# Run the Docker container
echo "Starting Sync Scribe Studio API..."
eval "$CMD"
