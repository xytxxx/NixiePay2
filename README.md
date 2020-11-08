# Script to calculate payments for each member in NixieSubs

## Usage
0. Install latest Python 3.

1. Get your credentials.json from step 1 
[here](https://developers.google.com/sheets/api/quickstart/python). (Prject Name: any thing you like, Then choose "Desktop App")

2. In credentials.json, add your Kanboard API tokens and the id of sheet template as shown: 
```lang-json
"kanboard": {
    "username": "jsonrpc",
    "api": "<ROOT KEY FOR KANBOARD>"
},
"sheet": {
    "spreadsheet_id": "1B7dGAgOtPej9vddkTleEvkzIHX1M4OqHwZU-W424jwo",
    "sheet_id": 0
}
```
You can get `ROOT KEY` from admin (布莱克）. 
The spreadsheet_id and sheet_id for template is fixed. You can just copy from
here (as long as you have access to the Nixiesubs folder on GDrive).

Your credentials.json should look like 
```lang-json
{
    "installed": {
        "client_id": "xxxxxxxxxxxxxxxxxx",
        "project_id": "xxxxxxxxxxxxxxxxx",
        ..........
    },
    "kanboard": {
        "username": "jsonrpc",
        "api": "xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx"
    },
    "sheet": {
        "spreadsheet_id": "1B7dGAgOtPej9vddkTleEvkzIHX1M4OqHwZU-W424jwo",
        "sheet_id": 0
    }
}
```

3. Run `pip install -r pip-requirements.txt` in terminal 

4. Run `python nixiePay.py [Column names to calculate, seperated by space]`. For example, `python nixiePay.py 2020-10 2020-09`

5. Go to your GDrive home page, you should see the newly created spreadsheet
   "LMGNSxxxx", move it to the Nixiesubs folder.
