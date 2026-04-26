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

  @staticmethod
  def queue(cases, update_threshold, color):
    pColor = color.get("primary")
    sColor = color.get("secondary")
    product_count = defaultdict(int)
    needs_commitment = 0

    for case in cases:
      product = case.get('Product__r', {}).get('Name', 'No Product')
      commitment = case.get('Time_Before_Next_Update_Commitment__c')

      if commitment and (commitment < (update_threshold / (24 * 60))):
        needs_commitment += 1
      product_count[product] += 1

    if not cases:
        panel = Panel("None, you're looking good!", title=f"[bold {pColor}]Team Queue[/bold {pColor}]", border_style=f"{pColor}")
        console.print('\n',Align.center(panel))
    else:
      lines = []
      for product, count in product_count.items():
        lines.append(f"[bold {sColor}]{count}[/bold {sColor}] new [bold]{product}[/bold] case(s)")
        if needs_commitment > 0 : lines.append(f"[bold red]{needs_commitment}[/bold red] case(s) needs commitment!")
      panel_content = "\n".join(lines)
      panel = Panel(panel_content, title=f"[bold {pColor}]Team Queue[/bold {pColor}]", border_style=f"{pColor}")
      console.print('\n',Align.center(panel))
  
  @staticmethod
  def personal(cases, update_threshold, color):
    pColor = color.get("primary")
    sColor = color.get("secondary")
    VacationFailedValidation = False
    days_remaining_vac = 0
    if Config().get_config_value("rules.vacation_scheduled"):
      vac_timeframe = Config().get_config_value("rules.back_from_vacation")
      days_remaining_vac = convert_vacation(vac_timeframe)
      if type(days_remaining_vac) != int:
        VacationFailedValidation = True

    InSupport = 0
    New = 0
    NeedsCommitment = 0
    AboutToMiss = 0
    MissDuringVacation = 0
    MissOverWeekend = 0

    if not cases:
      panel = Panel("You have no assigned cases!", title=f"[bold {pColor}]Your Cases[/bold {pColor}]", border_style=f"{pColor}")
    else:
      for case in cases:
        status = case.get('Status')
        status = status.upper()
        commitment_time = case.get('Time_Before_Next_Update_Commitment__c')

        if commitment_time and (commitment_time < 1 and status not in ['NEW', 'CLOSED']):
          if commitment_time < (update_threshold / (24 * 60)):
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
        panel = Panel("None, you're looking good!", title=f"[bold {pColor}]Your Cases[/bold {pColor}]", border_style=f"{pColor}")
      else:
        lines = []
        if InSupport > 0:
          lines.append(f"[bold {sColor}]{InSupport}[/bold {sColor}] case(s) are [bold]In Support[/bold]")
        if New > 0:
          lines.append(f"[bold {sColor}]{New}[/bold {sColor}] case(s) need an [bold]IC[/bold]")
        if NeedsCommitment > 0:
          lines.append(f"[bold {sColor}]{NeedsCommitment}[/bold {sColor}] case(s) need an [bold]update in 24 hours[/bold]")
        if AboutToMiss > 0:
          lines.append(f"[bold {sColor}]{AboutToMiss}[/bold {sColor}] case(s) need an [bold red]update right now[/bold red]")
        if MissDuringVacation > 0:
          lines.append(f"[bold {sColor}]{MissDuringVacation}[/bold {sColor}] case(s) will be missed during your vacation!")
        if MissOverWeekend > 0:
          lines.append(f"[bold {sColor}]{MissOverWeekend}[/bold {sColor}] commitments(s) are due on/before Monday!")
        if VacationFailedValidation:
          lines.append(f"Vacation config validation failed. Check config.json")

        panel_content = "\n".join(lines)
        panel = Panel(panel_content, title=f"[bold {pColor}]Personal Queue[/bold {pColor}]", border_style=f"{pColor}")

    console.print(Align.center(panel))

  @staticmethod
  def opened_today(cases, debug, color):
    pColor = color.get("primary")
    sColor = color.get("secondary")

    total_case = 0

    lines = []
    if cases:
      for case in cases:
        case_num = case.get("CaseNumber")
        product = case.get('Product__r', {}).get('Name', 'No Product')
        engineer = case.get('Owner', {}).get('Name', 'n/a')
        priority = case.get('Severity__c')
        total_case += 1
        lines.append(f"[bold {sColor}]{case_num}[/bold {sColor}] - {product} (P{priority.split(' ')[0]}) - {engineer.split(' ')[0]}")

      panel_content = "\n".join(lines)
      panel = Panel(panel_content, title=f"[bold {pColor}]Last 24 Hours[/bold {pColor}]", border_style=f"{pColor}")
    else:
      panel_content = "No cases created today"

    panel = Panel(panel_content, title=f"[bold {pColor}]Last 24 Hours[/bold {pColor}]", border_style=f"{pColor}")

    console.print(Align.center(panel))