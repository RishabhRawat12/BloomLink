# app/bloom_filter.py
import hashlib

class BloomFilter:
    def __init__(self, size=100_000, hash_count=3):
        self.size = size
        self.hash_count = hash_count
        self.bits = bytearray(size)

    def _hashes(self, key: str):
        h1 = int(hashlib.sha1(key.encode()).hexdigest(), 16)
        h2 = int(hashlib.md5(key.encode()).hexdigest(), 16)
        for i in range(self.hash_count):
            yield (h1 + i * h2) % self.size

    def add(self, key: str):
        for pos in self._hashes(key):
            self.bits[pos] = 1

    def might_exist(self, key: str) -> bool:
        return all(self.bits[pos] for pos in self._hashes(key))