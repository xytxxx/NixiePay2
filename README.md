# Script to calculate payments for each member in NixieSubs

## Usage
1. Get your credentials.json from step 1 
[here](https://developers.google.com/sheets/api/quickstart/python). (Prject Name: any thing you like, Then choose "Desktop App")

2. In credentials.json, add your Kanboard API tokens and the id of sheet template as shown: 
```lang-json
"kanboard": {
    "username": "xxxxx",
    "api": "xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx"
},
"sheet": {
    "spreadsheet_id": "1B7dGAgOtPej9vddkTleEvkzIHX1M4OqHwZU-W424jwo",
    "sheet_id": 0
}
```
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
        "username": "xxxx",
        "api": "xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx"
    },
    "sheet": {
        "spreadsheet_id": "1B7dGAgOtPej9vddkTleEvkzIHX1M4OqHwZU-W424jwo",
        "sheet_id": 0
    }
}
```

3. `pip install -r pip-requirements.txt`

4. `python nixiePay.py [Column names to calculate]`

5. Go to your GDrive home page, you should see the newly created spreadsheet
   "LMGNSxxxx", move it to the Nixiesubs folder.
