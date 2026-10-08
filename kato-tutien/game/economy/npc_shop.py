class NPCShopService:
    def __init__(self,economy): self.economy=economy
    def catalog(self): return self.economy.shop_catalog()
