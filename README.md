# SalesForce Query

This project helps automate the process of fetching Salesforce cases. It is designed to retrieve team and personal cases based on predefined queries and display relevant information based on the configuration in the `config.json` file.

## Prerequisites

1. **Python 3**: Ensure that Python 3 is installed on your system.
	- You can check this by running: 
		```python3 --version```
	- If you don’t have Python 3 installed, you can download it from the official [Python website](https://www.python.org/downloads/).

2. **Dependencies**: You need the `requests` library to interact with the Salesforce API.
	- Install the necessary dependencies by running:
		```pip3 install requests```

## Installation and Setup

### 1. Clone the Repository

First, download or clone the repository to your local machine.

```bash
git clone https://github.com/gdd12/SalesForceQuery.git
```

### 2. First-Time Setup

Navigate to the root directory and run the script.
```bash
cd SalesForceQuery
python3 SalesForce.py
```

The program will start and run a validation check for the existance of the credentials.json file. Since the first startup will not have this file, the program will exit and you can manually enter the credentials in the credentials.json file.

### 3. First-Time Setup
In the ```credentials.json``` file, fill out all fields with appropriate values.

Example of credentials.json:
```bash
{
  "url": "https://SalesForce-api.com/query",
  "username": "JohnDoe@Company.com",
  "password": "SecretPassword123",
  "engineer_name": "John Doe"
}
```

### 4. Start the program

Start the program by running the below command, you should now see relevant information in your terminal for the team queue and your personal queue.

```bash
python3 SalesForce.py
```

You should see something like this:
```bash
Fetching batch @ Mon Mar 31 08:46:26

  1 new Flow Manager case(s)
  3 new API Gateway case(s)
  1 new Transfer CFT case(s)
  1 new Amplify API Platform case(s)

  4 case(s) are In Support

Next poll in 5 minutes...
```