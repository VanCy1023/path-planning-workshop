"""Planning core for the revision experiments (RAAS-R2).

Compared with the submitted version:
  * RRT* is a real sampling planner (steer + rewiring + goal bias) implemented
    with vectorised nearest-neighbour queries; the previous version only drew
    random waypoints, slept 1.5 s and returned max_iter as the node count.
  * Obstacles are hard-blocked at RISK_OBSTACLE (the tensors encode buildings
    as 100); the previous 1e5 threshold never triggered.
  * All stochastic components use a seeded RNG.
  * RC_norm = RC / PL makes risk comparable across different maps.
"""

from __future__ import annotations

import heapq
import math
import random
import time

import numpy as np

RISK_OBSTACLE = 0.995


class PathPlanners:
    def __init__(self, risk_tensor, grid_res=2.0, seed=0):
        self.grid = risk_tensor
        self.nx, self.ny, self.nz = risk_tensor.shape
        self.res = float(grid_res)
        self.rng = random.Random(seed)

        self.dirs = []
        for dx in (-1, 0, 1):
            for dy in (-1, 0, 1):
                for dz in (-1, 0, 1):
                    if dx or dy or dz:
                        self.dirs.append((dx, dy, dz, math.sqrt(dx * dx + dy * dy + dz * dz)))

        free = self.grid < RISK_OBSTACLE
        self.free_share = float(free.mean())
        self.C_map_avg = float(self.grid[free].mean()) if free.any() else 1.0
        self.V_cens = []
        self.C_avg_cens = self.C_map_avg

    def _ensure_centroids(self):
        if self.V_cens:
            return
        free = self.grid < RISK_OBSTACLE
        if not np.any(free):
            return
        threshold = np.percentile(self.grid[free], 5)
        indices = np.argwhere((self.grid <= threshold) & free)
        if len(indices) == 0:
            return
        k = min(5, len(indices))
        picks = self.rng.sample(range(len(indices)), k)
        self.V_cens = [tuple(int(v) for v in indices[i]) for i in picks]
        self.C_avg_cens = float(np.mean([self.grid[c] for c in self.V_cens]))

    # ------------------------------------------------------------------ utils
    def is_valid(self, x, y, z):
        return (0 <= x < self.nx and 0 <= y < self.ny and 0 <= z < self.nz
                and self.grid[x, y, z] < RISK_OBSTACLE)

    def _reconstruct(self, came_from, start, goal):
        if goal not in came_from:
            return []
        path, cur = [], goal
        while cur in came_from:
            path.append(cur)
            cur = came_from[cur]
        path.append(start)
        path.reverse()
        return path

    # --------------------------------------------------------------- Dijkstra
    def dijkstra(self, start, goal):
        t0 = time.time()
        pq, g = [(0.0, start)], {start: 0.0}
        came_from, closed = {}, set()
        expanded = 0
        grid, res, dirs, ok = self.grid, self.res, self.dirs, self.is_valid
        while pq:
            cg, cur = heapq.heappop(pq)
            if cur in closed:
                continue
            closed.add(cur)
            expanded += 1
            if cur == goal:
                break
            if cg > g.get(cur, float("inf")):
                continue
            cx, cy, cz = cur
            for dx, dy, dz, dist in dirs:
                nb = (cx + dx, cy + dy, cz + dz)
                if not ok(*nb):
                    continue
                ng = cg + dist * res * (1.0 + grid[nb])
                if ng < g.get(nb, float("inf")):
                    came_from[nb] = cur
                    g[nb] = ng
                    heapq.heappush(pq, (ng, nb))
        return self._reconstruct(came_from, start, goal), time.time() - t0, expanded

    # --------------------------------------------------------------------- A*
    def astar_distance(self, start, goal):
        """Classical A*: geometric length only, risk ignored (risk-blind baseline)."""
        t0 = time.time()
        pq, g, closed = [(0.0, start)], {start: 0.0}, set()
        came_from = {}
        expanded = 0
        res, dirs, ok = self.res, self.dirs, self.is_valid
        gx, gy, gz = goal
        while pq:
            _, cur = heapq.heappop(pq)
            if cur in closed:
                continue
            closed.add(cur)
            expanded += 1
            if cur == goal:
                break
            cg = g[cur]
            cx, cy, cz = cur
            for dx, dy, dz, dist in dirs:
                nb = (cx + dx, cy + dy, cz + dz)
                if nb in closed or not ok(*nb):
                    continue
                ng = cg + dist * res
                if ng < g.get(nb, float("inf")):
                    came_from[nb] = cur
                    g[nb] = ng
                    h = math.sqrt((nb[0] - gx) ** 2 + (nb[1] - gy) ** 2 + (nb[2] - gz) ** 2) * res
                    heapq.heappush(pq, (ng + h, nb))
        return self._reconstruct(came_from, start, goal), time.time() - t0, expanded

    def risk_astar(self, start, goal):
        t0 = time.time()
        pq, g, closed = [(0.0, start)], {start: 0.0}, set()
        came_from = {}
        expanded = 0
        grid, res, dirs, ok = self.grid, self.res, self.dirs, self.is_valid
        gx, gy, gz = goal
        while pq:
            _, cur = heapq.heappop(pq)
            if cur in closed:
                continue
            closed.add(cur)
            expanded += 1
            if cur == goal:
                break
            cg = g[cur]
            cx, cy, cz = cur
            for dx, dy, dz, dist in dirs:
                nb = (cx + dx, cy + dy, cz + dz)
                if nb in closed or not ok(*nb):
                    continue
                ng = cg + dist * res * (1.0 + grid[nb])
                if ng < g.get(nb, float("inf")):
                    came_from[nb] = cur
                    g[nb] = ng
                    h = math.sqrt((nb[0] - gx) ** 2 + (nb[1] - gy) ** 2 + (nb[2] - gz) ** 2) * res
                    heapq.heappush(pq, (ng + h, nb))
        return self._reconstruct(came_from, start, goal), time.time() - t0, expanded

    # ------------------------------------------------------------- Weighted-A*
    def wa_star(self, start, goal, w=2.0):
        t0 = time.time()
        pq, g, closed = [(0.0, start)], {start: 0.0}, set()
        came_from = {}
        expanded = 0
        grid, res, dirs, ok = self.grid, self.res, self.dirs, self.is_valid
        gx, gy, gz = goal
        while pq:
            _, cur = heapq.heappop(pq)
            if cur in closed:
                continue
            closed.add(cur)
            expanded += 1
            if cur == goal:
                break
            cg = g[cur]
            cx, cy, cz = cur
            for dx, dy, dz, dist in dirs:
                nb = (cx + dx, cy + dy, cz + dz)
                if nb in closed or not ok(*nb):
                    continue
                ng = cg + dist * res * (1.0 + grid[nb])
                if ng < g.get(nb, float("inf")):
                    came_from[nb] = cur
                    g[nb] = ng
                    h = math.sqrt((nb[0] - gx) ** 2 + (nb[1] - gy) ** 2 + (nb[2] - gz) ** 2) * res
                    heapq.heappush(pq, (ng + w * h, nb))
        return self._reconstruct(came_from, start, goal), time.time() - t0, expanded

    # ------------------------------------------------------------- Cost-A*
    def cost_astar(self, start, goal, w=1.0):
        """A* whose heuristic mixes the goal direction with the nearest
        low-risk cluster centroid (the 'cost-aware' heuristic of the paper)."""
        self._ensure_centroids()
        t0 = time.time()
        pq, g, closed = [(0.0, start)], {start: 0.0}, set()
        came_from = {}
        expanded = 0
        grid, res, dirs, ok = self.grid, self.res, self.dirs, self.is_valid
        gx, gy, gz = goal
        cens = np.asarray(self.V_cens, dtype=float) if self.V_cens else None
        while pq:
            _, cur = heapq.heappop(pq)
            if cur in closed:
                continue
            closed.add(cur)
            expanded += 1
            if cur == goal:
                break
            cg = g[cur]
            cx, cy, cz = cur
            for dx, dy, dz, dist in dirs:
                nb = (cx + dx, cy + dy, cz + dz)
                if nb in closed or not ok(*nb):
                    continue
                ng = cg + dist * res * (1.0 + grid[nb])
                if ng < g.get(nb, float("inf")):
                    came_from[nb] = cur
                    g[nb] = ng
                    vec = np.array([gx - nb[0], gy - nb[1], gz - nb[2]], dtype=float)
                    d_goal = float(np.linalg.norm(vec))
                    h = d_goal * res
                    if cens is not None and len(cens):
                        d2 = ((cens - np.asarray(nb, dtype=float)) ** 2).sum(axis=1)
                        j = int(np.argmin(d2))
                        d_cen = math.sqrt(float(d2[j]))
                        h = max(h, d_cen * res)
                    heapq.heappush(pq, (ng + w * h, nb))
        return self._reconstruct(came_from, start, goal), time.time() - t0, expanded

    # -------------------------------------------------------------- EDA-CostA*
    def eda_cost_astar(self, start, goal, n_iter=2, m=3, kappa=2):
        t0 = time.time()
        pop, total = [], 0
        for _ in range(m):
            path, _, n = self.cost_astar(start, goal)
            total += n
            if path:
                pop.append(path)
        if not pop:
            return [], time.time() - t0, total

        def fitness(p):
            pl = rc = 0.0
            for a, b in zip(p, p[1:]):
                pl += math.sqrt((a[0] - b[0]) ** 2 + (a[1] - b[1]) ** 2 + (a[2] - b[2]) ** 2) * self.res
                rc += self.grid[b]
            return 0.7 * rc + 0.3 * pl

        for _ in range(n_iter):
            pop.sort(key=fitness)
            elite = pop[:kappa]
            offspring = []
            while len(elite) + len(offspring) < m:
                parent = self.rng.choice(elite)
                if len(parent) <= 15:
                    break
                i1 = self.rng.randint(2, len(parent) - 10)
                i2 = min(len(parent) - 1, i1 + self.rng.randint(3, 8))
                sub, _, n = self.cost_astar(parent[i1], parent[i2])
                total += n
                if sub:
                    offspring.append(parent[:i1] + sub + parent[i2 + 1:])
            pop = elite + offspring
            pop.sort(key=fitness)
        return (pop[0] if pop else []), time.time() - t0, total

    # ------------------------------------------------------------------- RRT*
    def rrt_star(self, start, goal, max_iter=4000, step_cells=5.0, rewire_radius=10.0):
        """Anytime RRT* with vectorised nearest-neighbour and rewiring."""
        t0 = time.time()
        rng = self.rng
        cap = max_iter + 2
        pos = np.zeros((cap, 3), dtype=float)
        cost = np.full(cap, np.inf)
        parent = np.full(cap, -1, dtype=int)
        pos[0] = start
        cost[0] = 0.0
        n = 1
        goal = np.asarray(goal, dtype=float)
        res, grid = self.res, self.grid

        def edge(a, b):
            length = float(np.linalg.norm(b - a))
            steps = max(1, int(math.ceil(length)))
            total = 0.0
            for i in range(1, steps + 1):
                q = a + (b - a) * (i / steps)
                x, y, z = int(round(q[0])), int(round(q[1])), int(round(q[2]))
                if not (0 <= x < self.nx and 0 <= y < self.ny and 0 <= z < self.nz):
                    return 0.0, False
                v = grid[x, y, z]
                if v >= RISK_OBSTACLE:
                    return 0.0, False
                total += length / steps * res * (1.0 + v)
            return total, True

        best_path, best_cost_to_goal = [], np.inf
        for _ in range(max_iter):
            if n >= cap:
                break
            target = goal if rng.random() < 0.1 else np.array([
                rng.uniform(0, self.nx - 1), rng.uniform(0, self.ny - 1), rng.uniform(0, self.nz - 1)])
            d = np.linalg.norm(pos[:n] - target, axis=1)
            i = int(np.argmin(d))
            vec = target - pos[i]
            length = float(np.linalg.norm(vec))
            if length < 1e-9:
                continue
            new = pos[i] + vec / length * min(step_cells, length)
            base, ok = edge(pos[i], new)
            if not ok:
                continue
            near = np.where(np.linalg.norm(pos[:n] - new, axis=1) <= rewire_radius)[0]
            best_parent, best = i, cost[i] + base
            for j in near:
                c, ok2 = edge(pos[j], new)
                if ok2 and cost[j] + c < best:
                    best_parent, best = int(j), cost[j] + c
            pos[n] = new
            cost[n] = best
            parent[n] = best_parent
            idx = n
            n += 1
            for j in near:
                c, ok2 = edge(new, pos[j])
                if ok2 and best + c < cost[j]:
                    parent[j] = idx
                    cost[j] = best + c
            if float(np.linalg.norm(new - goal)) <= step_cells:
                c, ok2 = edge(new, goal)
                if ok2 and best + c < best_cost_to_goal:
                    best_cost_to_goal = best + c
                    order, cur = [], idx
                    while cur != -1:
                        order.append(tuple(int(round(v)) for v in pos[cur]))
                        cur = int(parent[cur])
                    best_path = list(reversed(order)) + [tuple(int(round(v)) for v in goal)]
        return best_path, time.time() - t0, n

    # -------------------------------------------------------------------- PSO
    def pso(self, start, goal, particles=48, iterations=140, n_waypoints=14):
        """Particle swarm optimisation over offsets from the straight corridor.

        Each particle encodes lateral and vertical offsets of n_waypoints control
        points around the start-goal line, so the swarm explores risk-avoiding
        detours instead of the whole 3-D domain.  The cost is the same
        length-plus-risk integral used by A*, plus a large collision penalty.
        """
        t0 = time.time()
        rng = self.rng
        start = np.asarray(start, dtype=float)
        goal = np.asarray(goal, dtype=float)
        line = np.linspace(start, goal, n_waypoints + 2)[1:-1]
        dim = n_waypoints * 3
        span = np.tile(np.array([26.0, 26.0, 8.0]), n_waypoints)

        def to_points(vec):
            pts = line + vec.reshape(-1, 3)
            pts[:, 0] = np.clip(pts[:, 0], 1, self.nx - 2)
            pts[:, 1] = np.clip(pts[:, 1], 1, self.ny - 2)
            pts[:, 2] = np.clip(pts[:, 2], 1, self.nz - 2)
            for k in range(len(pts)):
                x, y, z = np.rint(pts[k]).astype(int)
                if self.grid[x, y, z] >= RISK_OBSTACLE:
                    for dz in range(1, 10):
                        z2 = min(z + dz, self.nz - 2)
                        if self.grid[x, y, z2] < RISK_OBSTACLE:
                            pts[k, 2] = z2
                            break
            return pts

        def segment_cost(a, b):
            length = float(np.linalg.norm(b - a))
            steps = max(1, int(math.ceil(length)))
            cost, penalty = 0.0, 0.0
            for i in range(1, steps + 1):
                q = a + (b - a) * (i / steps)
                x, y, z = int(round(q[0])), int(round(q[1])), int(round(q[2]))
                if not (0 <= x < self.nx and 0 <= y < self.ny and 0 <= z < self.nz):
                    penalty += 2000.0
                    continue
                v = self.grid[x, y, z]
                if v >= RISK_OBSTACLE:
                    penalty += 2000.0
                else:
                    cost += length / steps * self.res * (1.0 + v)
            return cost, penalty

        def evaluate(vec):
            pts = [start] + list(to_points(vec)) + [goal]
            cost = 0.0
            for a, b in zip(pts[:-1], pts[1:]):
                c, p = segment_cost(np.asarray(a, float), np.asarray(b, float))
                cost += c + p
            turn = 0.0
            for a, b, c in zip(pts[:-2], pts[1:-1], pts[2:]):
                u, v = np.asarray(b) - np.asarray(a), np.asarray(c) - np.asarray(b)
                nu, nv = np.linalg.norm(u), np.linalg.norm(v)
                if nu > 1e-9 and nv > 1e-9:
                    turn += 1.0 - float(np.dot(u, v) / (nu * nv))
            return cost + 5.0 * turn

        pos = np.zeros((particles, dim))
        vel = np.zeros((particles, dim))
        for i in range(particles):
            pos[i] = np.clip(rng.gauss(0, 8), -span, span) if i else np.zeros(dim)
            vel[i] = np.array([rng.uniform(-2.0, 2.0) for _ in range(dim)])
        best_pos = pos.copy()
        best_val = np.array([evaluate(x) for x in pos])
        g_idx = int(np.argmin(best_val))
        g_pos, g_val = best_pos[g_idx].copy(), float(best_val[g_idx])
        w, c1, c2 = 0.72, 1.5, 1.5

        for _ in range(iterations):
            r1 = np.array([rng.random() for _ in range(dim)])
            r2 = np.array([rng.random() for _ in range(dim)])
            vel = w * vel + c1 * r1 * (best_pos - pos) + c2 * r2 * (g_pos - pos)
            vel = np.clip(vel, -6.0, 6.0)
            pos = np.clip(pos + vel, -span, span)
            for i in range(particles):
                val = evaluate(pos[i])
                if val < best_val[i]:
                    best_val[i], best_pos[i] = val, pos[i].copy()
                    if val < g_val:
                        g_val, g_pos = float(val), pos[i].copy()

        pts = [start] + list(to_points(g_pos)) + [goal]
        path = [(int(round(q[0])), int(round(q[1])), int(round(q[2]))) for q in pts]
        clean = [path[0]]
        for q in path[1:]:
            if q != clean[-1]:
                clean.append(q)
        return clean, time.time() - t0, particles * iterations

    # ----------------------------------------------------------------- metrics
    def calc_metrics(self, path):
        out = dict(success=False, pl_m=float("nan"), rc=float("nan"), rc_norm=float("nan"),
                   sm_max_deg=float("nan"), sm_sum_deg=float("nan"), steps=0)
        if not path or len(path) < 2:
            return out
        pts = np.asarray(path, dtype=float)
        pl = float(np.linalg.norm(np.diff(pts, axis=0), axis=1).sum() * self.res)
        dense = []
        for a, b in zip(pts[:-1], pts[1:]):
            k = max(1, int(round(np.linalg.norm(b - a))))
            for m in range(k):
                dense.append(a + (b - a) * (m / k))
        rc = float(sum(self.grid[int(round(p[0])), int(round(p[1])), int(round(p[2]))] for p in dense) * self.res)
        turns = []
        for a, b, c in zip(pts[:-2], pts[1:-1], pts[2:]):
            u, v = b - a, c - b
            nu, nv = np.linalg.norm(u), np.linalg.norm(v)
            if nu > 1e-9 and nv > 1e-9:
                turns.append(math.degrees(math.acos(float(np.clip(np.dot(u, v) / (nu * nv), -1.0, 1.0)))))
        out.update(success=bool(path), pl_m=pl, rc=rc, rc_norm=rc / pl if pl else float("nan"),
                   sm_max_deg=max(turns) if turns else 0.0, sm_sum_deg=float(sum(turns)), steps=len(dense))
        return out
