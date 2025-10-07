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

### 3. First-Time Setup
The program will prompt you to enter the configuration - follow the wizard.

IMPORTANT: Entering the incorrect role is an irreversible change!

### Configurable after setup:
If you see a product missing from this tool you can perform the following to add it:
1. If a silentConfig.json is located in config/ you can it to the 'supported_products' section with the value of 'True'
2. If there is no silentConfig.json, add the product to the config.json located in config/ with the value of 'True'