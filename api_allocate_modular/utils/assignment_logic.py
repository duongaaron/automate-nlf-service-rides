import random
from collections import defaultdict
from utils.geo_utils import dist, route_cost
from utils.constants import driver_required_riders_to, driver_required_riders_back, FLEXIBLE_PLAN, BACK_HOME_PLAN, LUNCH_PLAN

def assign_whitelisted_groups(drivers, riders, driver_required_riders, rider_groups):
    assignments = defaultdict(list)
    unassigned_riders = set(riders)

    name_to_driver = {d.name.lower(): d for d in drivers}
    name_to_rider = {r.name.lower(): r for r in riders}
    remaining_drivers = set(drivers)

    normalized_rider_groups = [[n.lower() for n in group] for group in rider_groups]
    normalized_driver_required = {
        d.lower(): [r.lower() for r in group]
        for d, group in driver_required_riders.items()
    }

    for group in normalized_rider_groups:
        group_objs = [name_to_rider[name] for name in group if name in name_to_rider]
        if len(group_objs) < 2 or not all(r in unassigned_riders for r in group_objs):
            continue
        for driver in list(remaining_drivers):
            if driver.amount_seats >= len(group_objs):
                assignments[driver].extend(group_objs)
                for r in group_objs:
                    unassigned_riders.discard(r)
                driver.amount_seats -= len(group_objs)
                if driver.amount_seats == 0:
                    remaining_drivers.discard(driver)
                break

    for driver_name, rider_names in normalized_driver_required.items():
        driver = name_to_driver.get(driver_name)
        if not driver:
            continue
        group_objs = [name_to_rider[name] for name in rider_names if name in name_to_rider]
        if not group_objs or not all(r in unassigned_riders for r in group_objs):
            continue
        if driver.amount_seats >= len(group_objs):
            assignments[driver].extend(group_objs)
            for r in group_objs:
                unassigned_riders.discard(r)
            driver.amount_seats -= len(group_objs)
            if driver.amount_seats == 0:
                remaining_drivers.discard(driver)

    return assignments, list(remaining_drivers), unassigned_riders

def assign_riders_by_furthest_first(drivers, riders, destination, assignments=None):
    if assignments is None:
        assignments = defaultdict(list)
    for d in drivers:
        assignments.setdefault(d, [])

    shuffled_drivers = list(drivers)
    # Random = randomize driver and rider assignments
    # random.shuffle(shuffled_drivers)
    sorted_drivers = sorted(shuffled_drivers, key=lambda d: dist(d.long_lat_pair, destination), reverse=True)

    shuffled_riders = list(riders)
    # Random = randomize driver and rider assignments
    # random.shuffle(shuffled_riders)
    sorted_riders = sorted(shuffled_riders, key=lambda r: dist(r.long_lat_pair, destination), reverse=True)

    unassigned_riders = set()
    whitelist_names = set(d.lower() for d in driver_required_riders_to)

    for rider in sorted_riders:
        best_driver = None
        best_insert = None
        best_cost = float('inf')

        for driver in sorted_drivers:
            if driver.amount_seats <= 0 or driver.service_type != rider.service_type:
                continue
            route = assignments[driver]
            insert_positions = range(len(route)+1) if driver.name.lower() in whitelist_names else [len(route)]
            for pos in insert_positions:
                new_route = route[:pos] + [rider] + route[pos:]
                temp = dict(assignments)
                temp[driver] = new_route
                cost = sum(route_cost(d.long_lat_pair, temp[d], destination) for d in sorted_drivers)
                if cost < best_cost:
                    best_cost = cost
                    best_driver = driver
                    best_insert = pos

        if best_driver:
            assignments[best_driver].insert(best_insert, rider)
            best_driver.amount_seats -= 1
        else:
            unassigned_riders.add(rider)

    return assignments, unassigned_riders

def assign_from_church(drivers, riders, church_location, assignments=None):
    if assignments is None:
        assignments = defaultdict(list)
    for d in drivers:
        assignments.setdefault(d, [])

    sorted_drivers = sorted(drivers, key=lambda d: dist(d.long_lat_pair, church_location), reverse=True)
    sorted_riders = sorted(riders, key=lambda r: dist(r.long_lat_pair, church_location), reverse=True)

    unassigned_riders = set()
    whitelist_names = set(d.lower() for d in driver_required_riders_back)

    for rider in sorted_riders:
        best_driver = None
        best_insert = None
        best_cost = float('inf')

        for driver in sorted_drivers:
            if driver.amount_seats <= 0 or driver.plans != rider.plans:
                continue
            route = assignments[driver]
            insert_positions = range(len(route)+1) if driver.name.lower() in whitelist_names else [len(route)]
            for pos in insert_positions:
                new_route = route[:pos] + [rider] + route[pos:]
                temp = dict(assignments)
                temp[driver] = new_route
                cost = sum(route_cost(church_location, temp[d], d.long_lat_pair) for d in sorted_drivers)
                if cost < best_cost:
                    best_cost = cost
                    best_driver = driver
                    best_insert = pos

        if best_driver:
            assignments[best_driver].insert(best_insert, rider)
            best_driver.amount_seats -= 1
        else:
            unassigned_riders.add(rider)

    return assignments, unassigned_riders


def assign_flexible_plans_first(drivers, riders):
    flexible_drivers = [d for d in drivers if FLEXIBLE_PLAN in d.plans]
    non_flexible_drivers = [d for d in drivers if FLEXIBLE_PLAN not in d.plans]
    flexible_riders = [r for r in riders if FLEXIBLE_PLAN in r.plans]
    non_flexible_riders = [r for r in riders if FLEXIBLE_PLAN not in r.plans]

    drivers_by_plan = defaultdict(list)
    for d in non_flexible_drivers:
        drivers_by_plan[d.plans].append(d)

    riders_by_plan = defaultdict(list)
    for r in non_flexible_riders:
        riders_by_plan[r.plans].append(r)

    unassigned_flexible_riders = set(flexible_riders)
    assigned_flexible_drivers = set()

    for plan in [BACK_HOME_PLAN, LUNCH_PLAN]:
        rider_count = len(riders_by_plan[plan])
        seat_count = sum(d.amount_seats for d in drivers_by_plan[plan])
        needed_seats = rider_count - seat_count

        if needed_seats > 0:
            for d in flexible_drivers:
                if d in assigned_flexible_drivers:
                    continue
                d.plans = plan
                assigned_flexible_drivers.add(d)
                drivers_by_plan[plan].append(d)
                needed_seats -= d.amount_seats
                if needed_seats <= 0:
                    break

    for d in flexible_drivers:
        if d not in assigned_flexible_drivers:
            d.plans = BACK_HOME_PLAN
            drivers_by_plan[d.plans].append(d)

    remaining_flexible_riders = list(flexible_riders)

    for plan in [BACK_HOME_PLAN, LUNCH_PLAN]:
        rider_count = len(riders_by_plan[plan])
        seat_count = sum(d.amount_seats for d in drivers_by_plan[plan])
        extra_slots = seat_count - rider_count

        if extra_slots <= 0:
            continue

        assigned = 0
        for r in remaining_flexible_riders[:]:
            if assigned >= extra_slots:
                break
            r.plans = plan
            unassigned_flexible_riders.discard(r)
            remaining_flexible_riders.remove(r)
            assigned += 1

    assigned_flexible_riders = [r for r in flexible_riders if r not in unassigned_flexible_riders]
    all_unassigned_riders = non_flexible_riders + assigned_flexible_riders
    return all_unassigned_riders, unassigned_flexible_riders, drivers, riders