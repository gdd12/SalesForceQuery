import argparse
import sys
import os
from collections import defaultdict
from config import DEBUG

def info_logger():
  text = title()
  parser = argparse.ArgumentParser(
        prog="python3 main.py",
        description=f"""\
        {text}
--------------------------
A CLI tool to view and monitor Salesforce cases from your terminal.

Features:
- Authenticated API queries to Salesforce via Axway credentials
- Filters for team, personal, and newly opened cases
- Optional CSV export for reporting (Not yet)
- Configurable notifications (Only on Mac)

""",
        epilog="""\
Examples:
  python3 main.py --debug
  python3 main.py --notify

""",
    formatter_class=argparse.RawDescriptionHelpFormatter
  )

  parser.add_argument(
    "--debug",
    action="store_true",
    help="Enable verbose logging and show internal debug messages."
  )
  parser.add_argument(
    "--notify",
    action="store_true",
    help="Force notifications to be sent, overriding the config.json. MacOS ONLY!"
  )

  return parser.parse_args()

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

  if not debug: print("=== Team Queue ===")
  if not cases:
    print("  No cases in the queue")

  product_count = defaultdict(int)

  for case in cases:
    product = case.get('Product__r', {}).get('Name', 'No Product')
    product_count[product] += 1

  if product_count:
    for product, count in product_count.items():
      log(f"Total product count for {product} is {count}")
      if not debug:
        print(f"  {count} new {product} case(s)")

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
      print("   No case updates")
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

def display_team_needs_commitment(cases, debug):
  func = "display_team_needs_commitment()"
  def log(msg): DEBUG(debug, f"{func}: {msg}")

  log("Started")

  if not debug: print("\n=== Cases Needing Commitment Within 1 Day ===")
  for case in cases:
    case_num = case.get("CaseNumber")
    owner = case.get("Owner", {}).get("Name", "n/a")
    next_update = case.get("Time_Before_Next_Update_Commitment__c")
    print(f"Case: {case_num}")
    print(f"Owner: {owner}")
    print(f"Countdown: {next_update}")
    print("-----------------")
  if not cases and not debug: print("                     None")
  if debug: log("Finished")
  if not debug: print("="*45)

def title():
  title = """\

   _____       _           ______                            _____ _____ 
  / ____|     | |         |  ____|                     /\   |  __ \_   _|
 | (___   __ _| | ___  ___| |__ ___  _ __ ___ ___     /  \  | |__) || |  
  \___ \ / _` | |/ _ \/ __|  __/ _ \| '__/ __/ _ \   / /\ \ |  ___/ | |  
  ____) | (_| | |  __/\__ \ | | (_) | | | (_|  __/  / ____ \| |    _| |_ 
 |_____/ \__,_|_|\___||___/_|  \___/|_|  \___\___| /_/    \_\_|   |_____|
"""
  return title