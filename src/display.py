import sys
import os
from collections import defaultdict
from config import load_configuration, DEBUG

def clear_screen():
  if os.name == 'nt':
    os.system('cls')
  else:
    os.system('clear')

def handle_shutdown(signum, frame):
  sys.exit(0)

def display_team(cases, debug):
  func = "display_team()"
  DEBUG(debug, f'{func}: Started')

  if not cases:
    raise ValueError("No cases to display for the team.")
  product_count = defaultdict(int)
  DEBUG(debug, f'{func}: Initializing product count')
  for case in cases:
    product = case.get('Product__r', {}).get('Name', 'No Product')
    product_count[product] += 1
  if product_count:
    if not debug: print(f"Team queue list:")
    for product, count in product_count.items():
      DEBUG(debug, f'{func}: Total product count for {product} is {count}')
      if not debug:
        print(f"  {count} new {product} case(s)")
  else:
    print("  No cases in the queue")
  DEBUG(debug, f'{func}: Finished')

def display_personal(cases, debug):
  func = "display_personal()"
  DEBUG(debug, f'{func}: Started')
  if not cases:
    raise ValueError("No cases to display for personal.")
  DEBUG(debug, f'{func}: Initializing product count')
  InSupport = 0
  New = 0
  NeedsCommitment = 0
  DEBUG(debug, f'{func}: Looping through cases and capturing status and commitment_time')
  for case in cases:
    status = case.get('Status')
    commitment_time = case.get('Time_Before_Next_Update_Commitment__c')

    if commitment_time < 1 and status != 'New':
      NeedsCommitment += 1
    if status == "In Support":
      InSupport += 1
    if status == "New":
      New += 1
  DEBUG(debug, f'{func}: InSupport count: {InSupport}')
  DEBUG(debug, f'{func}: New count: {New}')
  DEBUG(debug, f'{func}: NeedsCommitment count: {NeedsCommitment}')
  if not debug: print(f"\nPersonal queue list:")
  if InSupport + New + NeedsCommitment == 0:
    if not debug: print(f"  No case updates")
    else: DEBUG(debug, f"{func}: No cases require updates")
  if InSupport > 0 and not debug:
    print(f"  {InSupport} case(s) are In Support")
  if New > 0 and not debug:
    print(f"  {New} case(s) need an IC")
  if NeedsCommitment > 0 and not debug:
    print(f"  {NeedsCommitment} case(s) need an update in 24 hours")
  DEBUG(debug, f'{func}: Finished')

def display_opened_today(cases, debug):
  func = "display_opened_today()"
  DEBUG(debug, f'{func}: Started')
  total_case = 0
  if not debug: print('\nCases opened today:')
  if not cases:
    raise ValueError("No cases were created today")
  else:
    for case in cases:
      case_num = case.get("CaseNumber")
      product = case.get('Product__r', {}).get('Name', 'No Product')
      total_case += 1
      if not debug:
        print(f'  {case_num} - {product}')
  DEBUG(debug, f'{func}: Total cases created today = {total_case}')
  DEBUG(debug, f'{func}: Finished')