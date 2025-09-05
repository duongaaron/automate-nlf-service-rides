from collections import defaultdict
from typing import List, Tuple, Dict, Iterable
from ortools.constraint_solver import pywrapcp, routing_enums_pb2
import os, requests, numpy as np

import os, math, requests
import numpy as np
from typing import List, Tuple

API_KEY = os.environ["GOOGLE_API_KEY"]
URL = "https://routes.googleapis.com/distanceMatrix/v2:computeRouteMatrix"
headers = {
    "Content-Type": "application/json",
    "X-Goog-Api-Key": API_KEY,
    "X-Goog-FieldMask": "originIndex,destinationIndex,distanceMeters,condition",
}

from geopy.distance import geodesic
coords_to_dist = dict()

def dist(coord1, coord2):
    if (coord1, coord2) in coords_to_dist:
        return coords_to_dist[(coord1, coord2)]
    elif (coord2, coord1) in coords_to_dist:
        return coords_to_dist[(coord2, coord1)]

    miles = geodesic(coord1, coord2).miles
    coords_to_dist[(coord1, coord2)] = miles
    coords_to_dist[(coord2, coord1)] = miles
    return miles

def report_blocks(dist, V, R):
    import numpy as np
    S = slice(0, V)               # starts
    Rr = slice(V, V+R)            # riders
    D = slice(V+R, V+R+V)         # depots

    def stats(block, name):
        sub = dist[block]
        infs = np.isinf(sub).sum()
        total = sub.size
        print(f"{name}: inf {infs}/{total}")


    # Sums of each type of node to other type of node
    stats((S, Rr), "S->R") # Start to rider
    stats((Rr, Rr), "R->R") # Rider to rider
    stats((Rr, D),  "R->D") # Rider to depot
    stats((S, D),   "S->D") # Start to depot

def build_distance_matrix(
    drivers,                       # objs with .long_lat_pair = (lat, lon)
    riders,                        # objs with .long_lat_pair = (lat, lon)
    destinations: List[Tuple[float,float]],  # usually [dest]*V
    chunk_limit: int = 625,        # max origins * dests per request
    travel_mode: str = "DRIVE",
    use_duration: bool = False     # False=meters, True=seconds
) -> np.ndarray:

    V = len(drivers)
    R = len(riders)
    assert len(destinations) >= 1, "Provide at least one destination (duplicate per vehicle if desired)."

    # --- Build unified node list: [starts][riders][depots] ---
    coords: List[Tuple[float,float]] = []

    # starts
    for d in drivers:
        lat, lng = d.long_lat_pair
        if lat is None or lng is None:
            raise ValueError(f"Driver {getattr(d,'name',d)} has None coords")
        coords.append((float(lat), float(lng)))

    # riders
    for r in riders:
        lat, lng = r.long_lat_pair
        if lat is None or lng is None:
            raise ValueError(f"Rider {getattr(r,'name',r)} has None coords")
        coords.append((float(lat), float(lng)))

    # depots (one or many)
    for (lat, lng) in destinations:
        coords.append((float(lat), float(lng)))

    N = len(coords)
    if N == 0:
        return np.zeros((0, 0))

    # nodes_json = [latlng(lat, lng) for (lat, lng) in coords]

    # def call_matrix(origins_json, dests_json):
    #     payload = {
    #         "origins": origins_json,
    #         "destinations": dests_json,
    #         "travelMode": travel_mode,
    #     }
    #     resp = requests.post(URL, json=payload, headers=headers, timeout=60)
    #     if resp.status_code != 200:
    #         print("Routes API error:", resp.status_code, resp.text)
    #     resp.raise_for_status()
    #     return resp.json()

    # Prepare result matrix
    dist_m = np.full((N, N), np.inf, dtype=float)
    
    for i in range(N):
        for j in range(N):
            dist_m[i][j] = dist(coords[i], coords[j])
            
    for row in dist_m:
        print(row)

    # EPM_BUDGET = 3000              # adjust to your quota in Console (may be <3000)
    # elements_per_call = 625
    # calls_per_min = max(1, EPM_BUDGET // elements_per_call)
    # min_interval = 60.0 / calls_per_min

    # last_call = 0.0

    # Chunk by destinations so (N * chunk) <= chunk_limit
    # max_dest = max(1, chunk_limit // N)
    # for d0 in range(0, N, max_dest):
    #     now = time.time()
    #     wait = min_interval - (now - last_call)
    #     if wait > 0:
    #         time.sleep(wait)
    #     last_call = time.time()
    #     d1 = min(N, d0 + max_dest)
    #     rows = call_matrix(nodes_json, nodes_json[d0:d1])

    #     # rows is a flat list; each element has originIndex and (chunk-local) destinationIndex
    #     for e in rows:
    #         oi = e["originIndex"]
    #         di = e["destinationIndex"] + d0
    #         cond = e.get("condition")
    #         if cond == "ROUTE_NOT_FOUND":
    #             # Log the exact coords that failed
    #             print(f"[ROUTE_NOT_FOUND] oi={oi}→di={di} | "
    #                   f"{coords[oi]} → {coords[di]}")
    #             continue

           
    #         dist_m[oi, di] = float(e.get("distanceMeters", np.inf))

    # Zero self-arcs
    np.fill_diagonal(dist_m, 0.0)

    # for i in range(N):
    #     for j in range(N):
    #         if same_point(coords[i], coords[j]):
    #             dist_m[i, j] = 0.0

    # Final audit: report any remaining infs (pairs never filled)
    inf_locs = np.argwhere(~np.isfinite(dist_m))
    if inf_locs.size:
        print(f"[WARN] {inf_locs.shape[0]} cells are still inf (unreachable or missing). Examples:")
        for (oi, di) in inf_locs[:10]:
            print(f"  {oi}→{di} : {coords[oi]} → {coords[di]}")
        if inf_locs.shape[0] > 10:
            print("  ... (truncated)")

    return dist_m

def build_vrp(
    drivers,
    riders,
    destinations,
    rider_groups=None,                 # list[list[int]] rider indices that must share same car
    allow_skips=True,
    skip_penalty=1e6,                  # large penalty discouraging skips
    service_allowed=None,              # {rider_idx: [vehicle indices allowed]}
):
    """
    Returns routing, manager, data structures ready to Solve().
    riders indices refer to position in `riders` list.
    vehicle indices refer to position in `drivers` list.
    """

    # --- Build node list & indices ---
    # Layout:
    #   [0 .. V-1]         => vehicle start nodes (one per driver)
    #   [V .. V+R-1]       => rider nodes
    #   [V+R .. V+R+V-1]   => per-vehicle depots (end nodes)
    V = len(drivers)
    R = len(riders)

    start_offset  = 0
    rider_offset  = V
    depot_offset  = V + R
    node_count    = depot_offset + V      # <-- FIX: V per-vehicle depots

    # starts
    index_to_name = {}
    name_to_index = {}
    index_to_coord = [None] * node_count
    # starts
    for i, driver in enumerate(drivers):
        idx = start_offset + i
        index_to_coord[idx] = driver.long_lat_pair
        index_to_name[idx] = driver.name
        name_to_index[driver.name] = idx

    # riders
    for i, rider in enumerate(riders):
        idx = rider_offset + i
        index_to_coord[idx] = rider.long_lat_pair
        index_to_name[idx] = rider.name
        name_to_index[rider.name] = idx

    # depots: there must be exactly V of these (one per vehicle)
    assert len(destinations) == V, f"destinations must have length == number of drivers (got {len(destinations)} vs V={V})"

    # depots
    for i, destination in enumerate(destinations):
        idx = depot_offset + i
        index_to_coord[idx] = destination
        index_to_name[idx] = f"Depot[{i}]"

    
    manager = pywrapcp.RoutingIndexManager(
        node_count,
        V,
        [start_offset + v for v in range(V)],        # starts
        [depot_offset + v for v in range(V)],        # ends (per-vehicle depot)
    )
    routing = pywrapcp.RoutingModel(manager)

    # --- Distance matrix built from EXACT node order
    dist_matrix = build_distance_matrix(drivers, riders, destinations)

    # Optional: quick diagnostics
    report_blocks(dist_matrix, V, R)

    # ---- Transit (distance) ----
    def transit_cb(from_index, to_index):
        i = manager.IndexToNode(from_index)
        j = manager.IndexToNode(to_index)
        c = dist_matrix[i][j]
        return 10**12 if not np.isfinite(c) else int(c)  # meters as int
    transit_cb_idx = routing.RegisterTransitCallback(transit_cb)
    routing.SetArcCostEvaluatorOfAllVehicles(transit_cb_idx)

    # ---- Capacity dimension (seat constraints) ----
    demands = [0] * node_count
    for i in range(R):
        demands[rider_offset + i] = 1  # each rider consumes 1 seat

    def demand_cb(index):
        node = manager.IndexToNode(index)
        return demands[node]

    demand_cb_idx = routing.RegisterUnaryTransitCallback(demand_cb)
    routing.AddDimension(
        demand_cb_idx,
        0,          # no slack
        10**9,      # big cap; per-vehicle bounds below
        True,
        "Capacity",
    )
    cap_dim = routing.GetDimensionOrDie("Capacity")
    for v, d in enumerate(drivers):
        cap_dim.CumulVar(routing.Start(v)).SetRange(0, d.amount_seats)
        cap_dim.CumulVar(routing.End(v)).SetRange(0, d.amount_seats)

    # ---- Allow skipping riders (correct handling) ----
    if allow_skips:
        # pick a big penalty relative to your arc costs (you’re using meters)
        finite = np.isfinite(dist_matrix)
        max_arc = int(dist_matrix[finite].max()) if finite.any() else 0
        big_penalty = max(10**9, 100 * max_arc)  # e.g., 100x worst hop
        for i in range(R):
            node = rider_offset + i
            routing.AddDisjunction([manager.NodeToIndex(node)], big_penalty)
    else:
        # Riders are required: DON'T add any disjunctions
        pass

    # ---- Service-type / allowed-vehicles constraints (optional) ----
    # ---- SAME service_type constraint ----
    # Build allowed vehicle lists per rider when not provided
    if service_allowed is None:
        # map service_type -> list of vehicle indices
        type_to_vehicles = {}
        for v, d in enumerate(drivers):
            t = getattr(d, "service_type", None)
            type_to_vehicles.setdefault(t, []).append(v)

        service_allowed = {}
        for ridx, r in enumerate(riders):
            rt = getattr(r, "service_type", None)
            allowed_vs = type_to_vehicles.get(rt, [])
            service_allowed[ridx] = allowed_vs

    # Apply allowed vehicles per rider index
    for ridx, allowed_vs in service_allowed.items():
        index = manager.NodeToIndex(rider_offset + ridx)
        if allowed_vs:
            routing.SetAllowedVehiclesForIndex(list(allowed_vs), index)
        else:
            # No compatible vehicle:
            #  - if allow_skips=True, keep the disjunction so it can be dropped.
            #  - if allow_skips=False, you likely want to fail fast:
            if not allow_skips:
                raise ValueError(
                    f"Rider {getattr(riders[ridx], 'name', ridx)} "
                    f"has no vehicle with matching service_type={getattr(riders[ridx],'service_type',None)}"
                )

    # ---- “Same car” groups (must-link sets) ----
    if rider_groups:
        for group in rider_groups:
            indices = [manager.NodeToIndex(rider_offset + i) for i in group]
            base_vehicle = routing.VehicleVar(indices[0])
            for idx in indices[1:]:
                routing.solver().Add(routing.VehicleVar(idx) == base_vehicle)

    # ---- Search parameters ----
    search_params = pywrapcp.DefaultRoutingSearchParameters()
    search_params.first_solution_strategy = routing_enums_pb2.FirstSolutionStrategy.PARALLEL_CHEAPEST_INSERTION
    search_params.local_search_metaheuristic = routing_enums_pb2.LocalSearchMetaheuristic.GUIDED_LOCAL_SEARCH
    search_params.time_limit.FromSeconds(300)     # give it more time
    search_params.log_search = False               # progress logs

    return routing, manager, search_params, index_to_coord, dist_matrix, index_to_name, name_to_index
def solve_and_extract(routing, manager, search_params):
    solution = routing.SolveWithParameters(search_params)
    if not solution:
        return None

    routes = []
    obj = solution.ObjectiveValue()
    for v in range(routing.vehicles()):
        idx = routing.Start(v)
        route_nodes = []
        load_vals = []
        while not routing.IsEnd(idx):
            node = manager.IndexToNode(idx)
            route_nodes.append(node)
            idx = solution.Value(routing.NextVar(idx))
        route_nodes.append(manager.IndexToNode(idx))  # end (depot)
        routes.append(route_nodes)
    return obj, routes

def print_solution_vrp(
    routing,
    manager,
    solution,
    drivers,
    riders,
    destinations,
    index_to_coord,
    dist_matrix,
    index_to_name,
    label_coords=True,
):
    """
    Pretty-print the VRP solution produced by OR-Tools for your node layout.
    - Distances are summed from dist_matrix (not the scaled objective units).
    - Load is read from the 'Capacity' dimension (1 per rider).
    - Dropped riders are listed at the end if allow_skips=True.
    """
    if solution is None:
        print("No solution.")
        return

    V = len(drivers)
    R = len(riders)
    start_offset = 0
    rider_offset = V
    depot_offset = V + R

    def coord_str(n):
        lat, lon = index_to_coord[n]
        return f"({lat:.6f}, {lon:.6f})"

    cap_dim = routing.GetDimensionOrDie("Capacity")

    print(f"Objective (scaled cost units): {solution.ObjectiveValue()}")
    total_dist = 0.0
    total_load = 0

    for v in range(routing.vehicles()):
        if not routing.IsVehicleUsed(solution, v):
            continue

        idx = routing.Start(v)
        route_nodes = [idx]
        # Build the route sequence of indices
        while not routing.IsEnd(idx):
            idx = solution.Value(routing.NextVar(idx))
            route_nodes.append(idx)

        # Print header
        print(f"\nRoute for vehicle {v}:")
        route_dist = 0.0

        # Walk the route and print hops
        for step, (a, b) in enumerate(zip(route_nodes[:-1], route_nodes[1:])):
            an = manager.IndexToNode(a)
            bn = manager.IndexToNode(b)

            lbl_a = index_to_name.get(an, f"Node[{an}]")
            lbl_b = index_to_name.get(bn, f"Node[{bn}]")

            # cumulative load at node 'a'
            load_a = solution.Value(cap_dim.CumulVar(a))
            # distance a->b from your matrix (guard inf)
            hop = float(dist_matrix[an][bn])
            if not (hop == hop):  # NaN guard
                hop = float("inf")

            if label_coords:
                lbl_a += f" {coord_str(an)}"

            print(f"  {lbl_a} -> {lbl_b}  dist={hop:.1f} load={load_a}")

            if hop != float("inf"):
                route_dist += hop

        # load at the end node
        end_idx = route_nodes[-1]
        load_end = solution.Value(cap_dim.CumulVar(end_idx))
        total_dist += route_dist
        total_load += load_end

        print(f"Distance of route {v}: {route_dist:.1f} (same units as dist_matrix)")
        print(f"Load of route {v}: {load_end}")

    print(f"\nTotal distance of all routes: {total_dist:.1f}")
    print(f"Total load of all routes: {total_load}")

    # ---- Dropped riders (skipped via disjunction) ----
    # A node is dropped if NextVar(index) == index in the solution.
   # ---- Dropped riders (skipped via disjunction) ----
    dropped_idx = []
    for ridx in range(R):
        global_node = rider_offset + ridx
        index = manager.NodeToIndex(global_node)
        if solution.Value(routing.NextVar(index)) == index:
            dropped_idx.append(ridx)

    dropped_names = []
    if dropped_idx:
        dropped_names = [riders[i].name for i in dropped_idx]
        print(f"\nDropped riders (count={len(dropped_idx)}): {dropped_names}")
    else:
        print("\nNo riders dropped.")

    # ---- Unused vehicles (no route started) ----
    unused = [v for v in range(routing.vehicles()) if not routing.IsVehicleUsed(solution, v)]
    unused_driver_names = []
    if unused:
        unused_driver_names = [drivers[v].name for v in unused]
        print(f"Unused vehicles (count={len(unused)}): {unused_driver_names}")
    else:
        print("All vehicles used.")

    return dropped_names, unused_driver_names

def solve_with_driver_fallback(drivers, riders, destinations):
    # --- Pass 1 ---
    routing, manager, params, idx2coord, dist, idx2name, name2idx = build_vrp(
        drivers, riders, destinations,
        allow_skips=False  # if you want everyone served
    )
    sol = routing.SolveWithParameters(params)
    if not sol:
        return None  # infeasible

    # Who is used?
    used_flags = [routing.IsVehicleUsed(sol, v) for v in range(len(drivers))]
    used_drivers   = [d for v, d in enumerate(drivers) if used_flags[v]]
    unused_drivers = [d for v, d in enumerate(drivers) if not used_flags[v]]

    # If everyone is used, you’re done
    if not unused_drivers:
        data = {
            "assignments_to": build_assignments(routing, manager, sol, drivers, riders),
            "unassigned_riders_to": [],
            "drivers": drivers, "riders": riders,
        }
        return data

    # --- Pass 2: convert unused drivers -> riders, keep only used vehicles ---
    # Make Rider objects for unused drivers (same coords/name; demand=1)
    # If your Rider class needs service_type, etc., copy those too.
    def driver_to_rider(d):
        r = type(riders[0]).__new__(type(riders[0]))  # same class as your Rider
        # minimal fields you actually use:
        r.name = d.name
        r.long_lat_pair = d.long_lat_pair
        r.pickup_location = getattr(d, "pickup_location", "")
        r.service_type = getattr(d, "service_type", None)
        return r

    fallback_riders = riders + [driver_to_rider(d) for d in unused_drivers]

    # destinations must match vehicle count (per-vehicle depot)
    fallback_destinations = [destinations[0]] * len(used_drivers)

    routing2, manager2, params2, idx2coord2, dist2, idx2name2, name2idx2 = build_vrp(
        used_drivers, fallback_riders, fallback_destinations,
        allow_skips=False
    )
    sol2 = routing2.SolveWithParameters(params2)
    if not sol2:
        # If you really want a result, you could allow_skips=True here as a fallback.
        return None

    assignments2 = build_assignments(routing2, manager2, sol2, used_drivers, fallback_riders)
    data = {
        "assignments_to": assignments2,
        "unassigned_riders_to": [],  # with allow_skips=False, all should be served
        "drivers": used_drivers,
        "riders": fallback_riders,
    }
    return data

    
def build_assignments(routing, manager, solution, drivers, riders):
    """
    Returns {driver_name: [rider_name, ...]} using the OR-Tools solution.
    
    - drivers: list of Driver objects (with .name)
    - riders: list of Rider objects (with .name)
    - rider_offset: global index offset where riders start in your model
    """
    assignments = defaultdict(list)

    rider_offset = len(drivers)

    for v in range(len(drivers)):   # one vehicle per driver
        index = routing.Start(v)
        driver = drivers[v]

        while not routing.IsEnd(index):
            node = manager.IndexToNode(index)
            # check if this node corresponds to a rider
            if rider_offset <= node < rider_offset + len(riders):
                rider_idx = node - rider_offset
                assignments[driver].append(riders[rider_idx])

            index = solution.Value(routing.NextVar(index))
    for driver in assignments:
        print(driver.name)
        for rider in assignments[driver]:
            print(rider.name)

        print("\n\n")
    return assignments

def solve(drivers, riders, destinations):
    routing, manager, params, idx2coord, dist, index_to_name, name_to_index = build_vrp(
        drivers, riders, destinations,
        allow_skips=True,
    )
    solution = routing.SolveWithParameters(params)

    dropped_riders, dropped_drivers = print_solution_vrp(
        routing, manager, solution, drivers, riders, destinations,
        idx2coord, dist, index_to_name
    )

    assignments = build_assignments(routing, manager, solution, drivers, riders)

    # IMPORTANT: return a dict with the keys ExcelExporter expects
    data = {
        "assignments_to": assignments,          # {Driver -> [Rider, ...]}
        "unassigned_riders_to": dropped_riders, # see Fix 2 below
        "oc_people_w_invalid_address": [],      # supply if you have it
        # optionally include lists so you can rebuild lookups if needed:
        "drivers": drivers,
        "riders": riders,
    }
    return data

# def solve(drivers, riders, destinations):
#     data = solve_with_driver_fallback(drivers, riders, destinations)

#     # If you still want to dump names to stdout:
#     if data and "assignments_to" in data:
#         assignments = data["assignments_to"]
#         for drv, rlist in assignments.items():
#             print(f"{drv.name}: {[r.name for r in rlist]}")

#     return data