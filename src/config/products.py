import os
from utils.helper import logger, get_non_empty_input
from utils.variables import FileNames

class Products():
  def __init__(self):
    self.base_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))

  def load_excluded_products(self ):
    excludedProductsFile = os.path.join(self.base_dir, "config", FileNames.ExProducts)
    try:
      with open(excludedProductsFile, 'r') as file:
        lines = file.readlines()
        excluded = {
          line.strip() for line in lines
          if line.strip() and not line.strip().startswith('#')
        }
        logger.debug(f"Total: {len(excluded)}. Excluded products include: {excluded}")
        return excluded
    except FileNotFoundError:
      logger.warning(f"Excluded file config cannot be found, displaying all returned products.")
      return set()
    return

  def add_excluded_product(self, product=None):
    excludedProductsFile = os.path.join(self.base_dir, "config", FileNames.ExProducts)

    product_to_exclude = product
    if not product:
      product_to_exclude = get_non_empty_input("Enter a product to exclude (RESET to reset the file): ")  

    existing_products = set()

    if os.path.exists(excludedProductsFile):
      with open(excludedProductsFile, 'r') as file:
        existing_products = {line.strip() for line in file if line.strip() and not line.strip().startswith('#')}

    if product_to_exclude in existing_products:
      print(f'\nProduct {product_to_exclude} already exits in {FileNames.ExProducts}')
      logger.warning(f'Product {product_to_exclude} already exits in {FileNames.ExProducts}')
      return

    if product_to_exclude.upper() == 'RESET':
      template = '# Any products you do not support can be placed in this file on new lines'
      try:
        if os.path.exists(excludedProductsFile):
          os.remove(excludedProductsFile)
        with open(excludedProductsFile, 'w') as file:
          file.write(template + '\n')
        print(f'Successfully reset {FileNames.ExProducts}')
        logger.info(f'Successfully reset {FileNames.ExProducts}')
      except Exception as e:
        logger.error(f"Failed to reset {excludedProductsFile}: {e}")
      return
    try:
      with open(excludedProductsFile, 'a') as file:
        file.write(product_to_exclude + '\n')
      logger.info(f"Added '{product_to_exclude}' to {excludedProductsFile}.")
      print(f'\nProduct {product_to_exclude} added to {FileNames.ExProducts}')

    except Exception as e:
      logger.error(f"Failed to add '{product_to_exclude}' to {excludedProductsFile}: {e}")