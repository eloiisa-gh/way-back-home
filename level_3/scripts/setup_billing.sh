#!/bin/bash

# --- Function for error handling ---
handle_error() {
  echo -e "\n\n*******************************************************"
  echo "Error: $1"
  echo "*******************************************************"
  # Instead of exiting, we warn the user and wait for input
  echo "The script encountered an error."
  echo "Press [Enter] to ignore this error and attempt to continue."
  echo "Press [Ctrl+C] to exit the script completely."
  read -r # Pauses script here
}

# --- Install Dependencies and Run Billing Setup ---
echo -e "\n--- Installing Python dependencies ---"
# Using || handle_error means if it fails, it will pause, allow you to read, and then proceed
pip install --upgrade --user google-cloud-billing || handle_error "Failed to install Python libraries."

echo -e "\n--- Running the Billing Enablement Script ---"
python3 billing-enablement.py || handle_error "The billing enablement script failed."

echo -e "\n--- Billing Setup Complete ---"
