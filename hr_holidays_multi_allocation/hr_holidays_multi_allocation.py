import logging
from openerp import tools
from openerp.osv import osv, fields

_logger = logging.getLogger(__name__)

class hr_holidays_multi_allocation(osv.osv_memory):
	_name = 'hr.holidays.multi.allocation'
	_description = 'Add allocations for multi-employees'
	
	_columns = {
		'description' : fields.char('Description', required=True, size=64, help='Description of attribution. 64 characters maximum'),
		'holiday_status_id': fields.many2one("hr.holidays.status", "Type of leave requested", required=True, help='Type of leave requested'),
		'days' : fields.float('Duration in days', default=2.08, digits=(4,2), required=True, help='Number of days off to add to each selected employees'), 
		}


	def generete_allocations(self, cr, uid, ids, context=None):
		input = self.read(cr, uid, ids, ['days', 'description', 'holiday_status_id'], context=context)[0]
		_logger.info('DATA : %s', input['holiday_status_id'][0])

		obj_holidays = self.pool.get('hr.holidays')
		obj_employee = self.pool.get('hr.employee')

		for employee in obj_employee.browse(cr, uid, context['active_ids'], context=context):
			allocation_id = obj_holidays.create(cr, uid, {
			"holiday_status_id" : input['holiday_status_id'][0],
			"state" : "confirm",
			"type" : "add",
			"employee_id" : employee.id,
			"name" : input['description'],
			"number_of_days_temp" : str(input['days']) }, context=context)
			obj_holidays.holidays_validate(cr, uid, allocation_id, context=context)
		
		return {}