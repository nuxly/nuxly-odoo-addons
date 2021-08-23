# -*- coding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution
#    Copyright (C) 2020 Nuxly SAS <contact@nuxly.com>
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU Affero General Public License as
#    published by the Free Software Foundation, either version 3 of the
#    License, or (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU Affero General Public License for more details.
#
#    You should have received a copy of the GNU Affero General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
##############################################################################

{
    "name": "CRM deduplicate filters",
    "version": "1.0",
    "category": 'Tools',
    "sequence": 20,
    "summary": 'Add some filters to the deduplication wizard',    
    "author": "Nuxly",
    "website": "http://nuxly.com",
    "description": """
CRM deduplicate filters :
=========================

This module add the following features to the deduplication wizard :
--------------------------------------------------------------------
   
    * Exclude results having is_company field not selected
    * Exclude results having active field not selected
    """,

    "depends": ['crm'],
    "images": [],
    "demo": [],
    "data": [
        'partner_merge_view.xml',],
    "active": True,
    "installable": True,
}

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
