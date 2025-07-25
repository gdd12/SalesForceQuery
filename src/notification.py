import os
from collections import defaultdict

import logging
logger = logging.getLogger()

def notify(cases, debug, sound):
  product_count = defaultdict(int)

  for case in cases:
    product = case.get('Product__r', {}).get('Name', 'No Product')
    product_count[product] += 1

  if product_count:
    message_parts = [f"{count} {product} Case(s)" for product, count in product_count.items()]
    message = "\n".join(message_parts)
    if sound:
      script = f'display notification "{message}" with title "New SalesForce Cases" sound name "{sound}"'
    else:
      script = f'display notification "{message}" with title "New SalesForce Cases"'

    try:
      logger.info(f"Sending notification: {message} with {'no' if not sound else f'{sound}'} sound")
      os.system(f"osascript -e '{script}'")
      logger.info("Notification sent.")
    except Exception as e:
      logger.error(f"Error sending notification: {e}")