from contextlib import contextmanager
import re
import sqlite3

import pytest

from meal_max.models.kitchen_model import (
    Meal,
    create_meal,
    clear_meals,
    delete_meal,
    get_meal_by_id,
    get_meal_by_name,
    get_leaderboard,
    update_meal_stats
)

######################################################
#
#    Fixtures
#
######################################################

def normalize_whitespace(sql_query: str) -> str:
    return re.sub(r'\s+', ' ', sql_query).strip()

# Mocking the database connection for tests
@pytest.fixture
def mock_cursor(mocker):
    mock_conn = mocker.Mock()
    mock_cursor = mocker.Mock()

    # Mock the connection's cursor
    mock_conn.cursor.return_value = mock_cursor
    mock_cursor.fetchone.return_value = None  # Default return for queries
    mock_cursor.fetchall.return_value = []
    mock_conn.commit.return_value = None

    # Mock the get_db_connection context manager from sql_utils
    @contextmanager
    def mock_get_db_connection():
        yield mock_conn  # Yield the mocked connection object

    mocker.patch("meal_max.models.kitchen_model.get_db_connection", mock_get_db_connection)

    return mock_cursor  # Return the mock cursor so we can set expectations per test

######################################################
#
#    Add and delete
#
######################################################

def test_create_meal(mock_cursor):
    """Test creating a new meal in the kitchen."""
    
    # Call the function to create a new meal
    create_meal(meal="Meal Name", cuisine="Cuisine", price=10.00, difficulty="LOW")
    
    expected_query = normalize_whitespace("""
        INSERT INTO meals (meal, cuisine, price, difficulty)
        VALUES (?, ?, ?, ?)
    """)
    
    actual_query = normalize_whitespace(mock_cursor.execute.call_args[0][0])
    
    # Assert that the SQL query was correct
    assert actual_query == expected_query, "The SQL query did not match the expected structure."
    
    # Extract the arguments used in the SQL call (second element of call_args)
    actual_arguments = mock_cursor.execute.call_args[0][1]
    
    # Assert that the SQL query was executed with the correct arguments
    expected_arguments = ("Meal Name", "Cuisine", 10.00, "LOW")
    assert actual_arguments == expected_arguments, "The SQL arguments did not match the expected values."
    
def test_create_meal_duplicate(mock_cursor):
    """Test creating a new meal with a duplicate name."""
    
    # Simulate that the db will raise an IntegrityError due to duplicate entry
    mock_cursor.execute.side_effect=sqlite3.IntegrityError("UNIQUE constraint failed: meals.meal")
    
    # Expect the function to raise a ValueError with a specifc message when handling the IntegrityError
    with pytest.raises(ValueError, match="Meal with name 'Meal Name' already exists"):
        create_meal(meal="Meal Name", cuisine="Cuisine", price=10.00, difficulty="LOW")
        
def test_create_meal_invalid_price_type():
    """Test creating a new meal with an invalid price type (not int or float)."""
    
    # Expect the function to raise a ValueError with a specific message when the price is not a number
    with pytest.raises(ValueError, match="Invalid price: ten. Price must be a positive number."):
        create_meal(meal="Meal Name", cuisine="Cuisine", price="ten", difficulty="LOW")

def test_create_meal_invalid_price_value():
    """Test creating a new meal with an invalid price value (negative number)."""
    
    # Expect the function to raise a ValueError with a specific message when the price is negative
    with pytest.raises(ValueError, match="Invalid price: -10. Price must be a positive number."):
        create_meal(meal="Meal Name", cuisine="Cuisine", price=-10, difficulty="LOW")
        
def test_create_meal_invalid_difficulty():
    """Test creating a new meal with an invalid difficulty level."""
    
    # Expect the function to raise a ValueError with a specific message when the difficulty is invalid
    with pytest.raises(ValueError, match="Invalid difficulty level: MEDIUM. Must be 'LOW', 'MED', or 'HIGH'."):
        create_meal(meal="Meal Name", cuisine="Cuisine", price=10.00, difficulty="MEDIUM")

def test_create_meal_db_error(mock_cursor):
    """Test creating a new meal when a database error occurs."""
    
    # Simulate a database error by raising an exception
    mock_cursor.execute.side_effect = sqlite3.Error("Database error")
    
    # Expect the function to raise a sqlite3.Error when a database error occurs
    with pytest.raises(sqlite3.Error):
        create_meal(meal="Meal Name", cuisine="Cuisine", price=10.00, difficulty="LOW")
        
def test_delete_meal(mock_cursor):
    """Test deleting a meal from the kitchen."""
    
    # Simulate that the meal exists in the database (id = 1)
    mock_cursor.fetchone.return_value = ([False])
    
    # Call the delete_meal function
    delete_meal(1)
    expected_select_sql = normalize_whitespace("SELECT deleted FROM meals WHERE id = ?")
    expected_update_sql = normalize_whitespace("UPDATE meals SET deleted = TRUE WHERE id = ?")
    
    # Access both calls to `execute()` using `call_args_list`
    actual_select_sql = normalize_whitespace(mock_cursor.execute.call_args_list[0][0][0])
    actual_update_sql = normalize_whitespace(mock_cursor.execute.call_args_list[1][0][0])
    
    # Ensure the correct SQL queries were executed
    assert actual_select_sql == expected_select_sql, "The SELECT query did not match the expected structure."
    assert actual_update_sql == expected_update_sql, "The UPDATE query did not match the expected structure."
    
    # Ensure the correct arguments were used in both SQL queries
    expected_select_args = (1,)
    expected_update_args = (1,)

    actual_select_args = mock_cursor.execute.call_args_list[0][0][1]
    actual_update_args = mock_cursor.execute.call_args_list[1][0][1]

    assert actual_select_args == expected_select_args, f"The SELECT query arguments did not match. Expected {expected_select_args}, got {actual_select_args}."
    assert actual_update_args == expected_update_args, f"The UPDATE query arguments did not match. Expected {expected_update_args}, got {actual_update_args}."
    
def test_delete_meal_not_found(mock_cursor):
    """Test deleting a meal that does not exist."""
    
    # Simulate that the meal does not exist in the database
    mock_cursor.fetchone.return_value = None
    
    # Expect the function to raise a ValueError with a specific message when the meal is not found
    with pytest.raises(ValueError, match="Meal with ID 1 not found"):
        delete_meal(1)
        
def test_delete_meal_already_deleted(mock_cursor):
    """Test deleting a meal that has already been deleted."""
    
    # Simulate that the meal has already been deleted (deleted = True)
    mock_cursor.fetchone.return_value = ([True])
    
    # Expect the function to raise a ValueError with a specific message when the meal has already been deleted
    with pytest.raises(ValueError, match="Meal with ID 1 has been deleted"):
        delete_meal(1)

def test_delete_meal_db_error(mock_cursor):
    """Test deleting a meal when a database error occurs."""
    
    # Simulate a database error by raising an exception
    mock_cursor.execute.side_effect = sqlite3.Error("Database error")
    
    # Expect the function to raise a sqlite3.Error when a database error occurs
    with pytest.raises(sqlite3.Error):
        delete_meal(1)
        
def test_clear_meals(mock_cursor, mocker):
    """Test clearing all meals from the kitchen (removes all meals)."""
    
    # Mock the file reading
    mocker.patch.dict('os.environ', {'SQL_CREATE_TABLE_PATH': 'sql/create_meal_table.sql'})
    mock_open = mocker.patch('builtins.open', mocker.mock_open(read_data="The body of the create statement"))
    
    # Call the clear_meals function
    clear_meals()
    
    # Ensure the file was opened using the environment variable's path
    mock_open.assert_called_once_with('sql/create_meal_table.sql', 'r')

    # Verify that the correct SQL script was executed
    mock_cursor.executescript.assert_called_once()
    
def test_clear_meals_db_error(mock_cursor, mocker):
    """Test clearing all meals from the kitchen when a database error occurs."""
    
    # Mock the file reading
    mocker.patch.dict('os.environ', {'SQL_CREATE_TABLE_PATH': 'sql/create_meal_table.sql'})
    mocker.patch('builtins.open', mocker.mock_open(read_data="The body of the create statement"))
    
    # Simulate a database error by raising an exception
    mock_cursor.executescript.side_effect = sqlite3.Error("Database error")
    
    # Expect the function to raise a sqlite3.Error when a database error occurs
    with pytest.raises(sqlite3.Error):
        clear_meals()
    
    
    
######################################################
#
#    Get Meal
#
######################################################

def test_get_meal_by_id(mock_cursor):
    # Simulate that the meal exists in the database (id = 1)
    mock_cursor.fetchone.return_value = (1, "Meal Name", "Cuisine", 10.00, "LOW", False)
    
    # Call the get_meal_by_id function and check the result
    result = get_meal_by_id(1)
    
    # Expected result based on the simulated fetchone return value
    expected_result = Meal(1, "Meal Name", "Cuisine", 10.00, "LOW")
    
    assert result == expected_result, f"Expected {expected_result}, got {result}"
    
    # Ensure the SQL query was executed correctly
    expected_query = normalize_whitespace("SELECT id, meal, cuisine, price, difficulty, deleted FROM meals WHERE id = ?")
    actual_query = normalize_whitespace(mock_cursor.execute.call_args[0][0])
    
    # Assert that the SQL query was correct
    assert actual_query == expected_query, "The SQL query did not match the expected structure."
    
    # Extract the arguments used in the SQL call
    actual_arguments = mock_cursor.execute.call_args[0][1]
    
    # Assert that the SQL query was executed with the correct arguments
    expected_arguments = (1,)
    assert actual_arguments == expected_arguments, "The SQL arguments did not match the expected values."
    
def test_get_meal_by_id_not_found(mock_cursor):
    # Simulate that the meal does not exist in the database
    mock_cursor.fetchone.return_value = None
    
    # Expect the function to raise a ValueError with a specific message when the meal is not found
    with pytest.raises(ValueError, match="Meal with ID 999 not found"):
        get_meal_by_id(999)

def test_get_meal_by_id_deleted(mock_cursor):
    # Simulate that the meal has already been deleted (deleted = True)
    mock_cursor.fetchone.return_value = (1, "Meal Name", "Cuisine", 10.00, "LOW", True)
    
    # Expect the function to raise a ValueError with a specific message when the meal has already been deleted
    with pytest.raises(ValueError, match="Meal with ID 1 has been deleted"):
        get_meal_by_id(1)

def test_get_meal_by_id_db_error(mock_cursor):
    # Simulate a database error by raising an exception
    mock_cursor.execute.side_effect = sqlite3.Error("Database error")
    
    # Expect the function to raise a sqlite3.Error when a database error occurs
    with pytest.raises(sqlite3.Error):
        get_meal_by_id(1)

def test_get_meal_by_name(mock_cursor):
    # Simulate that the meal exists in the database (id = 1)
    mock_cursor.fetchone.return_value = (1, "Meal Name", "Cuisine", 10.00, "LOW", False)
    
    # Call the get_meal_by_name function and check the result
    result = get_meal_by_name("Meal Name")
    
    # Expected result based on the simulated fetchone return value
    expected_result = Meal(1, "Meal Name", "Cuisine", 10.00, "LOW")
    
    assert result == expected_result, f"Expected {expected_result}, got {result}"
    
    # Ensure the SQL query was executed correctly
    expected_query = normalize_whitespace("SELECT id, meal, cuisine, price, difficulty, deleted FROM meals WHERE meal = ?")
    actual_query = normalize_whitespace(mock_cursor.execute.call_args[0][0])
    
    # Assert that the SQL query was correct
    assert actual_query == expected_query, "The SQL query did not match the expected structure."
    
    # Extract the arguments used in the SQL call
    actual_arguments = mock_cursor.execute.call_args[0][1]
    
    # Assert that the SQL query was executed with the correct arguments
    expected_arguments = ("Meal Name",)
    assert actual_arguments == expected_arguments, "The SQL arguments did not match the expected values."
    
def test_get_meal_by_name_not_found(mock_cursor):
    # Simulate that the meal does not exist in the database
    mock_cursor.fetchone.return_value = None
    
    # Expect the function to raise a ValueError with a specific message when the meal is not found
    with pytest.raises(ValueError, match="Meal with name Non-existent Meal not found"):
        get_meal_by_name("Non-existent Meal")
        
def test_get_meal_by_name_deleted(mock_cursor):
    # Simulate that the meal has already been deleted (deleted = True)
    mock_cursor.fetchone.return_value = (1, "Meal Name", "Cuisine", 10.00, "LOW", True)
    
    # Expect the function to raise a ValueError with a specific message when the meal has already been deleted
    with pytest.raises(ValueError, match="Meal with name Meal Name has been deleted"):
        get_meal_by_name("Meal Name")

def test_get_meal_by_name_db_error(mock_cursor):
    # Simulate a database error by raising an exception
    mock_cursor.execute.side_effect = sqlite3.Error("Database error")
    
    # Expect the function to raise a sqlite3.Error when a database error occurs
    with pytest.raises(sqlite3.Error):
        get_meal_by_name("Meal Name")
        
def test_get_leaderboard(mock_cursor):
    """Test retrieving the leaderboard of meals."""
    
    # Simulate that the leaderboard has values
    mock_cursor.fetchall.return_value = [
        (1, "Meal 1", "Cuisine A", 10.00, "LOW", 10, 5, 0.5),
        (2, "Meal 2", "Cuisine B", 15.00, "MED", 10, 4, 0.4),
        (3, "Meal 3", "Cuisine C", 20.00, "HIGH", 10, 3, 0.3)
    ]
    
    # Call the get_leaderboard function
    leaderboard = get_leaderboard()
    
    # Ensure the results match the expected output
    expected_result = [
        {"id": 1, "meal": "Meal 1", "cuisine": "Cuisine A", "price": 10.00, "difficulty": "LOW",  "battles": 10, "wins": 5, "win_pct": 50.0},
        {"id": 2, "meal": "Meal 2", "cuisine": "Cuisine B", "price": 15.00, "difficulty": "MED", "battles": 10, "wins": 4, "win_pct": 40.0},
        {"id": 3, "meal": "Meal 3", "cuisine": "Cuisine C", "price": 20.00, "difficulty": "HIGH", "battles": 10, "wins": 3, "win_pct": 30.0}
    ]
    
    assert leaderboard == expected_result, f"Expected {expected_result}, got {leaderboard}"
    
    # Ensure the SQL query was executed correctly
    expected_query = normalize_whitespace("""
        SELECT id, meal, cuisine, price, difficulty, battles, wins, (wins * 1.0 / battles) AS win_pct
        FROM meals
        WHERE deleted = false
        AND battles > 0      
        ORDER BY wins DESC                                               
    """)
    actual_query = normalize_whitespace(mock_cursor.execute.call_args[0][0])
    
    assert actual_query == expected_query, "The SQL query did not match the expected structure."
    
def test_get_leaderboard_by_win_pct(mock_cursor):
    """Test retrieving the leaderboard of meals by win pct."""
    
    # Simulate that the leaderboard has values
    mock_cursor.fetchall.return_value = [
        (1, "Meal 1", "Cuisine A", 10.00, "LOW", 10, 5, 0.5),
        (2, "Meal 2", "Cuisine B", 15.00, "MED", 10, 4, 0.4),
        (3, "Meal 3", "Cuisine C", 20.00, "HIGH", 10, 3, 0.3)
    ]
    
    # Call the get_leaderboard function
    leaderboard = get_leaderboard(sort_by="win_pct")
    
    # Ensure the results match the expected output
    expected_result = [
        {"id": 1, "meal": "Meal 1", "cuisine": "Cuisine A", "price": 10.00, "difficulty": "LOW",  "battles": 10, "wins": 5, "win_pct": 50.0},
        {"id": 2, "meal": "Meal 2", "cuisine": "Cuisine B", "price": 15.00, "difficulty": "MED", "battles": 10, "wins": 4, "win_pct": 40.0},
        {"id": 3, "meal": "Meal 3", "cuisine": "Cuisine C", "price": 20.00, "difficulty": "HIGH", "battles": 10, "wins": 3, "win_pct": 30.0}
    ]
    
    assert leaderboard == expected_result, f"Expected {expected_result}, got {leaderboard}"
    
    # Ensure the SQL query was executed correctly
    expected_query = normalize_whitespace("""
        SELECT id, meal, cuisine, price, difficulty, battles, wins, (wins * 1.0 / battles) AS win_pct
        FROM meals
        WHERE deleted = false
        AND battles > 0      
        ORDER BY win_pct DESC                                               
    """)
    actual_query = normalize_whitespace(mock_cursor.execute.call_args[0][0])
    
    assert actual_query == expected_query, "The SQL query did not match the expected structure."
    
def test_get_leaderboard_invalid_sort_by():
    """Test retrieving the leaderboard of meals with an invalid sort_by parameter."""
    
    # Expect the function to raise a ValueError with a specific message when the sort_by parameter is invalid
    with pytest.raises(ValueError, match="Invalid sort_by parameter: price"):
        get_leaderboard(sort_by="price")

def test_get_leaderboard_empty(mock_cursor):
    """Test retrieving the leaderboard of meals when the database is empty."""
        
    # Simulate that the leaderboard has no values
    mock_cursor.fetchall.return_value = []
    
    # Call the get_leaderboard function
    leaderboard = get_leaderboard()
    
    # Ensure the results are empty
    assert leaderboard == [], "The leaderboard should be empty when no meals are present."
    
    # Ensure the SQL query was executed correctly
    expected_query = normalize_whitespace("""
        SELECT id, meal, cuisine, price, difficulty, battles, wins, (wins * 1.0 / battles) AS win_pct
        FROM meals
        WHERE deleted = false
        AND battles > 0      
        ORDER BY wins DESC                                               
    """)
    actual_query = normalize_whitespace(mock_cursor.execute.call_args[0][0])
    
    assert actual_query == expected_query, "The SQL query did not match the expected structure."

def test_get_leaderboard_db_error(mock_cursor):
    """Test retrieving the leaderboard of meals when a database error occurs."""
    
    # Simulate a database error by raising an exception
    mock_cursor.execute.side_effect = sqlite3.Error("Database error")
    
    # Expect the function to raise a sqlite3.Error when a database error occurs
    with pytest.raises(sqlite3.Error):
        get_leaderboard()
    
######################################################
#
#    Update Meal Stats
#
######################################################

def test_update_meal_stats_win(mock_cursor):
    """Test updating the stats for a meal."""
    
    # Simulate that the meal exists in the database (id = 1)
    mock_cursor.fetchone.return_value = ([False])
    
    # Call the update_meal_stats function
    update_meal_stats(1, "win")
    
    # Ensure the SQL query was executed correctly
    expected_query = normalize_whitespace("UPDATE meals SET battles = battles + 1, wins = wins + 1 WHERE id = ?")
    actual_query = normalize_whitespace(mock_cursor.execute.call_args[0][0])
    
    assert actual_query == expected_query, "The SQL query did not match the expected structure."
    
    # Extract the arguments used in the SQL call
    actual_arguments = mock_cursor.execute.call_args[0][1]
    
    # Assert that the SQL query was executed with the correct arguments
    expected_arguments = (1,)
    assert actual_arguments == expected_arguments, "The SQL arguments did not match the expected values."
    
def test_update_meal_stats_loss(mock_cursor):
    """Test updating the stats for a meal."""
    
    # Simulate that the meal exists in the database (id = 1)
    mock_cursor.fetchone.return_value = ([False])
    
    # Call the update_meal_stats function
    update_meal_stats(1, "loss")
    
    # Ensure the SQL query was executed correctly
    expected_query = normalize_whitespace("UPDATE meals SET battles = battles + 1 WHERE id = ?")
    actual_query = normalize_whitespace(mock_cursor.execute.call_args[0][0])
    
    assert actual_query == expected_query, "The SQL query did not match the expected structure."
    
    # Extract the arguments used in the SQL call
    actual_arguments = mock_cursor.execute.call_args[0][1]
    
    # Assert that the SQL query was executed with the correct arguments
    expected_arguments = (1,)
    assert actual_arguments == expected_arguments, "The SQL arguments did not match the expected values."

def test_update_meal_stats_invalid_result(mock_cursor):
    """Test updating the stats for a meal with an invalid result."""
    
    # Simulate that the meal exists in the database (id = 1)
    mock_cursor.fetchone.return_value = ([False])
    
    # Expect the function to raise a ValueError with a specific message when the result is invalid
    with pytest.raises(ValueError, match="Invalid result: draw. Expected 'win' or 'loss'."):
        update_meal_stats(1, "draw")

def test_update_meal_stats_deleted(mock_cursor):
    """Test updating the stats for a meal that has been deleted."""
    
    # Simulate that the meal has already been deleted (deleted = True)
    mock_cursor.fetchone.return_value = ([True])
    
    # Expect the function to raise a ValueError with a specific message when the meal has already been deleted
    with pytest.raises(ValueError, match="Meal with ID 1 has been deleted"):
        update_meal_stats(1, "win")

def test_update_meal_stats_not_found(mock_cursor):
    """Test updating the stats for a meal that does not exist."""
    
    # Simulate that the meal does not exist in the database
    mock_cursor.fetchone.return_value = None
    
    # Expect the function to raise a ValueError with a specific message when the meal is not found
    with pytest.raises(ValueError, match="Meal with ID 999 not found"):
        update_meal_stats(999, "win")
        
def test_update_meal_stats_db_error(mock_cursor):
    """Test updating the stats for a meal when a database error occurs."""
    
    # Simulate a database error by raising an exception
    mock_cursor.execute.side_effect = sqlite3.Error("Database error")
    
    # Expect the function to raise a sqlite3.Error when a database error occurs
    with pytest.raises(sqlite3.Error):
        update_meal_stats(1, "win")
