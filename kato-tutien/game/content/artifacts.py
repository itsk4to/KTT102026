from game.content.items import ITEMS
ARTIFACTS={k:v for k,v in ITEMS.items() if v.get("category") in {"Pháp bảo","Binh khí"}}
