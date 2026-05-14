import shutil, os
from datetime import datetime
from logger import logger

from rich.console import Console, Group
from rich.panel import Panel
from rich.align import Align
from rich.text import Text

from dataclasses import dataclass
from typing import List

console = Console()

class CommonDisplay():
  @staticmethod
  def display_header(polling_interval):
    terminal_width = shutil.get_terminal_size().columns
    timestamp = f"Fetching batch @ {(datetime.now()).strftime('%a %b %H:%M')}"
    polling_info = f"Next poll in {polling_interval} minutes..."
    CommonDisplay.main_banner(extra_info=(timestamp, polling_info))
  
  @staticmethod
  def clear_screen():
    logger.debug("Clearing screen from startup")
    if os.name == 'nt':
      os.system('cls')
    else:
      os.system('clear')

  @staticmethod
  def failed_validation(cases, color):
    pColor = color.get("primary")
    sColor = color.get("secondary")

    lines = []
    for case in cases:
      case_num = case.get("CaseNumber") or "Empty"
      case_idx = case.get("Index")
      lines.append(f"[bold {sColor}]{case_num}[/bold {sColor}] at index [bold]{case_idx}[/bold]")
    if cases: 
      panel_content = "\n".join(lines)
      panel = Panel(Align.center(panel_content), title=f"[bold {pColor}]Cases Failed Validation [/bold {pColor}]", border_style=f"{pColor}")
      console.print(Align.center(panel))
    return

  @staticmethod
  def main_banner(extra_info=None):
    title = Text("SalesForceQuery Tool", style="bold cyan")
    subtitle = Text("Case Insights • Queue Monitoring • Commitments")

    items = [
      Align.center(title),
      Align.center(subtitle),
    ]

    if extra_info and len(extra_info) == 2:
      items.append(Align.center(Text(extra_info[0], style="dim")))
      items.append(Align.center(Text(extra_info[1], style="dim")))

    content = Group(*items)

    panel = Panel(content, border_style="cyan")
    console.print()
    console.print(Align.center(panel))
  
def display_placard(content, title, p_color):
  panel = Panel(content, title=f"[bold {p_color}]{title}[/bold {p_color}]", border_style=f"{p_color}", width=50)
  console.print(Align.center(panel))

@dataclass
class ManagerDashboardData:
	team_needs_commitment: List[dict]
	queue_needs_commitment: List[dict]
	update_threshold: int
	color: List[dict]

@dataclass
class EngineerDashboardData:
	team_cases: List[dict]
	personal_cases: List[dict]
	opened_today_cases: List[dict]
	update_threshold: int
	vacation_scheduled: bool
	vacation_return_date: str
	color: List[dict]