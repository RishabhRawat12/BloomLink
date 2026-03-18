import pytest
from app.bloom_filter import BloomFilter

def test_bloom_filter_add_and_check():
    bloom = BloomFilter(size=1000, hash_count=3)
    test_key = "abc1234"
    
    assert not bloom.might_exist(test_key)
    bloom.add(test_key)
    assert bloom.might_exist(test_key)

def test_bloom_filter_false_positives():
    bloom = BloomFilter(size=100_000, hash_count=3)
    bloom.add("known_key")
    
    # Extremely low chance of collision
    assert not bloom.might_exist("unknown_key")