# SalesForce Query

This project helps automate the process of fetching SalesForce cases. It is designed to retrieve team and personal cases based on predefined queries and display relevant information based on the configuration in the `config.json` file.

## Prerequisites

1. **Python 3**: Ensure that Python 3 is installed on your system.
	- You can check this by running: 
		```python3 --version```
	- If you don’t have Python 3 installed, you can download it from the official [Python website](https://www.python.org/downloads/).

2. **Dependencies**: You need the `requests` and `rich` libraries to interact with the SalesForce API. The `cryptography` is required for password encryption
	- Install the necessary dependencies by running:

      ```pip3 install requests```

      ```pip3 install rich```

      ```pip3 install cryptography```

## Installation and Setup

### 1. Clone the Repository

First, download or clone the repository to your local machine.

```bash
git clone https://github.com/gdd12/SalesForceQuery.git
```

### 2. First-Time Setup

Navigate to the root directory and run the script.
```bash
cd SalesForceQuery/src
python3 main.py
```

The program will prompt you to enter the configuration - follow the wizard.

### Configurable after setup:
If the query returns products you do not support, in another window use the '-e Product' argument and enter the product.
If the query returns a case you do not wish to see, in another window use the '-e Case <Case #>' argument and enter the product.

The help page can be found through the -h argument.
```bash
Usage: main.py [any of the below arguments]

Configuration:
  -c                    Print the current config.json configuration
  -r                    Change role
  -t <OPTION>           Edit the teams list ('add' or 'view')
                          Ex: -t view
                          Ex: -t add
  -e <TYPE> <OPT>       Add an exclusion of a case or product. The 'case' option must be followed by a case #.
                        Use the 'RESET' option to reset the file
                          Ex: -e Case 0156872
                          Ex: -e Case RESET
                          Ex: -e Product

Runtime Options:
  -q                    Simulate SQL against SalesForce
  -s                    Interactive config setup
  -x                    Run in test mode
  -z                    Clean the system-created config files. Does not remove runtime/user defined data

Debug Options:
  -d                    Enable logging
  -dv                   Enable verbose logging
```

### Technical Documentation

**config/config.json**

The ```config.json``` file is the core configuration layer of the application. It defines authentication details, runtime behavior, query logic, and UI customization.

***Top-Level Fields***
```bash
Key                Type                      Description

Username           string                    SalesForce username used for authentication (typically your email)
api_url            string                    Base URL for the SalesForce API endpoint
front_end_board    string                    Optional endpoint for pushing data to a frontend dashboard
engineer_name      string                    Used for filtering queries specific to the logged-in engineer
debug              boolean                   Enabled debug logging when set to ```true```
role               string                    Determines which query logic us used (Engineer vs Manager) and the display
```

```rules``` Object

Controls runtime behavior and polling logic.

```bash
Key                       Type                      Description

poll_interval             int (seconds)             Frequency at which the program polls SalesForce for updates
update_threshold          int (minutes)             Threshold before a case is flagged as nearing SLA breach
vacation_scheduled        boolean                   Enables vacation mode logic
back_from_vacation        string (date)             Date when the engineer returns; used to allow for alerts. Ex: May 19 or December 4
upload_to_tse_board       boolean                   Toggles whether results are pushed to a frontend dashboard
max_buffer_size_bytes     int (bytes)               Maximum size for on-disk response buffering
```

```colors``` Object

Defines UI themeing using the ```rich``` library. For the full list of colors, consult with the 3rd-party library documentation: https://rich.readthedocs.io/en/stable/appendix/colors.html
```bash
Key              Type                Description

send             boolean             Enables/disables notifications (Only on Mac)
color            string              Notification sound identifier (only on Mac)
```
**config/teams.json**

The ```teams.json``` file defines which teams and groups are included in query construction. It acts as a dynamic filter layer that determines whose cases are pulled from SalesForce. Atleast one team must be 'viewable' in order for program to function.

This file can be edited manually or managed via CLI flags:

-t add → Add team members

-t view → Toggle whether a team is included in queries

The ```viewable``` flag must be a boolean type and the ```list``` flag must be comma separated with full engineer names as seen in SalesForce.

**config/excludedCases.cfg**

The ```excludedCases.cfg``` file contains a list of case numbers which will be excluded from the display on the UI. Manual addition to this file is supported however, the ```-e Case <Case #>``` flag can be used when calling this program to add the file.

**config/excludedProducts.cfg**

The ```excludedProducts.cfg``` file contains a list of products which will be excluded from the display on the UI. Manual addition to this file is supported however, the ```-e Product``` flag can be used when calling this program to add the file.

**config/dataBuffer.json** and **config/filereg.json**

These two files shall **not** be manipulated. If these files become corrupted, manual removal is required in order for them to be rebuilt.

**Notifications**

When using this program on Mac, the ability to receive pop-up notifications for cases in the queue is possible. In order to see these notifications, you may need to follow these steps:
1. Open the application Script Editor
2. In the text field copy the following:

    ```display notification "Test notification from Script Editor" with title "Test"```

3. Press the play button
4. A pop-up should appear. If a pop-up does not appear, enable notificates through System Settings.


**Debugging**

Turn on logging capabilities either through the ```config.json``` file, specifically the 'debug' flag. Or call the program with:
1. ```-d``` for info level debug
2. ```-dv``` for verbose level debug