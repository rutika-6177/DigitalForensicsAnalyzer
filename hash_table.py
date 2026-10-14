class HashTable:
    """
    Hash Table with Separate Chaining (Collision Resolution)
    Designed for Forensic Evidence O(1) Duplicate Lookup.
    """
    def __init__(self, size=17):
        self.size = size
        self.table = [[] for _ in range(size)]
        self.count = 0

    def _hash(self, key):
        hash_val = 0
        for char in str(key):
            hash_val = (hash_val * 31 + ord(char)) % self.size
        return hash_val

    def insert(self, evidence_id, evidence):
        index = self._hash(evidence_id)
        bucket = self.table[index]
        for i, (k, v) in enumerate(bucket):
            if k == evidence_id:
                bucket[i] = (evidence_id, evidence)
                return
        bucket.append((evidence_id, evidence))
        self.count += 1

    def search(self, evidence_id):
        index = self._hash(evidence_id)
        bucket = self.table[index]
        for k, v in bucket:
            if k == evidence_id:
                return v
        return None

    def remove(self, evidence_id):
        index = self._hash(evidence_id)
        bucket = self.table[index]
        for i, (k, v) in enumerate(bucket):
            if k == evidence_id:
                del bucket[i]
                self.count -= 1
                return True
        return False

    def display(self):
        print("\n--- FORENSIC HASH TABLE BUCKETS (Separate Chaining) ---")
        for i, bucket in enumerate(self.table):
            if bucket:
                chain = " -> ".join(f"[{k}]" for k, _ in bucket)
                print(f"Bucket #{i:02d}: {chain}")
            else:
                print(f"Bucket #{i:02d}: NULL (empty)")