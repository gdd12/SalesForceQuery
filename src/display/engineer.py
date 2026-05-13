import shutil
import os
from datetime import datetime
from collections import defaultdict
from config.config import Config
from rich.console import Console
from rich.panel import Panel
from rich.align import Align
from utils.helper import convert_days_to_dhm, convert_vacation
from logger import logger

console = Console()

class EngineerDisplay():
  def __init__(self, dashboard):
    self.data = dashboard

    self.p_color = dashboard.color.get("primary")
    self.s_color = dashboard.color.get("secondary")

  def render(self):
    self.queue()
    self.personal()
    self.case_insights()
    self.opened_today()

  def queue(self):
    product_count = defaultdict(int)
    needs_commitment = 0
    cases = self.data.team_cases

    for case in cases:
      product = case.get('Product__r', {}).get('Name', 'No Product')
      commitment = case.get('Time_Before_Next_Update_Commitment__c')

      if commitment and (commitment < (self.data.update_threshold / (24 * 60))):
        needs_commitment += 1
      product_count[product] += 1

    if not cases:
        panel = Panel("None, you're looking good!", title=f"[bold {self.p_color}]Team Queue[/bold {self.p_color}]", border_style=f"{self.p_color}")
        console.print('\n',Align.center(panel))
    else:
      lines = []
      for product, count in product_count.items():
        lines.append(f"[bold {self.s_color}]{count}[/bold {self.s_color}] new [bold]{product}[/bold] case(s)")
        if needs_commitment > 0 : lines.append(f"[bold red]{needs_commitment}[/bold red] case(s) needs commitment!")
      panel_content = "\n".join(lines)
      panel = Panel(panel_content, title=f"[bold {self.p_color}]Team Queue[/bold {self.p_color}]", border_style=f"{self.p_color}")
      console.print('\n',Align.center(panel))
  
  def personal(self):
    VacationFailedValidation = False
    days_remaining_vac = 0
    if self.data.vacation_scheduled:
      vac_timeframe = self.data.vacation_return_date
      days_remaining_vac = convert_vacation(vac_timeframe)
      if type(days_remaining_vac) != int:
        VacationFailedValidation = True

    cases = self.data.personal_cases

    InSupport = 0
    New = 0
    NeedsCommitment = 0
    AboutToMiss = 0
    MissDuringVacation = 0
    MissOverWeekend = 0

    if not cases:
      panel = Panel("You have no assigned cases!", title=f"[bold {self.p_color}]Your Cases[/bold {self.p_color}]", border_style=f"{self.p_color}")
    else:
      for case in cases:
        status = case.get('Status')
        status = status.upper()
        commitment_time = case.get('Time_Before_Next_Update_Commitment__c')

        if commitment_time and (commitment_time < 1 and status not in ['NEW', 'CLOSED']):
          if commitment_time < (self.data.update_threshold / (24 * 60)):
            AboutToMiss += 1
          else:
            NeedsCommitment += 1

        if status == "IN SUPPORT":
          InSupport += 1

        if status == "NEW":
          New += 1
        
        if (not VacationFailedValidation) and days_remaining_vac > 0 and (days_remaining_vac > commitment_time):
          MissDuringVacation += 1

        if (datetime.today().strftime('%A').lower() == 'friday' and commitment_time < 3):
          MissOverWeekend += 1

      if (InSupport + New + NeedsCommitment + MissOverWeekend + AboutToMiss == 0) and MissDuringVacation < 1:
        panel = Panel("None, you're looking good!", title=f"[bold {self.p_color}]Your Cases[/bold {self.p_color}]", border_style=f"{self.p_color}")
      else:
        lines = []
        if InSupport > 0:
          lines.append(f"[bold {self.s_color}]{InSupport}[/bold {self.s_color}] case(s) are [bold]In Support[/bold]")
        if New > 0:
          lines.append(f"[bold {self.s_color}]{New}[/bold {self.s_color}] case(s) need an [bold]IC[/bold]")
        if NeedsCommitment > 0:
          lines.append(f"[bold {self.s_color}]{NeedsCommitment}[/bold {self.s_color}] case(s) need an [bold]update in 24 hours[/bold]")
        if AboutToMiss > 0:
          lines.append(f"[bold {self.s_color}]{AboutToMiss}[/bold {self.s_color}] case(s) need an [bold red]update right now[/bold red]")
        if MissDuringVacation > 0:
          lines.append(f"[bold {self.s_color}]{MissDuringVacation}[/bold {self.s_color}] case(s) will be missed during your vacation!")
        if MissOverWeekend > 0:
          lines.append(f"[bold {self.s_color}]{MissOverWeekend}[/bold {self.s_color}] commitments(s) are due on/before Monday!")
        if VacationFailedValidation:
          lines.append(f"Vacation config validation failed. Check config.json")

        panel_content = "\n".join(lines)
        panel = Panel(panel_content, title=f"[bold {self.p_color}]Your Cases[/bold {self.p_color}]", border_style=f"{self.p_color}")

    console.print(Align.center(panel))

  def opened_today(self):
    total_case = 0
    cases = self.data.opened_today_cases

    lines = []
    if cases:
      for case in cases:
        case_num = case.get("CaseNumber")
        product = case.get('Product__r', {}).get('Name', 'No Product')
        engineer = case.get('Owner', {}).get('Name', 'n/a')
        priority = case.get('Severity__c')
        total_case += 1
        lines.append(f"[bold {self.s_color}]{case_num}[/bold {self.s_color}] - {product} (P{priority.split(' ')[0]}) - {engineer.split(' ')[0]}")

      panel_content = "\n".join(lines)
      panel = Panel(panel_content, title=f"[bold {self.p_color}]Last 24 Hours[/bold {self.p_color}]", border_style=f"{self.p_color}")
    else:
      panel_content = "No cases created today"

    panel = Panel(panel_content, title=f"[bold {self.p_color}]Last 24 Hours[/bold {self.p_color}]", border_style=f"{self.p_color}")

    console.print(Align.center(panel))

  def case_insights(self):
    missing_complexity = 0
    other_case_reason = 0

    cases = self.data.personal_cases

    if cases:
      for case in cases:
        case_reason = case.get('Case_Reason__c')
        case_complexity = case.get('Case_Complexity__c')
        if not case_complexity:
          missing_complexity += 1
        if case_reason == 'Other':
          other_case_reason += 1

    lines = []

    if missing_complexity > 0:
      lines.append(f"[bold {self.s_color}]{missing_complexity}[/bold {self.s_color}] case(s) missing a [bold]Case Complexity[/bold]")
    if other_case_reason > 0:
      lines.append(f"[bold {self.s_color}]{other_case_reason}[/bold {self.s_color}] case(s) opened as [bold]Other[/bold]")
    if missing_complexity + other_case_reason == 0:
      lines.append("No case insights available")
    
    panel_content = "\n".join(lines)
    panel = Panel(panel_content, title=f"[bold {self.p_color}]Case Insights[/bold {self.p_color}]", border_style=f"{self.p_color}")

    console.print(Align.center(panel))