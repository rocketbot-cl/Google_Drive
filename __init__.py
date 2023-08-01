# coding: utf-8
"""
Base para desarrollo de modulos externos.
Para obtener el modulo/Funcion que se esta llamando:
     GetParams("module")

Para obtener las variables enviadas desde formulario/comando Rocketbot:
    var = GetParams(variable)
    Las "variable" se define en forms del archivo package.json

Para modificar la variable de Rocketbot:
    SetVar(Variable_Rocketbot, "dato")

Para obtener una variable de Rocketbot:
    var = GetVar(Variable_Rocketbot)

Para obtener la Opcion seleccionada:
    opcion = GetParams("option")


Para instalar librerias se debe ingresar por terminal a la carpeta "libs"

    pip install <package> -t .

"""
from __future__ import print_function
import os.path
import pickle
import sys

base_path = tmp_global_obj["basepath"]
cur_path = base_path + 'modules' + os.sep + 'gdrive' + os.sep + 'libs' + os.sep


cur_path_x64 = os.path.join(cur_path, 'Windows' + os.sep +  'x64' + os.sep)
cur_path_x86 = os.path.join(cur_path, 'Windows' + os.sep +  'x86' + os.sep)

if cur_path_x64 not in sys.path and sys.maxsize > 2**32:
    sys.path.append(cur_path_x64)
elif cur_path_x86 not in sys.path and sys.maxsize < 2**32:
    sys.path.append(cur_path_x86)

from google.auth.transport.requests import Request
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.http import MediaIoBaseDownload

import magic
from googleapiclient.http import MediaFileUpload
import io

"""
    Obtengo el modulo que fueron invocados
"""
module = GetParams("module")

# creds = None
global creds
global mod_gdrive_session

mimes = {
    'application/vnd.google-apps.spreadsheet': 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
    'application/vnd.google-apps.document': 'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
    # 'application/pdf': 'application/pdf',
    'application/vnd.google-apps.presentation': 'application/vnd.openxmlformats-officedocument.presentationml.presentation'
}


import_formats = {
    ".docx": "application/vnd.google-apps.document",
    ".odt": "application/vnd.google-apps.document",
    ".rtf": "application/vnd.google-apps.document",
    ".pdf": "application/vnd.google-apps.document",
    ".html": "application/vnd.google-apps.document",
    ".xlsx": "application/vnd.google-apps.spreadsheet",
    ".xls": "application/vnd.google-apps.spreadsheet",
    ".ods":	"application/vnd.google-apps.spreadsheet",
    ".csv": "application/vnd.google-apps.spreadsheet",
    ".tsv": "application/vnd.google-apps.spreadsheet",
    ".pptx": "application/vnd.google-apps.presentation",
    ".odp": "application/vnd.google-apps.presentation",
    ".jpg": "application/vnd.google-apps.document",
    ".png": "application/vnd.google-apps.document",
    ".json": "application/vnd.google-apps.script"
}   

export_formats = {
    "Microsoft Word (.docx)": "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
    "OpenDocument (.odt)": "application/vnd.oasis.opendocument.text",
    "Rich Text (.rtf)": "application/rtf",
    "PDF (.pdf)": "application/pdf",
    "Plain Text (.txt)": "text/plain",
    "Web Page (HTML) (.zip)": "application/zip",
    "EPUB (.epub)": "application/epub+zip",
    "Microsoft Excel (.xlsx)": "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    "OpenDocument (.ods)":	"application/x-vnd.oasis.opendocument.spreadsheet",
    "Comma Separated Values (.csv)": "text/csv",
    "Tab Separated Values (.tsv)": "text/tab-separated-values",
    "Microsoft PowerPoint (.pptx)": "application/vnd.openxmlformats-officedocument.presentationml.presentation",
    "ODP (.odp)": "application/vnd.oasis.opendocument.presentation",
    "JPEG (.jpg)": "image/jpeg",
    "PNG (.png)": "image/png",
    "Scalable Vector Graphics (.svg)": "image/svg+xml",
    "JSON (.json)": "application/vnd.google-apps.script+json"
}

session = GetParams("session")
if not session:
    session = ''

try:
    if not mod_gdrive_session : #type:ignore
        mod_gdrive_session = {}
except NameError:
    mod_gdrive_session = {}

if module == "GoogleSuite":
    cred = None

    credential_path = GetParams("credentials_path")
    
    if session == '':
        filename = "token_drive.pickle"
    else:
        filename = "token_drive_{s}.pickle".format(s=session)
    
    filename = os.path.join(base_path, filename)
    
    if not os.path.exists(credential_path):
        raise Exception("El archivo de credenciales no existe en la ruta especificada")

    SCOPES = [
        'https://www.googleapis.com/auth/drive',
        'https://www.googleapis.com/auth/spreadsheets'
    ]

    if os.path.exists(filename):
        with open(filename, 'rb') as token:
            cred = pickle.load(token)
        # If there are no (valid) credentials available, let the user log in.
    if not cred or not cred.valid:
        if cred and cred.expired and cred.refresh_token:
            cred.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(
                credential_path, SCOPES)
            cred = flow.run_local_server()
        # Save the credentials for the next run
        with open(filename, 'wb') as token:
            pickle.dump(cred, token)

    # global creds
    mod_gdrive_session[session] = cred

if not mod_gdrive_session[session]:
    raise Exception("No hay credenciales ni token válidos, por favor configure sus credenciales")

if module == "ListFiles":

    var = GetParams('var_file_list')
    filter_ = GetParams("filter")
    mine = GetParams("mine")
    shared = GetParams("shared")
    
    try:
        # By default the command will get the data from all drives, if mine is checked, then will only bring back files thats have the user as owner.
        if mine and eval(mine):
            if filter_ and filter_ != "": 
                filter_ += " and 'me' in owners"
            else: 
                filter_ = "'me' in owners"
            
        if shared and eval(shared):
            if filter_ and filter_ != "": 
                filter_ += " and sharedWithMe = true"
            else: 
                filter_ = "sharedWithMe = true"        
        
        if filter_ and "'me' in owners" in filter_ and "sharedWithMe = true" in filter_:
            raise Exception ("Can not use both filters ('me' in owners and sharedWithMe = true) in the same query...")
        
        service = build('drive', 'v3', credentials=mod_gdrive_session[session])

        results = service.files().list(
            q=filter_,
            fields="files(id, name, mimeType, parents)",
            pageSize=1000, spaces='drive', includeItemsFromAllDrives=True,
            supportsAllDrives=True, includeLabels=True).execute()
        items = results.get('files', [])
        files = []
        if len(items) > 0:
            for item in items:
                try:
                    parents = item['parents'][0]
                except:
                    parents = ""
                files.append({'name': item['name'], 'id': item['id'], 'mimeType': item['mimeType'], 'parents': parents})
        
        SetVar(var, files)
    except Exception as e:
        print("\x1B[" + "31;40mAn error occurred\x1B[" + "0m")
        PrintException()
        raise e

if module == 'DownloadFile':
    try:
        drive_id = GetParams('drive_id')
        if not drive_id:
            raise Exception("ID de archivo no enviado")

        file_path = GetParams('path_to_file')
        if not file_path:
            raise Exception("No se ingreso ruta donde guardar el archivo")

        service = build('drive', 'v3', credentials=mod_gdrive_session[session])
        file = service.files().get(fileId=drive_id, supportsAllDrives=True).execute()
        
        request = None
        if file['mimeType'] in mimes:
            mime = mimes[file['mimeType']]
            request = service.files().export_media(fileId=drive_id, mimeType=mime)
        else:
            mime = file['mimeType']
            request = service.files().get_media(fileId=drive_id)
        fh = io.BytesIO()
        downloader = MediaIoBaseDownload(fh, request)
        # downloader = MediaIoBaseDownload(fh, request)
        done = False
        while done is False:
            status, done = downloader.next_chunk()
            print("Download %d%%." % int(status.progress() * 100))

        keys = list(export_formats.keys())
        values = list(export_formats.values())
        try:
            index = values.index(mime)
            extension = keys[index].split()[-1][1:-1]
        except:
            extension = ""
        
        filename = file['name'] + extension if extension not in file['name'] else file['name']
        with io.open(file_path + os.sep + filename, 'wb') as out:
            fh.seek(0)
            out.write(fh.read())

    except Exception as e:
        print("\x1B[" + "31;40mAn error occurred\x1B[" + "0m")
        PrintException()
        raise e

if module == 'ExportFile':
    try:
        drive_id = GetParams('drive_id')
        if not drive_id:
            raise Exception("ID de archivo no enviado")

        file_path = GetParams('path_to_file')
        if not file_path:
            raise Exception("No se ingreso ruta donde guardar el archivo")

        export_format = GetParams('format')
        mime = export_formats.get(export_format)
        
        service = build('drive', 'v3', credentials=mod_gdrive_session[session])
        file = service.files().get(fileId=drive_id, supportsAllDrives=True).execute()
        request = None

        request = service.files().export_media(fileId=drive_id, mimeType=mime)
        fh = io.BytesIO()
        downloader = MediaIoBaseDownload(fh, request)

        done = False
        while done is False:
            status, done = downloader.next_chunk()
            print("Download %d%%." % int(status.progress() * 100))

        extension = export_format.split()[-1][1:-1]
        
        with io.open(file_path + os.sep + file['name'] + extension, 'wb') as out:
            fh.seek(0)
            out.write(fh.read())

    except Exception as e:
        print("\x1B[" + "31;40mAn error occurred\x1B[" + "0m")
        PrintException()
        raise e

if module == 'CreateFolder':
    try:
        var = GetParams('var')
        folder_name = GetParams('folder_name')
        parent_id = GetParams('parent_id')

        body = {
            'name': folder_name,
            'mimeType': "application/vnd.google-apps.folder"
        }
        
        if parent_id:
            body['parents'] = [parent_id]

        service = build('drive', 'v3', credentials=mod_gdrive_session[session])
        root_folder = service.files().create(body=body, supportsAllDrives=True).execute()

        if var:
            SetVar(var, root_folder)

    except Exception as e:
        print("\x1B[" + "31;40mAn error occurred\x1B[" + "0m")
        PrintException()
        raise e

if module == 'CopyMoveFile':
    try:
        var = GetParams('var')
        folder_id = GetParams('folder_id')
        file_id = GetParams('file_id')

        if not folder_id or not file_id:
            raise Exception("No ha ingresado archivo o carpeta")

        option = GetParams('options')

        service = build('drive', 'v3', credentials=mod_gdrive_session[session])
        
        file_to_move = service.files().get(fileId=file_id,
                                           fields='parents, name', supportsAllDrives=True).execute()
        
        previous_parents = ",".join(file_to_move.get('parents'))

        copy = option == "copy"

        parents = folder_id
        
        if copy:
            file_id = service.files().copy(fileId=file_id, supportsAllDrives=True).execute()["id"]

        file = service.files().update(fileId=file_id,
                                      removeParents = previous_parents,
                                      addParents = parents,
                                      enforceSingleParent = True,
                                      fields='id, parents, name',
                                      supportsAllDrives=True).execute()

        if copy:
            file = service.files().update(fileId=file_id,
                                          body={
                                              "name": file_to_move["name"]
                                          },
                                          fields='id, name, parents', 
                                          supportsAllDrives=True).execute()

        if var:
            SetVar(var, file)


    except Exception as e:
        print("\x1B[" + "31;40mAn error occurred\x1B[" + "0m")
        PrintException()
        raise e

if module == "UploadFile":
    try:
        file_path = GetParams("file_path")

        if not file_path:
            raise Exception("No ha ingresado una ruta")

        if not os.path.exists(file_path):
            raise Exception("Archivo ingresado no existe")

        new_name = GetParams("new_name")
        folder = GetParams("folder")
        convert = GetParams("convert")
        var = GetParams("var")

        service = build('drive', 'v3', credentials=mod_gdrive_session[session])

        mimeType = None
        if convert and eval(convert) == True:
            filename, file_extension = os.path.splitext(file_path)
            mimeType = import_formats.get(file_extension, None)
 
        file_mime = magic.from_file(file_path, mime=True)

        if file_path.endswith('.csv'):
            file_mime = 'text/csv'
        if file_path.endswith('.xlsx'):
            file_mime = 'application/vnd.ms-excel'

        name = new_name or os.path.basename(file_path)

        file_metadata = {'name': name, 'mimeType': mimeType} if mimeType else  {'name': name}
        media = MediaFileUpload(file_path,
                                mimetype=file_mime)

        if folder:
            file_metadata['parents'] = [folder]

        file = service.files().create(body=file_metadata,
                                      media_body=media,
                                      fields='id', supportsAllDrives=True).execute()
        if var:
            SetVar(var, file)

    except Exception as e:
        print("\x1B[" + "31;40mAn error occurred\x1B[" + "0m")
        PrintException()
        raise e

if module == "DeleteFile":
    try:
        file_id = GetParams("file_id")
        if not file_id:
            raise Exception("No ha ingresado un ID")
        service = build('drive', 'v3', credentials=mod_gdrive_session[session])
        result = GetParams("result")
            
        file = service.files().delete(fileId=file_id, supportsAllDrives=True).execute()
        SetVar(result, True)

    except Exception as e:
        SetVar(result, False)
        print("\x1B[" + "31;40mAn error occurred\x1B[" + "0m")
        PrintException()
        raise e

if module == "ShareFile":
    try:
        file_id = GetParams("file_id")
        if not file_id:
            raise Exception("No ha ingresado un ID")
        service = build('drive', 'v3', credentials=mod_gdrive_session[session])
        result = GetParams("result")

        service.permissions().create(body={"role": "reader", "type": "anyone"}, fileId=file_id).execute()
        SetVar(result, True)

    except Exception as e:
        SetVar(result, False)
        print("\x1B[" + "31;40mAn error occurred\x1B[" + "0m")
        PrintException()
        raise e