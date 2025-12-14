"""Tests for services queue module."""
import unittest
import sys
from pathlib import Path

# Import directly to avoid muts package import issues
sys.path.insert(0, str(Path(__file__).parent.parent / 'muts' / 'services'))
from queue import ECUQueue


class TestECUQueue(unittest.TestCase):
    """Test ECUQueue class."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.queue = ECUQueue()
    
    def test_initialization(self):
        """Test ECUQueue initialization."""
        self.assertIsNotNone(self.queue.q)
        self.assertEqual(len(self.queue.q), 0)
    
    def test_push_many(self):
        """Test push_many method."""
        actions = [
            {"type": "read", "did": 0x1234},
            {"type": "write", "did": 0x5678, "data": b'\x01\x02'}
        ]
        
        self.queue.push_many(actions)
        
        self.assertEqual(len(self.queue.q), 2)
    
    def test_drain_sim(self):
        """Test drain_sim method."""
        actions = [
            {"type": "x"},
            {"type": "y"},
            {"type": "z"}
        ]
        
        self.queue.push_many(actions)
        count = self.queue.drain_sim()
        
        self.assertEqual(count, 3)
        self.assertEqual(len(self.queue.q), 0)
    
    def test_drain_sim_empty(self):
        """Test drain_sim with empty queue."""
        count = self.queue.drain_sim()
        
        self.assertEqual(count, 0)
    
    def test_multiple_operations(self):
        """Test multiple push and drain operations."""
        # First batch
        self.queue.push_many([{"type": "a"}, {"type": "b"}])
        self.assertEqual(len(self.queue.q), 2)
        
        # Drain
        count1 = self.queue.drain_sim()
        self.assertEqual(count1, 2)
        self.assertEqual(len(self.queue.q), 0)
        
        # Second batch
        self.queue.push_many([{"type": "c"}])
        self.assertEqual(len(self.queue.q), 1)
        
        # Drain again
        count2 = self.queue.drain_sim()
        self.assertEqual(count2, 1)
        self.assertEqual(len(self.queue.q), 0)


if __name__ == '__main__':
    unittest.main()

