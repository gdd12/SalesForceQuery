import sys
import os
from collections import defaultdict
from config import DEBUG

def clear_screen():
  if os.name == 'nt':
    os.system('cls')
  else:
    os.system('clear')

def handle_shutdown(signum, frame):
  sys.exit(0)

def display_team(cases, debug):
  func = "display_team()"
  def log(msg): DEBUG(debug, f"{func}: {msg}")

  log("Started")

  if not cases:
    raise ValueError("No cases to display for the team.")

  product_count = defaultdict(int)

  for case in cases:
    product = case.get('Product__r', {}).get('Name', 'No Product')
    product_count[product] += 1

  if product_count:
    if not debug: print("=== Team Queue ===")
    for product, count in product_count.items():
      log(f"Total product count for {product} is {count}")
      if not debug:
        print(f"  {count} new {product} case(s)")
  else:
    print("  No cases in the queue")

  if not debug: print("="*20)
  log("Finished")

def display_personal(cases, debug):
  func = "display_personal()"
  def log(msg): DEBUG(debug, f"{func}: {msg}")

  log("Started")

  if not cases:
    raise ValueError("No cases to display for personal.")

  InSupport = 0
  New = 0
  NeedsCommitment = 0

  for case in cases:
    status = case.get('Status')
    commitment_time = case.get('Time_Before_Next_Update_Commitment__c')

    if commitment_time < 1 and status != 'New':
      NeedsCommitment += 1

    if status == "In Support":
      InSupport += 1

    if status == "New":
      New += 1

  log(f'InSupport count: {InSupport}')
  log(f'New count: {New}')
  log(f'NeedsCommitment count: {NeedsCommitment}')

  if not debug: print("\n=== Personal Queue ===")

  if InSupport + New + NeedsCommitment == 0:
    if not debug:
      print("  No case updates")
    else:
      log("Total is 0, no cases require updates")

  if InSupport > 0 and not debug:
    print(f"  {InSupport} case(s) are In Support")

  if New > 0 and not debug:
    print(f"  {New} case(s) need an IC")

  if NeedsCommitment > 0 and not debug:
    print(f"  {NeedsCommitment} case(s) need an update in 24 hours")

  if not debug: print("="*22)
  log("Finished")

def display_opened_today(cases, debug):
  func = "display_opened_today()"
  def log(msg): DEBUG(debug, f"{func}: {msg}")

  log("Started")

  total_case = 0
  if not debug: print("\n=== Cases Opened Today ===")

  if not cases:
    raise ValueError("No cases were created today")

  for case in cases:
    case_num = case.get("CaseNumber")
    product = case.get('Product__r', {}).get('Name', 'No Product')
    engineer = case.get('Owner', {}).get('Name', 'n/a')
    total_case += 1
    if not debug:
      print(f'  {case_num} - {product} w/ {engineer}')

  if not debug: print("="*26)

  log(f"Total cases created today = {total_case}")
  log("Finished")