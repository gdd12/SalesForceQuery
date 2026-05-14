from utils.helper import convert_days_to_dhm
from rich.console import Console
from rich.panel import Panel
from rich.align import Align
from display.common import ManagerDashboardData, display_placard

console = Console()

class ManagerDisplay():
  def __init__(self, dashboard: ManagerDashboardData):
    self.data = dashboard

    self.p_color = dashboard.color.get("primary")
    self.s_color = dashboard.color.get("secondary")

  def render(self):
    self.team_commitment()
    self.queue_commitment()

  def team_commitment(self):
    lines = []
    cases = self.data.team_needs_commitment

    for case in cases:
      case_num = case.get("CaseNumber")
      owner = case.get("Owner", {}).get("Name", "n/a")
      next_update = case.get("Time_Before_Next_Update_Commitment__c")
      if next_update:
        next_update_formated = convert_days_to_dhm(next_update)
      else: next_update_formated = 'Null'
      lines.append(f"[bold {self.s_color}]{case_num}[/bold {self.s_color}] w/ {owner} in [bold]{next_update_formated}[/bold]")
    if not cases: lines.append(f"None, your team is looking good!")

    panel_content = "\n".join(lines)

    display_placard(content=panel_content, title="Team commitments within 1 Day", p_color=self.p_color)

  def queue_commitment(self):
    lines = []
    cases = self.data.queue_needs_commitment

    for case in cases:
      case_num = case.get("CaseNumber")
      product = case.get('Product__r', {}).get('Name', 'No Product')
      next_update = case.get("Time_Before_Next_Update_Commitment__c")
      
      if next_update: next_update_formated = convert_days_to_dhm(next_update)
      else: next_update_formated = 'Null'

      lines.append(f"[bold {self.s_color}]{case_num}[/bold {self.s_color}] for [bold]{product}[/bold] in [bold]{next_update_formated}[/bold]")
    if not cases: lines.append(f"       None, your team has it covered!")
    panel_content = "\n".join(lines)

    display_placard(content=panel_content, title=f"Queue commitments within {self.data.update_threshold} minutes", p_color=self.p_color)