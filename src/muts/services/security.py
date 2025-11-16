from .queue import queue

class SecurityService:
    def enable_valet(self, pin: str) -> None:
        queue.push_many([
            {"type": "valet_enable", "pin": pin, "torque_cap": 0.5, "rpm_cap": 3000}
        ])
        queue.drain_sim()

    def disable_valet(self, pin: str) -> None:
        queue.push_many([{"type": "valet_disable", "pin": pin}])
        queue.drain_sim()
