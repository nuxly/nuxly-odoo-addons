# -*- coding: utf-8 -*-
{
    'name': "Odoo.sh Backup to Cloud (Google Drive / OneDrive)",
    'version': '17.0.1.0.0',
    'summary': "Send Odoo.sh automatic backups to Google Drive / OneDrive",
    'description': """
        Ce module hérite de auto_database_backup et ajoute deux options :
        - Sauvegarde Odoo.sh > Google Drive
        - Sauvegarde Odoo.sh > OneDrive

        Il désactive la saisie du master password,
        masque les options inutiles, et utilise uniquement les fonctions 
        de token pour l'envoi dans le cloud. 
    """,
    'author': "Nuxly",
    'category': 'Tools',
    'depends': ['auto_database_backup'],
    'data': [
        'views/db_backup_configure_view.xml',
    ],
    'installable': True,
    'license': 'LGPL-3',
    'application': True,
}
