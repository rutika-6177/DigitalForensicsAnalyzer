from collections import deque

class EvidenceGraph:
    """
    Evidence Relationship Graph using Adjacency List representation.
    - Vertices V: Image Evidence items
    - Edges E: Relationships (Exact Duplicate, Perceptual Match, Shared Camera/Device)
    """
    def __init__(self):
        self.adj_list = {} # id -> list of (neighbor_id, weight, relationship_type)

    def add_vertex(self, evidence_id):
        if evidence_id not in self.adj_list:
            self.adj_list[evidence_id] = []

    def add_edge(self, u, v, weight=1.0, relation_type="DUPLICATE"):
        self.add_vertex(u)
        self.add_vertex(v)
        # Undirected relationship
        if not any(neighbor == v for neighbor, _, _ in self.adj_list[u]):
            self.adj_list[u].append((v, weight, relation_type))
        if not any(neighbor == u for neighbor, _, _ in self.adj_list[v]):
            self.adj_list[v].append((u, weight, relation_type))

    def display(self):
        print("\n--- FORENSIC EVIDENCE GRAPH (Adjacency List) ---")
        for vertex, edges in self.adj_list.items():
            edge_strs = [f"-> {target} (Weight: {w}, {rel})" for target, w, rel in edges]
            print(f"Vertex [{vertex}]: {', '.join(edge_strs) if edge_strs else 'No edges'}")

    def bfs(self, start_id):
        """Breadth-First Search traversal to detect connected evidence clusters"""
        if start_id not in self.adj_list:
            return []
        visited = set([start_id])
        order = []
        queue = deque([start_id])

        while queue:
            curr = queue.popleft()
            order.append(curr)
            for neighbor, _, _ in self.adj_list[curr]:
                if neighbor not in visited:
                    visited.add(neighbor)
                    queue.append(neighbor)
        return order

    def find_shortest_chain(self, start_id, end_id):
        """Find chain of custody link between two evidence items using BFS"""
        if start_id not in self.adj_list or end_id not in self.adj_list:
            return None
        visited = set([start_id])
        queue = deque([(start_id, [start_id])])

        while queue:
            curr, path = queue.popleft()
            if curr == end_id:
                return path
            for neighbor, _, _ in self.adj_list[curr]:
                if neighbor not in visited:
                    visited.add(neighbor)
                    queue.append((neighbor, path + [neighbor]))
        return None
