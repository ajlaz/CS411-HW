#!/bin/bash

# Define the base URL for the Flask API
BASE_URL="http://localhost:5002/api"

# Flag to control whether to echo JSON output
ECHO_JSON=false

# Parse command-line arguments
while [ "$#" -gt 0 ]; do
  case $1 in
    --echo-json) ECHO_JSON=true ;;
    *) echo "Unknown parameter passed: $1"; exit 1 ;;
  esac
  shift
done


###############################################
#
# Health checks
#
###############################################

# Function to check the health of the service
check_health() {
  echo "Checking health status..."
  curl -s -X GET "$BASE_URL/health" | grep -q '"status": "healthy"'
  if [ $? -eq 0 ]; then
    echo "Service is healthy."
  else
    echo "Health check failed."
    exit 1
  fi
}

# Function to check the database connection
check_db() {
  echo "Checking database connection..."
  curl -s -X GET "$BASE_URL/db-check" | grep -q '"database_status": "healthy"'
  if [ $? -eq 0 ]; then
    echo "Database connection is healthy."
  else
    echo "Database check failed."
    exit 1
  fi
}

##########################################################
#
# Meal Management
#
##########################################################

clear_catalog() {
    echo "Clearing the meals catalog..."
    curl -s -X DELETE "$BASE_URL/clear-meals" | grep -q '"status": "success"'
}

create_meal() {
    meal=$1
    cuisine=$2
    price=$3
    difficulty=$4

    echo "Adding meal ($meal) to the catalog..."
    curl -s -X POST "$BASE_URL/create-meal" -H "Content-Type: application/json" \
    -d "{\"meal\":\"$meal\", \"cuisine\":\"$cuisine\", \"price\":$price, \"difficulty\":\"$difficulty\"}" | grep -q '"status": "success"'

    if [ $? -eq 0 ]; then
        echo "Meal added successfully."
    else
        echo "Failed to add meal."
        exit 1
    fi
}

delete_meal_by_id() {
    meal_id=$1

    echo "Deleting meal with ID ($meal_id)..."
    response=$(curl -s -X DELETE "$BASE_URL/delete-meal/$meal_id")
    if echo "$response" | grep -q '"status": "success"'; then
        echo "Meal deleted succesfully by ID ($meal_id)."
    else
        echo "Failed to delete meal by ID ($meal_id)."
        exit 1
    fi
}

get_meal_by_id() {
    meal_id=$1

    echo "Getting meal by ID($meal_id)..."
    response=$(curl -s -X GET "$BASE_URL/get-meal-by-id/$meal_id")
    if echo "$response" | grep -q '"status": "success"'; then
        echo "Meal retrieved successfully by ID ($meal_id)."
        if [ "$ECHO_JSON" = true ]; then
            echo "Meal JSON (ID $meal_id):"
            echo "$response" | jq .
    fi
  else
    echo "Failed to get meal by ID ($meal_id)."
    exit 1
  fi
}


get_meal_by_name() {
    meal=$1

    echo "Getting meal by name ($meal)..."
    response=$(curl -s -X GET "$BASE_URL/get-meal-by-name/$meal")
    if echo "$response" | grep -q '"status": "success"'; then
        echo "Meal retrieved successfully by name ($meal)."
        if [ "$ECHO_JSON" = true ]; then
            echo "Meal JSON (name $meal):"
            echo "$response" | jq .
    fi
  else
    echo "Failed to get meal by name ($meal)."
    exit 1
  fi
}

############################################################
#
# Battle Management
#
############################################################

prep_combatant() {
  meal=$1
  cuisine=$2
  price=$3

  echo "Adding meal to combatants: $meal - $cuisine ($price)..."
  response=$(curl -s -X POST "$BASE_URL/prep-combatant" \
    -H "Content-Type: application/json" \
    -d "{\"meal\":\"$meal\", \"cuisine\":\"$cuisine\", \"price\":$price}")

  if echo "$response" | grep -q '"status": "success"'; then
    echo "Meal added to combatants successfully."
    if [ "$ECHO_JSON" = true ]; then
      echo "Song JSON:"
      echo "$response" | jq .
    fi
  else
    echo "Failed to add meal to combatants."
    exit 1
  fi
}

clear_combatants() {
  echo "Clearing combatants..."
  response=$(curl -s -X POST "$BASE_URL/clear-combatants")

  if echo "$response" | grep -q '"status": "success"'; then
    echo "Combatants cleared successfully."
  else
    echo "Failed to clear combatants."
    exit 1
  fi
}

############################################################
#
# Start Battle
#
############################################################

battle() {
  echo "Starting battle..."
  response=$(curl -s -X GET "$BASE_URL/battle")

  if echo "$response" | grep -q '"status": "success"'; then
    echo "Battle is now occurring."
  else
    echo "Failed to start battle."
    exit 1
  fi
}

get_combatants() {
  echo "Retrieving all meals from combatants..."
  response=$(curl -s -X GET "$BASE_URL/get-combatants")

  if echo "$response" | grep -q '"status": "success"'; then
    echo "All meals retrieved successfully."
    if [ "$ECHO_JSON" = true ]; then
      echo "Songs JSON:"
      echo "$response" | jq .
    fi
  else
    echo "Failed to retrieve all meals from combatants."
    exit 1
  fi
}

############################################################
#
# Leaderboard
#
############################################################

get_leaderboard() {
    echo "Getting the meal leaderboard..."
    response=$(curl -s -X GET "$BASE_URL/leaderboard")
    if echo "$response" | grep -q '"status": "success"'; then
        echo "Leaderboard retrieved successfully."
        if [ "$ECHO_JSON" = true ]; then
            echo "Leaderboard JSON:"
            echo "$response" | jq .
    fi
  else
    echo "Failed to get the leaderboard."
    exit 1
  fi
}

# Run the health checks
check_health
check_db

# Clear the meal catalog
clear_catalog
clear_combatants

# Add some meals to the catalog
create_meal "Spaghetti" "Italian" 12.99 "MED"
create_meal "Pizza" "Italian" 14.99 "LOW"
create_meal "Sushi" "Japanese" 19.99 "HIGH"

delete_meal_by_id 1

get_meal_by_id 2
get_meal_by_name "Pizza"

prep_combatant "Pizza" "Italian" 14.99 "LOW"
prep_combatant "Sushi" "Japanese" 19.99 "HIGH"

get_combatants

battle

get_leaderboard

echo "All tests passed successfully."
