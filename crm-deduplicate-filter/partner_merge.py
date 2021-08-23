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

from openerp import api, fields, models


class BasePartnerMergeAutomaticWizard(models.TransientModel):
    _inherit = "base.partner.merge.automatic.wizard"


    exclude_not_active = fields.Boolean("'Active' field not selected")
    exclude_not_company = fields.Boolean("'Is a company?' field not selected")

    @api.multi
    def _process_query(self, query):

        if any([self.exclude_not_company, self.exclude_not_active]):
            filters = []
            if self.exclude_not_company:
                filters.append("is_company = True")
            if self.exclude_not_active:
                filters.append("active = True")
            index_where = query.find('WHERE')
            index_group_by = query.find('GROUP BY')
            subquery = "%s" % ' AND '.join(filters)
            if index_where > 0:
                subquery = "AND (%s) " % subquery
            else:
                subquery = "WHERE %s " % subquery
            query = query[:index_group_by] + subquery + query[index_group_by:]
        return super(BasePartnerMergeAutomaticWizard, self)._process_query(query)
