import pytest

from meal_max.models.battle_model import BattleModel
from meal_max.models.kitchen_model import Meal

@pytest.fixture
def mock_update_meal_stats(mocker):
    """Mock the update_meal_stats function for testing purposes."""
    return mocker.patch("meal_max.models.battle_model.update_meal_stats")

@pytest.fixture
def mock_get_random(mocker):
    """Mock the get_random function for testing purposes."""
    return mocker.patch("meal_max.models.battle_model.get_random", return_value = 0.52)

@pytest.fixture
def battle_model():
    """Fixture to provide a new instance of BattleModel for each test."""
    return BattleModel()

"""Fixtures providing sample combatants for the tests."""
@pytest.fixture
def sample_meal1():
    return Meal(1, 'Meal 1', 'Italian', 24.99, 'MED')

@pytest.fixture
def sample_meal2():
    return Meal(2, 'Meal 2', 'French', 49.99, 'HIGH')

@pytest.fixture
def sample_meal3():
    return Meal(3, 'Meal 3', 'Spanish', 54.99, 'HIGH')

@pytest.fixture
def sample_combatants(sample_meal1, sample_meal2):
    return [sample_meal1, sample_meal2]

##################################################
# Add Meal Management Test Cases
##################################################

def test_add_meal_to_combatants(battle_model, sample_meal1):
    """Test adding a meal to the combatants list."""
    battle_model.prep_combatant(sample_meal1)
    assert len(battle_model.combatants) == 1
    assert battle_model.combatants[0].meal == 'Meal 1'

def test_add_meal_to_full_combatants(battle_model, sample_combatants, sample_meal3):
    """Test error when adding a meal to the combatants list when it is full."""

    battle_model.combatants.extend(sample_combatants)
    assert len(battle_model.combatants) == 2

    with pytest.raises(ValueError, match="Combatant list is full, cannot add more combatants."):
        battle_model.prep_combatant(sample_meal3)

##################################################
# Remove Meal Management Test Cases
##################################################

def test_clear_combatants(battle_model, sample_meal1):
    """Test clearing the entire combatants list."""
    battle_model.prep_combatant(sample_meal1)

    battle_model.clear_combatants()
    assert len(battle_model.combatants) == 0, "Combatants list should be empty after clearing"


##################################################
# Meal Retrieval Test Cases
##################################################

def test_get_combatants(battle_model, sample_combatants):
    """Test successfully retrieving all meals from the combatant list."""
    battle_model.combatants.extend(sample_combatants)

    all_meals = battle_model.get_combatants()
    assert len(all_meals) == 2
    assert all_meals[0].id == 1
    assert all_meals[1].id == 2

##################################################
# Utility Function Test Cases
##################################################

def test_get_battle_score(battle_model, sample_meal2):
    """Test successfully calculating a meal's score."""

    score = battle_model.get_battle_score(sample_meal2)
    assert score == 298.94, "Expected Meal 2 to have a score of 298.94"

##################################################
# Battle Test Cases
##################################################

def test_battle(battle_model, sample_combatants, mock_update_meal_stats, mock_get_random):
    """Test the battle method without interacting with the actual database."""
    battle_model.combatants.extend(sample_combatants)

    assert len(battle_model.combatants) == 2

    score_1 = battle_model.get_battle_score(sample_combatants[0])
    score_2 = battle_model.get_battle_score(sample_combatants[1])

    delta = abs(score_1 - score_2) / 100

    # Simulate retrieving a random number from random.org
    random_number = mock_get_random()

    winner = battle_model.battle()

    if delta > random_number:
        # Assert that update_play_count was called with the id of both combatants and their appropriate 'win' or 'loss' outcome
        mock_update_meal_stats.assert_any_call(1, 'win')
        mock_update_meal_stats.assert_any_call(2, 'loss')

        # Assert that the winner was Meal 1 in sample_combatants
        assert winner == sample_combatants[0].meal
    else:
         # Assert that update_play_count was called with the id of both combatants and their appropriate 'win' or 'loss' outcome
        mock_update_meal_stats.assert_any_call(2, 'win')
        mock_update_meal_stats.assert_any_call(1, 'loss')

        # Assert that the winner was Meal 2 in sample_combatants
        assert winner == sample_combatants[1].meal
    
    # Assert that the loser has been removed from the combatants list
    assert len(battle_model.combatants) == 1

def test_battle_one_combatant(battle_model, sample_meal1):
    """Test starting a battle with one combatant."""
    battle_model.prep_combatant(sample_meal1)
    assert len(battle_model.combatants) == 1

    with pytest.raises(ValueError, match="Two combatants must be prepped for a battle."):
        battle_model.battle()

def test_battle_empty_combatants(battle_model):
    """Test starting a battle with no combatants."""
    assert len(battle_model.combatants) == 0

    with pytest.raises(ValueError, match="Two combatants must be prepped for a battle."):
        battle_model.battle()
