# SalesForce Query

This project helps automate the process of fetching Salesforce cases. It is designed to retrieve team and personal cases based on predefined queries and display relevant information based on the configuration in the `config.json` file.

## Prerequisites

1. **Python 3**: Ensure that Python 3 is installed on your system.
	- You can check this by running: 
		```python3 --version```
	- If you don’t have Python 3 installed, you can download it from the official [Python website](https://www.python.org/downloads/).

2. **Dependencies**: You need the `requests` and `rich` library to interact with the Salesforce API.
	- Install the necessary dependencies by running:
		```pip3 install requests```
    ```pip3 install rich```

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

The program will start and run a validation check for the existance of the credentials.json and config.json file. Since the first startup will not have these files, the program will create them from a template.

### 3. First-Time Setup
In the ```credentials.json``` file, fill out all fields with appropriate values.

Example of credentials.json:
```bash
{
  "url": "https://SalesForce-api.com/query",
  "username": "JohnDoe@Company.com",
  "engineer_name": "First Last"
}
```
In the ```config.json``` file, set the products you support to 'true'.

If you are a manager, update the ```"role": "engineer"``` to ```"role": "manager"```

If you are on Mac, update the ```"notifications": false``` to ```"notifications": true```. Or you can run the program with the --notify flag to override the value in the config.json. Ex ```python3 main.py --notify```

### 4. Start the program

Start the program by running the below command. You will be prompted to enter your password and once complete, should now see relevant information in your terminal for the configured queries.

```bash
python3 main.py
```