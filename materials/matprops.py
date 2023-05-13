class MatProps:
    def __init__(self, youngs_mod, yield_strength, ult_strength, ult_strain):
        self.youngs_mod = youngs_mod
        self.yield_strength = yield_strength
        self.yield_strain = (yield_strength / youngs_mod) * 100 + 0.2
        self.ult_strength = ult_strength
        self.ult_strain = ult_strain
        self.plastic_tangent_mod = (ult_strength - yield_strength) / ((ult_strain - self.yield_strain) / 100)

    def __str__(self):
        return f"Young's Modulus = {self.youngs_mod / 1E6} MPa\n" \
               f"Yield Strength = {self.yield_strength / 1E6} MPa\n" \
               f"Yield Strain = {self.yield_strain} %\n" \
               f"Ultimate Strength = {self.ult_strength / 1E6} MPa\n" \
               f"Ultimate Strain = {self.ult_strain}\n" \
               f"Plastic Tangent Modulus = {self.plastic_tangent_mod / 1e6} MPa\n"
