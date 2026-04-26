from utils.helper import convert_days_to_dhm
from rich.console import Console
from rich.panel import Panel
from rich.align import Align

console = Console()

class ManagerDisplay():
  @staticmethod
  def team_commitment(cases, update_threshold, color):
    pColor = color.get("primary")
    sColor = color.get("secondary")
    lines = []

    for case in cases:
      case_num = case.get("CaseNumber")
      owner = case.get("Owner", {}).get("Name", "n/a")
      next_update = case.get("Time_Before_Next_Update_Commitment__c")
      if next_update:
        next_update_formated = convert_days_to_dhm(next_update)
      else: next_update_formated = 'Null'
      lines.append(f"[bold {sColor}]{case_num}[/bold {sColor}] w/ {owner} in [bold]{next_update_formated}[/bold]")
    if not cases: lines.append(f"None, your team is looking good!")

    panel_content = "\n".join(lines)
    panel = Panel(Align.center(panel_content), title=f"[bold {pColor}]Team commitments within 1 Day[/bold {pColor}]", border_style=f"{pColor}")
    
    console.print('\n',Align.center(panel))

  @staticmethod
  def queue_commitment(cases, update_threshold, color):
    pColor = color.get("primary")
    sColor = color.get("secondary")

    lines = []

    for case in cases:
      case_num = case.get("CaseNumber")
      product = case.get('Product__r', {}).get('Name', 'No Product')
      next_update = case.get("Time_Before_Next_Update_Commitment__c")
      
      if next_update: next_update_formated = convert_days_to_dhm(next_update)
      else: next_update_formated = 'Null'

      lines.append(f"[bold {sColor}]{case_num}[/bold {sColor}] for [bold]{product}[/bold] in [bold]{next_update_formated}[/bold]")
    if not cases: lines.append(f"   None, your team has it covered!")
    panel_content = "\n".join(lines)
    panel = Panel(Align.center(panel_content), title=f"[bold {pColor}]Queue commitments within {update_threshold} minutes[/bold {pColor}]", border_style=f"{pColor}")

    console.print(Align.center(panel))