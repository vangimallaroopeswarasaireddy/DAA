from __future__ import annotations

import heapq
from dataclasses import dataclass
from typing import Dict, List, Tuple, Any


@dataclass
class EdgeState:
    from_node: str
    to_node: str
    base_cost: float
    capacity: float
    history: List[float]  # [t-1, t-2, t-3]


def edge_key(from_node: str, to_node: str) -> str:
    return f"{from_node}->{to_node}"


def compute_effective_cost(edge: EdgeState) -> float:
    h = edge.history
    stress_tax = (3 * h[0] + 2 * h[1] + 1 * h[2]) / 6.0
    return edge.base_cost + stress_tax


def build_graph(edges: List[dict]) -> Dict[str, List[str]]:
    graph: Dict[str, List[str]] = {}
    for e in edges:
        graph.setdefault(e["from_node"], []).append(e["to_node"])
    return graph


def shortest_path_by_dynamic_cost(
    nodes: List[str],
    edge_map: Dict[str, EdgeState],
    source: str,
    sink: str,
) -> Tuple[float, List[str]]:
    graph: Dict[str, List[Tuple[str, float]]] = {n: [] for n in nodes}

    for k, edge in edge_map.items():
        graph.setdefault(edge.from_node, []).append(
            (edge.to_node, compute_effective_cost(edge))
        )

    dist = {node: float("inf") for node in nodes}
    parent: Dict[str, str | None] = {node: None for node in nodes}
    dist[source] = 0.0

    pq: List[Tuple[float, str]] = [(0.0, source)]

    while pq:
        cur_dist, u = heapq.heappop(pq)
        if cur_dist > dist[u]:
            continue
        if u == sink:
            break

        for v, weight in graph.get(u, []):
            nd = cur_dist + weight
            if nd < dist[v]:
                dist[v] = nd
                parent[v] = u
                heapq.heappush(pq, (nd, v))

    if dist[sink] == float("inf"):
        return float("inf"), []

    path = []
    cur = sink
    while cur is not None:
        path.append(cur)
        cur = parent[cur]
    path.reverse()
    return dist[sink], path


def path_edges(path: List[str]) -> List[str]:
    return [edge_key(path[i], path[i + 1]) for i in range(len(path) - 1)]


def path_bottleneck(edge_map: Dict[str, EdgeState], edge_keys: List[str]) -> float:
    if not edge_keys:
        return 0.0
    return min(edge_map[k].capacity for k in edge_keys)


def shift_history_and_apply_hour_flow(edge_map: Dict[str, EdgeState], hour_flows: Dict[str, float]) -> None:
    for k, edge in edge_map.items():
        current_flow = hour_flows.get(k, 0.0)
        old_t1, old_t2, _old_t3 = edge.history
        edge.history = [current_flow, old_t1, old_t2]


def schedule_water_flow(payload: dict) -> dict:
    nodes: List[str] = payload["nodes"]
    edges: List[dict] = payload["edges"]
    source: str = payload["source"]
    sink: str = payload["sink"]
    total_demand: float = float(payload["total_demand"])
    hours: int = int(payload.get("hours", 24))

    edge_map: Dict[str, EdgeState] = {}
    for e in edges:
        k = edge_key(e["from_node"], e["to_node"])
        edge_map[k] = EdgeState(
            from_node=e["from_node"],
            to_node=e["to_node"],
            base_cost=float(e["base_cost"]),
            capacity=float(e["capacity"]),
            history=[0.0, 0.0, 0.0],
        )

    remaining = total_demand
    total_cost = 0.0
    delivered_total = 0.0
    schedule: List[dict] = []

    for hour in range(1, hours + 1):
        hour_flows: Dict[str, float] = {}
        hour_cost = 0.0

        hours_left = hours - hour + 1
        target_this_hour = remaining / hours_left if hours_left > 0 else 0.0
        remaining_for_this_hour = target_this_hour

        # Repeatedly route along cheapest currently available path.
        while remaining_for_this_hour > 1e-9:
            _, path = shortest_path_by_dynamic_cost(nodes, edge_map, source, sink)
            if not path:
                break

            p_edges = path_edges(path)
            if not p_edges:
                break

            bottleneck = path_bottleneck(edge_map, p_edges)
            if bottleneck <= 1e-9:
                break

            flow_to_send = min(bottleneck, remaining_for_this_hour)

            # Add flow to each edge in path
            for ek in p_edges:
                hour_flows[ek] = hour_flows.get(ek, 0.0) + flow_to_send

            remaining_for_this_hour -= flow_to_send

            # Temporarily reduce capacity so multiple path allocations this hour respect capacity
            for ek in p_edges:
                edge_map[ek].capacity -= flow_to_send

        # Compute hour result using pre-shift history
        hour_flow_records = []
        delivered_this_hour = 0.0

        # Sink inflow = delivered volume this hour
        for ek, flow in hour_flows.items():
            edge = edge_map[ek]
            eff_cost = compute_effective_cost(edge)
            edge_total = flow * eff_cost
            hour_cost += edge_total

            hour_flow_records.append(
                {
                    "from_node": edge.from_node,
                    "to_node": edge.to_node,
                    "flow": round(flow, 4),
                    "effective_cost": round(eff_cost, 4),
                    "edge_cost_total": round(edge_total, 4),
                }
            )

            if edge.to_node == sink:
                delivered_this_hour += flow

        total_cost += hour_cost
        delivered_total += delivered_this_hour
        remaining = max(0.0, total_demand - delivered_total)

        schedule.append(
            {
                "hour": hour,
                "delivered_this_hour": round(delivered_this_hour, 4),
                "hour_cost": round(hour_cost, 4),
                "flows": hour_flow_records,
            }
        )

        # Restore capacities for next hour
        for e in edges:
            k = edge_key(e["from_node"], e["to_node"])
            edge_map[k].capacity = float(e["capacity"])

        # Shift history for next hour
        shift_history_and_apply_hour_flow(edge_map, hour_flows)

    unmet = max(0.0, total_demand - delivered_total)

    note = None
    if unmet > 1e-9:
        note = (
            "Demand could not be fully satisfied within the given hourly capacities "
            "and scheduling horizon."
        )

    return {
        "status": "completed" if unmet <= 1e-9 else "partial",
        "total_cost": round(total_cost, 4),
        "delivered_volume": round(delivered_total, 4),
        "total_demand": round(total_demand, 4),
        "unmet_demand": round(unmet, 4),
        "hours": hours,
        "schedule": schedule,
        "note": note,
    }