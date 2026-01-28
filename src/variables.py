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
  Verbose = 'debug_verbose'

Arg_Definition = (
  ('-c', "Print out the current configuration"),
  ('-d', "Debug mode"),
  ('-dv', "Debug mode with verbose logging"),
  ('-e', "Add an exclusion case number. Use 'RESET' to reset the file"),
  ('-q', "Enter simulation environment"),
  ('-r', "Change user role"),
  ('-s', "Re-write configuration"),
  ('-t', "Add to the team list. Usage: -t, -t update, or -t viewable"),
  ('-x', "Enable test mode, results in no API calls only if a /config/dataBuffer.json exists"),
  ('-h', "Help page"),
)