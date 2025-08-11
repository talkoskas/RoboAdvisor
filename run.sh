#!/bin/bash
source .venv/Scripts/activate  # for Git Bash on Windows
streamlit run --browser.serverAddress "roboadvisor.cs.bgu.ac.il" --server.port 443 MainStreamlit.py
