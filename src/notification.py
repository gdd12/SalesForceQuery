import os
from collections import defaultdict
from config import DEBUG

def notify(cases, debug):
  func = "notify()"
  DEBUG(debug, f'{func}: Started')
  product_count = defaultdict(int)

  for case in cases:
    product = case.get('Product__r', {}).get('Name', 'No Product')
    product_count[product] += 1

  if product_count:
    message_parts = []
    for product, count in product_count.items():
      message_parts.append(f"{count} {product} Case(s)")

  message = "\n".join(message_parts)
  script = f'display notification "{message}" with title "New SalesForce Cases" sound name "Funk"'
  os.system(f"osascript -e '{script}'")
  DEBUG(debug, f'{func}: Finished')