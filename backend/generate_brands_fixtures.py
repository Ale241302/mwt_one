import json
import os

fixtures_dir = r"c:\Users\ale13\OneDrive\Documents\mwt_one\backend\apps\brands\fixtures"
os.makedirs(fixtures_dir, exist_ok=True)

# 1. Brand
brand = [
  {
    "model": "brands.brand",
    "pk": "rana_walk",
    "fields": {
      "name": "Rana Walk",
      "brand_type": "own",
      "is_active": True
    }
  }
]

rules = []
for idx, art in enumerate(["ART-01", "ART-02", "ART-05", "ART-06", "ART-09", "ART-11"]):
    rules.append({
        "model": "brands.brandartifactrule",
        "pk": idx + 1,
        "fields": {
            "brand": "rana_walk",
            "artifact_type": art,
            "destination": "ALL",
            "is_required": True
        }
    })

with open(os.path.join(fixtures_dir, "rana_walk_brand.json"), "w", encoding="utf-8") as f:
    json.dump(brand + rules, f, indent=2)

# 2. SKUs
sizes = ["S1", "S2", "S3", "S4", "S5", "S6"]
skus = []
pk_counter = 1

def add_skus(product_key, arch_list):
    global pk_counter
    # Format: RW-{PROD}-{ARCH}-{SIZE}
    for arch in arch_list:
        for size in sizes:
            sku_code = f"RW-{product_key.upper()}-{arch}-{size}"
            skus.append({
                "model": "brands.brandsku",
                "pk": pk_counter,
                "fields": {
                    "brand": "rana_walk",
                    "product_key": product_key,
                    "arch": arch,
                    "size": size,
                    "sku_code": sku_code
                }
            })
            pk_counter += 1

add_skus("gol", ["MED"])
add_skus("vel", ["MED"])
add_skus("orb", ["MED"])
add_skus("leo", ["LOW", "MED", "HGH"])
add_skus("bis", ["LOW", "MED", "HGH"])

with open(os.path.join(fixtures_dir, "rana_walk_skus.json"), "w", encoding="utf-8") as f:
    json.dump(skus, f, indent=2)

print("Fixtures generated successfully.")
