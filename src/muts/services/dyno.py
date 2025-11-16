class DynoService:
    def virtual_pull(self) -> dict:
        # Toy model for now — assistants can replace this with real math later
        peak_hp = 265
        peak_tq = 380
        return {"peak_hp": peak_hp, "peak_tq": peak_tq}
