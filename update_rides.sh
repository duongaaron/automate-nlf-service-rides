#!/bin/bash

# Run the Python script
python3 api_allocate_modular/main.py

# Stage all changes
git add .

# Commit with message
git commit -m "update for this week's rides"

# Push to remote
git push