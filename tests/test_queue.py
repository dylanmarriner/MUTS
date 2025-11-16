from muts.services.queue import ECUQueue

def test_queue_drain():
    q = ECUQueue()
    q.push_many([{"type": "x"}, {"type": "y"}])
    assert q.drain_sim() == 2
