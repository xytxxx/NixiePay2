# Wrapper for Google Sheet API

import pickle
import os.path
from googleapiclient.discovery import build
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
import json
import re

secret = {}
with open('credentials.json') as f:
    secret = json.load(f)

# If modifying these scopes, delete the file token.pickle.
SCOPES = ["https://www.googleapis.com/auth/drive",
          "https://www.googleapis.com/auth/drive.file",
          "https://www.googleapis.com/auth/spreadsheets"]
# The ID and range of a sample spreadsheet.
TEMPLATE_SPREADSHEET_ID = secret['sheet']['spreadsheet_id']
TEMPLATE_SHEET_ID = secret['sheet']['sheet_id']

class Sheet:
    def __init__(self):
        creds = None
        # The file token.pickle stores the user's access and refresh tokens, and is
        # created automatically when the authorization flow completes for the first
        # time.
        if os.path.exists('token.pickle'):
            with open('token.pickle', 'rb') as token:
                creds = pickle.load(token)
        # If there are no (valid) credentials available, let the user log in.
        if not creds or not creds.valid:
            if creds and creds.expired and creds.refresh_token:
                creds.refresh(Request())
            else:
                flow = InstalledAppFlow.from_client_secrets_file(
                    'credentials.json', SCOPES)
                creds = flow.run_local_server(port=0)
            # Save the credentials for the next run
            with open('token.pickle', 'wb') as token:
                pickle.dump(creds, token)

        self.service = build('sheets', 'v4', credentials=creds)

    def createNewSheetFromTemplate(self, title: str):
        newSheet = {
            'properties': {
                'title': title
            }
        }
        newSheet = self.service.spreadsheets().create(
            body=newSheet,
            fields='spreadsheetId'
        ).execute()
        copy_sheet_to_another_spreadsheet_request_body = {
            'destination_spreadsheet_id': newSheet.get('spreadsheetId')
        }
        self.service.spreadsheets().sheets().copyTo(
            spreadsheetId=TEMPLATE_SPREADSHEET_ID, 
            sheetId=TEMPLATE_SHEET_ID, 
            body=copy_sheet_to_another_spreadsheet_request_body
        ).execute()
        self.service.spreadsheets().batchUpdate(
            spreadsheetId=newSheet.get('spreadsheetId'), 
            body={
                'requests': [
                    {
                        'deleteSheet': {
                            'sheetId': 0
                        }
                    }
                ]
            }
        ).execute()
        allSheets = self.service.spreadsheets().get(
            spreadsheetId=newSheet.get('spreadsheetId')
        ).execute()
        newSheet['id'] = allSheets['sheets'][0]['properties']['sheetId']
        self.service.spreadsheets().batchUpdate(
            spreadsheetId=newSheet.get('spreadsheetId'), 
            body={
                'requests': [
                    {
                        'updateSheetProperties': {
                            'properties': {
                                'sheetId': newSheet.get('id'),
                                'title': 'Table'
                            },
                            'fields': 'title'
                        }
                    }
                ]
            }
        ).execute()
        return newSheet
    
    @staticmethod
    def rangeToGrid(range: str): 
        m = re.match(r'(?P<col1>[A-Z]+)(?P<row1>[0-9]+):(?P<col2>[A-Z]+)(?P<row2>[0-9]+)', range)
        dic = m.groupdict()
        row1 = int(dic['row1']) - 1
        row2 = int(dic['row2']) 
        col1 = ord(dic['col1']) - ord('A') 
        col2 = ord(dic['col2']) - ord('A') + 1
        return {
            'startRowIndex': row1,
            'endRowIndex': row2,
            'startColumnIndex': col1,
            'endColumnIndex': col2
        }        

    def writeValues(self, sheet, range, values):
        body = {
            'range': range,
            'values': values,
            'majorDimension':"ROWS"
        }
        result = self.service.spreadsheets().values().update(
            spreadsheetId=sheet.get('spreadsheetId'), 
            valueInputOption='USER_ENTERED',
            body=body,
            range=range
        ).execute()
        return result

    def writeNotes(self, sheet, range: str, rowsOfNotes):            
        gridRange = self.rangeToGrid(range)
        gridRange['sheetId'] = sheet.get('id')
        noteRows = []
        for notes in rowsOfNotes:
            row = []
            for note in notes:
                row.append({
                    'note': note
                })
            noteRows.append({
                'values': row
            })
        result = self.service.spreadsheets().batchUpdate(
            spreadsheetId=sheet.get('spreadsheetId'), 
            body={
                'requests': [
                    {
                        'updateCells': {
                            'range': gridRange,
                            'rows': noteRows,
                            'fields': 'note'
                        }
                    }
                ]
            }
        ).execute()
        return result



