# -*- coding: utf-8 -*-
{
    'name': 'Multiple allocation of days off',
    'version': '1.0',
    'category': 'Human Resources',
    'description': """ 
DESCRIPTION
-----------
* Adds an option in the 'More' menu : Allocation management
* Adds leave for all selected employees
* Adds leave to the employee whose record is displayed""",
    'author': 'Nuxly',
    'website' : "http://nuxly.com",
    'depends': [
    	'hr_holidays',
    	],
    'data': [
    	'hr_holidays_multi_allocation_view.xml'
    	],
    'installable': True,
    'auto_install': False,
}
