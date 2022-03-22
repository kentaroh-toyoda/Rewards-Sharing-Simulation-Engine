import pytest

from logic.pool import Pool
from logic.sim import Simulation
from logic.stakeholder import Stakeholder
from logic.strategy import Strategy
import logic.helper as hlp


# todo add more tests

# todo review failing test
def test_calculate_operator_utility():
    model = Simulation(total_stake=1)
    pool = Pool(cost=0.001, pledge=0.1, owner=156, margin=0.1, alpha=0.3, beta=0.1, pool_id=555,
                reward_function_option=0, total_stake=1)
    model.pools[555] = pool
    player = Stakeholder(unique_id=156, model=model, stake=0.1, cost=0.001)
    strategy = Strategy(owned_pools={555: pool})

    utility = player.calculate_operator_utility_from_strategy(strategy)

    assert utility == 0.0148638461538461537


def test_calculate_margin_perfect_strategy(mocker):
    total_stake = 1
    model = Simulation(k=2, total_stake=total_stake)
    player1 = Stakeholder(1, model, stake=0.001, cost=0.001)
    player2 = Stakeholder(2, model, stake=0.002, cost=0.001)
    player3 = Stakeholder(3, model, stake=0.003, cost=0.001)
    player4 = Stakeholder(4, model, stake=0.0001, cost=0.001)

    players_list = [player1, player2, player3, player4]
    mocker.patch('logic.sim.Simulation.get_players_list', return_value=players_list)

    player1_margin = player1.calculate_margin_perfect_strategy()
    player2_margin = player2.calculate_margin_perfect_strategy()
    player3_margin = player3.calculate_margin_perfect_strategy()
    player4_margin = player4.calculate_margin_perfect_strategy()

    assert player1_margin == player4_margin == 0
    assert player3_margin > player2_margin > 0


def test_calculate_margin_semi_perfect_strategy():
    total_stake = 1
    model = Simulation(k=2, total_stake=total_stake)
    player156 = Stakeholder(156, model, stake=0.001)
    player157 = Stakeholder(157, model, stake=0.005)
    player159 = Stakeholder(159, model, stake=0.0001)
    pool555 = Pool(cost=0.001, pledge=0.001, owner=156, alpha=0.3, beta=0.1, pool_id=555, reward_function_option=0,
                   total_stake=total_stake)
    model.pools[555] = pool555
    pool556 = Pool(cost=0.001, pledge=0.002, owner=157, alpha=0.3, beta=0.1, pool_id=556, reward_function_option=0,
                   total_stake=total_stake)
    model.pools[556] = pool556
    pool557 = Pool(cost=0.001, pledge=0.003, owner=157, alpha=0.3, beta=0.1, pool_id=557, reward_function_option=0,
                   total_stake=total_stake)
    model.pools[557] = pool557
    pool558 = Pool(cost=0.001, pledge=0.0001, owner=159, alpha=0.3, beta=0.1, pool_id=558, reward_function_option=0,
                   total_stake=total_stake)
    model.pools[558] = pool558

    pool555.margin = player156.calculate_margin_semi_perfect_strategy(pool555)
    pool556.margin = player157.calculate_margin_semi_perfect_strategy(pool556)
    pool557.margin = player157.calculate_margin_semi_perfect_strategy(pool557)
    pool558.margin = player159.calculate_margin_semi_perfect_strategy(pool558)

    assert pool555.margin == pool558.margin == 0
    assert pool557.margin > pool556.margin > 0

    desirability555 = hlp.calculate_pool_desirability(pool555.margin, pool555.potential_profit)
    desirability556 = hlp.calculate_pool_desirability(pool556.margin, pool556.potential_profit)
    desirability557 = hlp.calculate_pool_desirability(pool557.margin, pool557.potential_profit)
    desirability558 = hlp.calculate_pool_desirability(pool558.margin, pool558.potential_profit)
    assert desirability555 == desirability556 == desirability557 > desirability558 > 0


def test_close_pool():
    total_stake = 1
    model = Simulation(total_stake=total_stake)
    player = Stakeholder(156, model, 0.001)
    pool = Pool(cost=0.001, pledge=0.001, owner=156, margin=0.2, alpha=0.3, beta=0.1, pool_id=555,
                reward_function_option=0, total_stake=total_stake)
    model.pools[555] = pool

    player.close_pool(555)

    assert 555 not in model.pools.keys()

    # try to close the same pool again but get an exception because it doesn't exist anymore
    with pytest.raises(ValueError) as e_info:
        player.close_pool(555)
    assert str(e_info.value) == 'Given pool id is not valid.'

    # try to close another player's pool
    with pytest.raises(ValueError) as e_info:
        model.pools[555] = pool
        player = Stakeholder(157, model, 0.003)
        player.close_pool(555)
    assert str(e_info.value) == "Player tried to close pool that belongs to another player."


def test_determine_current_pools():
    total_stake = 1
    model = Simulation(total_stake=total_stake)
    player = Stakeholder(unique_id=1, model=model, stake=0.005)
    pool1 = Pool(cost=0.001, pledge=0.001, owner=1, margin=0.2, alpha=0.3, beta=0.1, pool_id=1,
                 reward_function_option=0, total_stake=total_stake)
    pool2 = Pool(cost=0.001, pledge=0.001, owner=1, margin=0.2, alpha=0.3, beta=0.1, pool_id=2,
                 reward_function_option=0, total_stake=total_stake)
    pool3 = Pool(cost=0.001, pledge=0.001, owner=1, margin=0.1, alpha=0.3, beta=0.1, pool_id=3,
                 reward_function_option=0, total_stake=total_stake)
    current_pools = {1: pool1, 2: pool2, 3: pool3}
    player.strategy.owned_pools = current_pools

    # new pool number same as current pool number so return all pools
    new_num_pools = 3
    pools_to_keep = player.determine_current_pools(new_num_pools)
    assert pools_to_keep.keys() == current_pools.keys()

    # new pool number higher than current pool number so return all pools
    new_num_pools = 4
    pools_to_keep = player.determine_current_pools(new_num_pools)
    assert pools_to_keep.keys() == current_pools.keys()

    # new pool number lower than current pool number so return best pools
    new_num_pools = 1
    pools_to_keep = player.determine_current_pools(new_num_pools)
    assert pools_to_keep.keys() == {3}

    # new pool number lower than current pool number so return best pools (with tie breaking)
    new_num_pools = 2
    pools_to_keep = player.determine_current_pools(new_num_pools)
    assert pools_to_keep.keys() == {1, 3}


def test_find_delegation_move():
    total_stake = 1
    k = 10
    model = Simulation(k=k, total_stake=total_stake)
    player156 = Stakeholder(156, model, stake=0.001)
    player157 = Stakeholder(157, model, stake=0.005)
    player158 = Stakeholder(158, model, stake=0.003)
    player159 = Stakeholder(159, model, stake=0.0001)
    pool555 = Pool(cost=0.001, pledge=0.001, owner=156, alpha=0.3, beta=0.1, pool_id=555, reward_function_option=0,
                   total_stake=total_stake, margin=0.1)
    model.pools[555] = pool555
    pool556 = Pool(cost=0.001, pledge=0.002, owner=157, alpha=0.3, beta=0.1, pool_id=556, reward_function_option=0,
                   total_stake=total_stake, margin=0.1)
    model.pools[556] = pool556
    pool557 = Pool(cost=0.001, pledge=0.003, owner=157, alpha=0.3, beta=0.1, pool_id=557, reward_function_option=0,
                   total_stake=total_stake, margin=0.1)
    model.pools[557] = pool557
    pool558 = Pool(cost=0.001, pledge=0.003, owner=158, alpha=0.3, beta=0.1, pool_id=558, reward_function_option=0,
                   total_stake=total_stake, margin=0)
    model.pools[558] = pool558

    # one pool with higher desirability, choose that
    delegator_strategy = player159.find_delegation_move()
    allocations = delegator_strategy.stake_allocations
    assert allocations.keys() == {558}
    assert allocations[558] == 0.0001

    # ties in desirability and potential profit, break with stake
    pool558.margin = 0.1
    pool558.stake = 0.007
    delegator_strategy = player159.find_delegation_move()
    allocations = delegator_strategy.stake_allocations
    assert allocations.keys() == {558}
    assert allocations[558] == 0.0001


    # ties in desirability, potential profit and stake, break with id
    pool558.stake = 0.003
    delegator_strategy = player159.find_delegation_move()
    allocations = delegator_strategy.stake_allocations
    assert allocations.keys() == {557}
    assert allocations[557] == 0.0001


    # highest desirability pools saturated, choose next
    pool558.stake = 0.1
    pool557.stake = 0.1
    delegator_strategy = player159.find_delegation_move()
    allocations = delegator_strategy.stake_allocations
    assert allocations.keys() == {556}
    assert allocations[556] == 0.0001