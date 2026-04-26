import os
from collections import defaultdict
from logger import logger

def notify(cases, isTest: False, sound):
  product_count = defaultdict(int)

  if isTest:
    logger.debug("Test mode enabled, notification will NOT be sent.")
    return

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
      os.system(f"osascript -e '{script}'")
      logger.info(f"Sent notification: {message_parts} with {'no' if not sound else f'{sound}'} sound")
    except Exception as e:
      logger.error(f"Error sending notification: {e}")