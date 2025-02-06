## Installation and Usage of the Application

Follow the instructions bellow for installing the required dependencies in Linux:
```bash
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

Follow the instructions bellow for installing the required dependencies in Windows:
```bash
python -m venv venv
venv\Scripts\activate.bat
pip install -r requirements.txt
```

In order to use the final application (final_model.py) open the command line in the folder of the application and use the following command:   
```
python final_model.py [PATH TO THE FILE TO TEST]
```  
Although its important to warn the user that some emails will not function properly due to enconding and strange formats, so we advise to use emails in plain text or html. An example of an .eml file is available in the repository under the name *teste.eml*
