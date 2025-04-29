# -*- coding: utf-8 -*-
from odoo import models, fields, api, _
from datetime import datetime
import json
import requests
import logging
import os
import tempfile
import shutil
import odoo.tools.osutil
from odoo.exceptions import UserError
_logger = logging.getLogger(__name__)

class DbBackupConfigure(models.Model):
    _inherit = 'db.backup.configure'
    # Extend available backup destinations to add 2 destinations for Odoo.sh
    backup_destination = fields.Selection(
    selection_add=[
        ('odoo_sh_gdrive', 'Odoo.sh + Google Drive'),
        ('odoo_sh_onedrive', 'Odoo.sh + OneDrive')])
    db_name = fields.Char(required=False)
    master_pwd = fields.Char(required=False)

    @api.constrains('db_name')
    def _check_db_credentials(self):
        """
        Override constraint to bypass DB credential check
        when using Odoo.sh (where it's unnecessary).
        """
        _logger.debug("Skipping DB name check for backup config.")
        return

    def _schedule_auto_backup(self):
        """
        Override Odoo's base method to add support for:
        - Creating and zipping Odoo.sh backups from /backup.daily
        - Sending them to Google Drive or OneDrive
        - Auto-removing old backups from cloud if enabled
        """
        super()._schedule_auto_backup() 
        _logger.warning("========= SCHEDULE BACKUP CALL =========")
        records = self.search([])
        for rec in records:
            if rec.backup_destination not in ['odoo_sh_gdrive', 'odoo_sh_onedrive']:
                continue
            filename, content = rec._extract_daily_backup_zip()
            if not filename:
                continue
            try:
                # Google Drive backup Odoo.sh
                if rec.backup_destination == 'odoo_sh_gdrive':
                    rec._send_to_gdrive(filename, content)
                    if rec.auto_remove:
                        headers = {"Authorization": f"Bearer {rec.gdrive_access_token}"}
                        query = f"parents = '{rec.google_drive_folder_key}'"
                        files_req = requests.get(
                            f"https://www.googleapis.com/drive/v3/files?q={query}",
                            headers=headers)
                        for file in files_req.json().get('files', []):
                            meta = requests.get(
                                f"https://www.googleapis.com/drive/v3/files/{file['id']}?fields=createdTime",
                                headers=headers)
                            created = meta.json().get('createdTime', '')[:19].replace('T', ' ')
                            days = (fields.Datetime.now() - fields.datetime.strptime(created, '%Y-%m-%d %H:%M:%S')).days
                            if days >= rec.days_to_remove:
                                requests.delete(f"https://www.googleapis.com/drive/v3/files/{file['id']}", headers=headers)
                # Onedrive Backup Odoo.sh
                elif rec.backup_destination == 'odoo_sh_onedrive':
                    rec._send_to_onedrive(filename, content)
                    if rec.auto_remove:
                        headers = {'Authorization': f"Bearer {rec.onedrive_access_token}"}
                        list_url = f"https://graph.microsoft.com/v1.0/me/drive/items/{rec.onedrive_folder_key}/children"
                        response = requests.get(list_url, headers=headers)
                        for file in response.json().get('value', []):
                            created = file['createdDateTime'][:19].replace('T', ' ')
                            days = (fields.Datetime.now() - fields.datetime.strptime(created, '%Y-%m-%d %H:%M:%S')).days
                            if days >= rec.days_to_remove:
                                delete_url = f"https://graph.microsoft.com/v1.0/me/drive/items/{file['id']}"
                                requests.delete(delete_url, headers=headers)
                if rec.notify_user:
                        self.env.ref('auto_database_backup.mail_template_data_db_backup_successful').send_mail(rec.id, force_send=True)
            except Exception as e:
                rec.generated_exception = str(e)
                _logger.exception("ODoo.sh Backup failed: %s", e)
                if rec.notify_user:
                    self.env.ref('auto_database_backup.mail_template_data_db_backup_failed').send_mail(rec.id, force_send=True)

    def _extract_daily_backup_zip(self):
        """
        Scan folder /backup.daily in oOdoo.sh and zip any folder or file containing 'daily'
        into a temporary ZIP archive for cloud upload.
        """
        zip_path = "backup.daily"
        temp_dir = tempfile.mkdtemp()
        found = False
        if not zip_path:
            _logger.warning(f"Le dossier {zip_path} est introuvable")
            raise UserError(_("Le dossier de sauvegarde 'backup.daily' est introuvable. Vérifiez la configuration de votre environnement."))
        _logger.debug("Scanning directory: %s", zip_path)
        entries = os.listdir(zip_path)
        _logger.debug("Entries found: %s", entries)
        for f in entries:
            _logger.debug("Checking entry: %s", f)
            if 'daily' in f.lower():
                found = True
                abs_src = os.path.join(zip_path, f)
                abs_dst = os.path.join(temp_dir, f)
                if os.path.isdir(abs_src):
                    _logger.warning("Copying directory: %s", abs_src)
                    shutil.copytree(abs_src, abs_dst)
                else:
                    _logger.warning("Copying file: %s", abs_src)
                    shutil.copy2(abs_src, abs_dst)
        if not found:
            _logger.debug("No file or folder with 'daily' found in %s", zip_path)
            shutil.rmtree(temp_dir, ignore_errors=True)
            return None, None
        temp_zip = tempfile.NamedTemporaryFile(delete=False)
        odoo.tools.osutil.zip_dir(temp_dir, temp_zip, include_dir=False)
        temp_zip.seek(0)
        filename = f"backup_{datetime.today().strftime('%Y-%m-%d')}.zip"
        content = temp_zip.read()
        temp_zip.close()
        shutil.rmtree(temp_dir, ignore_errors=True)
        _logger.debug("Created zip archive: %s", filename)
        return filename, content

    # Upload a ZIP backup to Google Drive
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
        _logger.debug("Upload to Google Drive response code: %s", res.status_code)
        _logger.debug("Response content: %s", res.text)
        res.raise_for_status()

    # Upload a ZIP backup to OneDrive
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
        _logger.debug("Upload to OneDrive response code: %s", res.status_code)
        res.raise_for_status()
