import argparse
import shutil
import sys
import os
from datetime import datetime
from collections import defaultdict
from config import DEBUG, background_color
from rich.console import Console
from rich.panel import Panel
from rich.align import Align
from helper import convert_days_to_dhm

console = Console()

def info_logger():
  parser = argparse.ArgumentParser(
        prog="python3 main.py",
        description=f"""\
SalesForce API Query Tool
--------------------------
A CLI tool to view and monitor Salesforce cases from your terminal.

Features:
  Authenticated API queries to Salesforce via Axway credentials
  Filters for team, personal, and newly opened cases
  Optional CSV export for reporting (Not yet)
  Configurable notifications (Only on Mac)

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

def display_header(polling_interval, debug):
  func = "display_header()"
  def log(msg): DEBUG(debug, f"{func}: {msg}")
  log("Started")
  terminal_width = shutil.get_terminal_size().columns

  timestamp = f"Fetching batch @ {(datetime.now()).strftime('%a %b %H:%M')}"
  polling_info = f"Next poll in {polling_interval} minutes..."

  print(timestamp.center(terminal_width))
  print(polling_info.center(terminal_width))
  log("Finished")

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
  color = background_color()

  product_count = defaultdict(int)
  for case in cases:
    product = case.get('Product__r', {}).get('Name', 'No Product')
    product_count[product] += 1

  if not debug:
    if not cases:
        panel = Panel("No cases in the queue", title=f"[bold {color}]Team Queue[/bold {color}]", border_style=f"{color}")
        console.print('\n',Align.center(panel))
    else:
      lines = []
      for product, count in product_count.items():
        log(f"Total product count for {product} is {count}")
        lines.append(f"[bold yellow]{count}[/bold yellow] new [bold]{product}[/bold] case(s)")
      panel_content = "\n".join(lines)
      panel = Panel(panel_content, title=f"[bold {color}]Team Queue[/bold {color}]", border_style=f"{color}")
      console.print('\n',Align.center(panel))

  log("Finished")

def display_personal(cases, debug):
  func = "display_personal()"
  def log(msg): DEBUG(debug, f"{func}: {msg}")
  log("Started")
  color = background_color()

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

  if not debug:
    if InSupport + New + NeedsCommitment == 0:
      panel = Panel("No case updates", title=f"[bold {color}]Your Cases[/bold {color}]", border_style=f"{color}")
    else:
      lines = []

      if InSupport > 0:
        lines.append(f"[bold yellow]{InSupport}[/bold yellow] case(s) are [bold]In Support[/bold]")

      if New > 0:
        lines.append(f"[bold yellow]{New}[/bold yellow] case(s) need an [bold]IC[/bold]")

      if NeedsCommitment > 0:
        lines.append(f"[bold yellow]{NeedsCommitment}[/bold yellow] case(s) need an [bold]update in 24 hours[/bold]")

      panel_content = "\n".join(lines)
      panel = Panel(panel_content, title=f"[bold {color}]Personal Queue[/bold {color}]", border_style=f"{color}")

    console.print(Align.center(panel))

  log("Finished")

def display_opened_today(cases, debug):
  func = "display_opened_today()"
  def log(msg): DEBUG(debug, f"{func}: {msg}")
  log("Started")
  color = background_color()

  total_case = 0
  if not cases:
    panel = Panel("No cases created today", title=f"[bold {color}]Cases Opened Today[/bold {color}]", border_style=f"{color}")

  lines = []

  for case in cases:
    case_num = case.get("CaseNumber")
    product = case.get('Product__r', {}).get('Name', 'No Product')
    engineer = case.get('Owner', {}).get('Name', 'n/a')
    total_case += 1
    lines.append(f"[bold yellow]{case_num}[/bold yellow] - {product} w/ {engineer}")
  
  panel_content = "\n".join(lines)
  panel = Panel(panel_content, title=f"[bold {color}]Opened Today[/bold {color}]", border_style=f"{color}")

  if not debug:
    console.print(Align.center(panel))

  log(f"Total cases created today = {total_case}")
  log("Finished")

def display_team_needs_commitment(cases, debug):
  func = "display_team_needs_commitment()"
  def log(msg): DEBUG(debug, f"{func}: {msg}")
  log("Started")
  color = background_color()

  lines = []

  for case in cases:
    case_num = case.get("CaseNumber")
    owner = case.get("Owner", {}).get("Name", "n/a")
    next_update = case.get("Time_Before_Next_Update_Commitment__c")
    next_update_formated = convert_days_to_dhm(next_update)
    lines.append(f"[bold yellow]{case_num}[/bold yellow] w/ {owner} in [bold]{next_update_formated}[/bold]")
  if not cases: lines.append(f"                  None")

  panel_content = "\n".join(lines)
  panel = Panel(panel_content, title=f"[bold {color}]Team commitments within 1 Day[/bold {color}]", border_style=f"{color}")
  
  if not debug: console.print('\n',Align.center(panel))
  log("Finished")

def display_queue_needs_commitment(cases, debug):
  func="display_queue_needs_commitment()"
  def log(msg): DEBUG(debug, f"{func}: {msg}")
  log("Started")
  color = background_color()

  lines = []

  for case in cases:
    case_num = case.get("CaseNumber")
    product = case.get('Product__r', {}).get('Name', 'No Product')
    next_update = case.get("Time_Before_Next_Update_Commitment__c")
    next_update_formated = convert_days_to_dhm(next_update)
    lines.append(f"[bold yellow]{case_num}[/bold yellow] for [bold]{product}[/bold] in [bold]{next_update_formated}[/bold]")
  if not cases: lines.append(f"                 None")
  panel_content = "\n".join(lines)
  panel = Panel(panel_content, title=f"[bold {color}]Queue commitments within 45 minutes[/bold {color}]", border_style=f"{color}")

  if not debug: console.print(Align.center(panel))
  log("Finished")

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