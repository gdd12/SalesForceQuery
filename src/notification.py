import os
from collections import defaultdict
from config import DEBUG

def notify(cases, debug, sound):
  func = "notify()"
  def log(msg): DEBUG(debug, f"{func}: {msg}")

  product_count = defaultdict(int)

  for case in cases:
    product = case.get('Product__r', {}).get('Name', 'No Product')
    product_count[product] += 1

  if product_count:
    message_parts = [f"{count} {product} Case(s)" for product, count in product_count.items()]
    message = "\n".join(message_parts)
    script = f'display notification "{message}" with title "New SalesForce Cases" sound name "{sound}"'

    try:
      os.system(f"osascript -e '{script}'")
      log("Notification sent.")
    except Exception as e:
      log(f"Error sending notification: {e}")