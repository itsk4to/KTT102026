class PlayerMarket:
    def __init__(self,economy_service): self.service=economy_service
    def browse(self,limit=30): return self.service.market_browse(limit)
    def list(self,user_id,item_id,qty,price_each): return self.service.market_list(user_id,item_id,qty,price_each)
    def buy(self,user_id,listing_id): return self.service.market_buy(user_id,listing_id)
    def cancel(self,user_id,listing_id): return self.service.market_cancel(user_id,listing_id)
