# -*- coding: utf-8 -*-
from odoo import models, fields, api, _
from odoo.exceptions import ValidationError
from datetime import timedelta
import json
import requests
import logging
import os

_logger = logging.getLogger(__name__)

ONEDRIVE_SCOPE = ['offline_access', 'Files.ReadWrite.All']
GOOGLE_TOKEN_ENDPOINT = 'https://accounts.google.com/o/oauth2/token'
ONEDRIVE_TOKEN_URL = 'https://login.microsoftonline.com/common/oauth2/v2.0/token'

class DbBackupConfigure(models.Model):
    _inherit = 'db.backup.configure'

    backup_destination = fields.Selection(
    selection_add=[
        ('odoo_sh_gdrive', 'Odoo.sh + Google Drive'),
        ('odoo_sh_onedrive', 'Odoo.sh + OneDrive')])
    db_name = fields.Char(required=False)
    master_pwd = fields.Char(required=False)

    @api.constrains('db_name')
    def _check_db_credentials(self):
        #TODO ajout verification odoo sh  backup_destination + xml
        _logger.debug("Skipping DB name check for backup config.")
        return

    def _schedule_auto_backup(self):
        super()._schedule_auto_backup()  # appel de la méthode parent
        _logger.warning("========= SCHEDULE BACKUP CALL =========")
        records = self.search([])
        for rec in records:
            zip_path = "/backup.daily"
            files = sorted(self._list_files(zip_path), reverse=True)
            if not files:
                raise ValidationError("No backup found in backup.daily.")
            backup_file = files[0]
            with open(os.path.join(zip_path, backup_file), "rb") as f:
                content = f.read()
                if rec.backup_destination == 'odoo_sh_gdrive':
                    rec._send_to_gdrive(backup_file, content)
                elif rec.backup_destination == 'odoo_sh_onedrive':
                    rec._send_to_onedrive(backup_file, content)

    def _list_files(self, path):
        try:
            files = [f for f in os.listdir(path) if f.endswith(".zip")]
            _logger.debug("List of .zip files in %s: %s", path, files)
            return files
        except Exception as e:
            _logger.error("Failed to list files in %s: %s", path, str(e))
            return []

    def _send_to_gdrive(self, filename, content):
        _logger.debug("Preparing to upload to Google Drive: %s", filename)

        # Refresh token if expired
        if self.gdrive_token_validity <= fields.Datetime.now():
            _logger.debug("Google token expired, refreshing...")
            self.generate_gdrive_refresh_token()
        headers = {"Authorization": f"Bearer {self.gdrive_access_token}"}
        meta = {
            "name": filename,
            "parents": [self.google_drive_folder_key],}
        files = {
            'data': ('metadata', json.dumps(meta), 'application/json'),
            'file': (filename, content, 'application/zip')}
        res = requests.post(
            "https://www.googleapis.com/upload/drive/v3/files?uploadType=multipart",
            headers=headers, files=files
        )
        _logger.warning("Upload to Google Drive response code: %s", res.status_code)
        _logger.warning("Response content: %s", res.text)
        res.raise_for_status()


    def _send_to_onedrive(self, filename, content):
        _logger.debug("Preparing to upload to OneDrive: %s", filename)
        if self.onedrive_token_validity <= fields.Datetime.now():
            _logger.debug("OneDrive token expired, refreshing...")
            self.generate_onedrive_refresh_token()

        headers = {
            'Authorization': f"Bearer {self.onedrive_access_token}",
            'Content-Type': 'application/json'
        }
        upload_url = f"https://graph.microsoft.com/v1.0/me/drive/items/{self.onedrive_folder_key}:/{filename}:/content"
        res = requests.put(upload_url, headers=headers, data=content)
        _logger.warning("Upload to OneDrive response code: %s", res.status_code)
        res.raise_for_status()
