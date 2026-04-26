import shutil, os
from datetime import datetime
from logger import logger

from rich.console import Console
from rich.panel import Panel
from rich.align import Align

console = Console()

class CommonDisplay():
  @staticmethod
  def display_header(polling_interval):
    terminal_width = shutil.get_terminal_size().columns
    timestamp = f"Fetching batch @ {(datetime.now()).strftime('%a %b %H:%M')}"
    polling_info = f"Next poll in {polling_interval} minutes..."

    print(timestamp.center(terminal_width))
    print(polling_info.center(terminal_width))
  
  @staticmethod
  def clear_screen():
    logger.debug("Cleaing screen from startup")
    if os.name == 'nt':
      os.system('cls')
    else:
      os.system('clear')
  
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