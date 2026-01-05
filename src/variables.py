class VARS:
  Products = 'products'
  Username = 'username'
  Role = 'role'
  Debug = 'debug'
  Notifications = 'notifications'
  SendNotif = 'send'
  SoundNotif = 'sound'
  EngineerName = 'engineer_name'
  ApiUrl = 'api_url'
  Rules = 'rules'
  Polling = 'poll_interval'
  Colors = 'colors'
  Primary = 'primary'
  Secondary = 'secondary'
  Config = 'config'
  Exclude = 'exclude'
  Notify = 'notify'
  Setup = 'setup'
  Test = 'test'
  Simulate = 'simulate'
  Team = 'team'

Arg_Flag_Alias = {
  '-c': 'config',
  '-d': 'debug',
  '-e': 'exclude',
  '-q': 'simulate',
  '-s': 'setup',
  '-t': 'team',
  '-x': 'test',
  '-h': 'help'
}

Arg_Definition = (
  ('-c', "Print out the current configuration"),
  ('-d', "Debug mode"),
  ('-e', "Add an exclusion case number. Use 'RESET' to reset the file"),
  ('-q', "Enter simulation environment"),
  ('-s', "Re-write configuration"),
  ('-t', "Add to the team list. Usage: -t update, or simply -t to view configuration"),
  ('-x', "Enable test mode, results in no API calls only if a mockData.json is present in /config/"),
  ('-h', "Help page"),
)