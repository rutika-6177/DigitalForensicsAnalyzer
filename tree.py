class TreeNode:
    def __init__(self, evidence_id, data, parent=None):
        self.evidence_id = evidence_id
        self.data = data
        self.parent = parent
        self.children = []
        self.depth = (parent.depth + 1) if parent else 0

class EvidenceTree:
    """
    Hierarchical Evidence Derivation Tree:
    - Root: Case Investigation Root
    - Level 1: Original Evidence Items
    - Level 2+: Duplicates / Modified copies linked to their parent original
    """
    def __init__(self):
        self.root = TreeNode("ROOT", {"name": "Forensic Case Root #CR-2026", "status": "ORIGINAL"})

    def add_evidence(self, evidence_id, data, parent_id="ROOT"):
        parent_node = self.find(parent_id, self.root)
        if not parent_node:
            parent_node = self.root
        new_node = TreeNode(evidence_id, data, parent_node)
        parent_node.children.append(new_node)
        return new_node

    def find(self, evidence_id, current_node=None):
        if current_node is None:
            current_node = self.root
        if current_node.evidence_id == evidence_id:
            return current_node
        for child in current_node.children:
            found = self.find(evidence_id, child)
            if found:
                return found
        return None

    def display(self, node=None, prefix=""):
        if node is None:
            node = self.root
            print("\n--- FORENSIC EVIDENCE HIERARCHY TREE ---")
        status = node.data.get("status", "ORIGINAL")
        name = node.data.get("file_name", node.data.get("name", ""))
        print(f"{prefix}|-- [{node.evidence_id}] ({status}) - {name}")
        for i, child in enumerate(node.children):
            self.display(child, prefix + "    ")

    def bfs_traversal(self):
        """Breadth-First Search / Level-Order Traversal"""
        result = []
        queue = [self.root]
        while queue:
            curr = queue.pop(0)
            result.append(curr.evidence_id)
            for child in curr.children:
                queue.append(child)
        return result

    def preorder_traversal(self, node=None, result=None):
        """Pre-order Traversal: Root -> Children"""
        if result is None:
            result = []
        if node is None:
            node = self.root
        result.append(node.evidence_id)
        for child in node.children:
            self.preorder_traversal(child, result)
        return result
