import shutil
import sys
import os
from datetime import datetime
from collections import defaultdict
from config import background_color
from rich.console import Console
from rich.panel import Panel
from rich.align import Align
from helper import convert_days_to_dhm

from logger import setup_logger
logger = setup_logger()

console = Console()

def display_header(polling_interval):
  logger.info(f"Printing the header layers")
  terminal_width = shutil.get_terminal_size().columns
  timestamp = f"Fetching batch @ {(datetime.now()).strftime('%a %b %H:%M')}"
  polling_info = f"Next poll in {polling_interval} minutes..."

  print(timestamp.center(terminal_width))
  print(polling_info.center(terminal_width))

def clear_screen():
  logger.info("Cleaing screen from other garbage")
  if os.name == 'nt':
    os.system('cls')
  else:
    os.system('clear')

def handle_shutdown(signum, frame):
  logger.info(f"Shutdown code: {signum}")
  sys.exit(0)

def display_team(cases, debug):
  color = background_color()

  product_count = defaultdict(int)
  for case in cases:
    product = case.get('Product__r', {}).get('Name', 'No Product')
    product_count[product] += 1

  
  if not cases:
      panel = Panel("No cases in the queue", title=f"[bold {color}]Team Queue[/bold {color}]", border_style=f"{color}")
      console.print('\n',Align.center(panel))
  else:
    lines = []
    for product, count in product_count.items():
      lines.append(f"[bold yellow]{count}[/bold yellow] new [bold]{product}[/bold] case(s)")
    panel_content = "\n".join(lines)
    panel = Panel(panel_content, title=f"[bold {color}]Team Queue[/bold {color}]", border_style=f"{color}")
    console.print('\n',Align.center(panel))

def display_personal(cases, debug):
  color = background_color()
  InSupport = 0
  New = 0
  NeedsCommitment = 0

  if not cases:
    raise ValueError("No cases to display for personal.")

  for case in cases:
    status = case.get('Status')
    commitment_time = case.get('Time_Before_Next_Update_Commitment__c')

    if commitment_time < 1 and status not in ['New', 'Closed']:
      NeedsCommitment += 1

    if status == "In Support":
      InSupport += 1

    if status == "New":
      New += 1

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

def display_opened_today(cases, debug):
  color = background_color()

  total_case = 0

  lines = []
  if cases:
    for case in cases:
      case_num = case.get("CaseNumber")
      product = case.get('Product__r', {}).get('Name', 'No Product')
      engineer = case.get('Owner', {}).get('Name', 'n/a')
      total_case += 1
      lines.append(f"[bold yellow]{case_num}[/bold yellow] - {product} w/ {engineer}")

    panel_content = "\n".join(lines)
    panel = Panel(panel_content, title=f"[bold {color}]Last 24 Hours[/bold {color}]", border_style=f"{color}")
  else:
    panel_content = "No cases created today"

  panel = Panel(panel_content, title=f"[bold {color}]Last 24 Hours[/bold {color}]", border_style=f"{color}")

  console.print(Align.center(panel))

def display_team_needs_commitment(cases, debug):
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
  
  console.print('\n',Align.center(panel))

def display_queue_needs_commitment(cases, debug):
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

  console.print(Align.center(panel))