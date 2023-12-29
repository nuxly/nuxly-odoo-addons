#-*- coding:utf-8 -*-

import base64
import io

from odoo import models, fields, api, _
from odoo.exceptions import UserError, AccessDenied
from odoo.tools import float_is_zero, pycompat
from odoo.tools.misc import get_lang
from datetime import date

import logging
logger = logging.getLogger(__name__)

class AccountFrFecUnique(models.TransientModel):
    _inherit = 'account.fr.fec'

    # Adding requested field to filter unique export only
    unique_export = fields.Boolean(string='Unique Export', help="If enabled, generates accounting entries exclusively for those that haven't been exported, using the 'exported_date' field.")
    
    # Make 'date_from' and 'date_to' non-required for future changes.
    date_from = fields.Date(required=False)
    date_to = fields.Date(required=False)
    
    
    # Update this method to handle unique export
    def mark_exported_unique(self):
        # Ensure there is only one record (singleton) for this wizard
        self.ensure_one()

        # Check if unique export is enabled and it's not a test file
        if self.unique_export and not self.test_file:
            # Retrieve entries that have not been exported
            entries_to_export = self.env['account.move'].search([
                ('exported_date', '=', False)
            ])
            logger.warning("les entree : %s" % entries_to_export)
            
            # Check filters for dates (date_from and date_to)
            if self.date_from:
                entries_to_export = entries_to_export.filtered(lambda record: record.date >= self.date_from)
                logger.warning("les entree a exporter date_from  : %s" % entries_to_export)

            if self.date_to:
                entries_to_export = entries_to_export.filtered(lambda record: record.date <= self.date_to)
                logger.warning("les entree  a exporter date_to : %s" % entries_to_export)

            # Mark the entries as exported
            entries_to_export.mark_exported()


    # Overriding the original method to customize FEC generation
    # Adding conditions and modifications generates FEC exclusively for those that haven't been exported.
    def generate_fec(self):
        self.ensure_one()
        if not (self.env.is_admin() or self.env.user.has_group('account.group_account_user')):
            raise AccessDenied()
        # We choose to implement the flat file instead of the XML
        # file for 2 reasons :
        # 1) the XSD file impose to have the label on the account.move
        # but Odoo has the label on the account.move.line, so that's a
        # problem !
        # 2) CSV files are easier to read/use for a regular accountant.
        # So it will be easier for the accountant to check the file before
        # sending it to the fiscal administration
        
        #######################
        # PATCH STARTS HERE   #
        #######################
 
        # Management of start date and end date:
        # Initialize 'date_from' to January 1, 1900, if no start date is specified and unique export is enabled.
        if not self.date_from and self.unique_export:
            self.date_from = date(1900, 1 ,1)
        # Initialize 'date_to' to the current date if no end date is specified and unique export is enabled.
        if not self.date_to and self.unique_export:
            self.date_to = fields.Date.today()
       
        
        today = fields.Date.today()
        if self.date_from and self.date_from > today:
            raise UserError(_('You could not set the start date or the end date in the future.'))
        if self.date_to and self.date_to > today:
            raise UserError(_('You could not set the start date or the end date in the future.'))
        if self.date_from >= self.date_to:
            raise UserError(_('The start date must be inferior to the end date.'))

                 
        #######################
        # PATCH ENDS HERE     #
        #######################       


        company = self.env.company
        company_legal_data = self._get_company_legal_data(company)

        header = [
            u'JournalCode',    # 0
            u'JournalLib',     # 1
            u'EcritureNum',    # 2
            u'EcritureDate',   # 3
            u'CompteNum',      # 4
            u'CompteLib',      # 5
            u'CompAuxNum',     # 6  We use partner.id
            u'CompAuxLib',     # 7
            u'PieceRef',       # 8
            u'PieceDate',      # 9
            u'EcritureLib',    # 10
            u'Debit',          # 11
            u'Credit',         # 12
            u'EcritureLet',    # 13
            u'DateLet',        # 14
            u'ValidDate',      # 15
            u'Montantdevise',  # 16
            u'Idevise',        # 17
            ]
        

        #######################
        # PATCH STARTS HERE   #
        #######################
        if self.unique_export:
            rows_to_write = [header]
            # INITIAL BALANCE
            unaffected_earnings_account = self.env['account.account'].search([
                ('account_type', '=', 'equity_unaffected'),
                ('company_id', '=', company.id)
            ], limit=1)

            if self.pool['account.account'].name.translate:
                lang = self.env.user.lang or get_lang(self.env).code
                aa_name = f"COALESCE(aa.name->>'{lang}', aa.name->>'en_US')"
            else:
                aa_name = "aa.name"
            
            for row in self._cr.fetchall():
                listrow = list(row)
                account_id = listrow.pop()
                rows_to_write.append(listrow)

            # LINES
            if self.pool['account.journal'].name.translate:
                lang = self.env.user.lang or get_lang(self.env).code
                aj_name = f"COALESCE(aj.name->>'{lang}', aj.name->>'en_US')"
            else:
                aj_name = "aj.name"

            query_limit = int(self.env['ir.config_parameter'].sudo().get_param('l10n_fr_fec.batch_size', 500000)) # To prevent memory errors when fetching the results
            
            # Add to the sql request condition for unique export: filter out entries that have been already exported
            sql_query = f'''
            SELECT
                REGEXP_REPLACE(replace(aj.code, '|', '/'), '[\\t\\r\\n]', ' ', 'g') AS JournalCode,
                REGEXP_REPLACE(replace({aj_name}, '|', '/'), '[\\t\\r\\n]', ' ', 'g') AS JournalLib,
                REGEXP_REPLACE(replace(am.name, '|', '/'), '[\\t\\r\\n]', ' ', 'g') AS EcritureNum,
                TO_CHAR(am.date, 'YYYYMMDD') AS EcritureDate,
                aa.code AS CompteNum,
                REGEXP_REPLACE(replace({aa_name}, '|', '/'), '[\\t\\r\\n]', ' ', 'g') AS CompteLib,
                CASE WHEN aa.account_type IN ('asset_receivable', 'liability_payable')
                THEN
                    CASE WHEN rp.ref IS null OR rp.ref = ''
                    THEN rp.id::text
                    ELSE replace(rp.ref, '|', '/')
                    END
                ELSE ''
                END
                AS CompAuxNum,
                CASE WHEN aa.account_type IN ('asset_receivable', 'liability_payable')
                THEN COALESCE(REGEXP_REPLACE(replace(rp.name, '|', '/'), '[\\t\\r\\n]', ' ', 'g'), '')
                ELSE ''
                END AS CompAuxLib,
                CASE WHEN am.ref IS null OR am.ref = ''
                THEN '-'
                ELSE REGEXP_REPLACE(replace(am.ref, '|', '/'), '[\\t\\r\\n]', ' ', 'g')
                END
                AS PieceRef,
                TO_CHAR(COALESCE(am.invoice_date, am.date), 'YYYYMMDD') AS PieceDate,
                CASE WHEN aml.name IS NULL OR aml.name = '' THEN '/'
                    WHEN aml.name SIMILAR TO '[\\t|\\s|\\n]*' THEN '/'
                    ELSE REGEXP_REPLACE(replace(aml.name, '|', '/'), '[\\t\\n\\r]', ' ', 'g') END AS EcritureLib,
                replace(CASE WHEN aml.debit = 0 THEN '0,00' ELSE to_char(aml.debit, '000000000000000D99') END, '.', ',') AS Debit,
                replace(CASE WHEN aml.credit = 0 THEN '0,00' ELSE to_char(aml.credit, '000000000000000D99') END, '.', ',') AS Credit,
                CASE WHEN rec.name IS NULL THEN '' ELSE rec.name END AS EcritureLet,
                CASE WHEN aml.full_reconcile_id IS NULL THEN '' ELSE TO_CHAR(rec.create_date, 'YYYYMMDD') END AS DateLet,
                TO_CHAR(am.date, 'YYYYMMDD') AS ValidDate,
                CASE
                    WHEN aml.amount_currency IS NULL OR aml.amount_currency = 0 THEN ''
                    ELSE replace(to_char(aml.amount_currency, '000000000000000D99'), '.', ',')
                END AS Montantdevise,
                CASE WHEN aml.currency_id IS NULL THEN '' ELSE rc.name END AS Idevise
            FROM
                account_move_line aml
                LEFT JOIN account_move am ON am.id=aml.move_id
                LEFT JOIN res_partner rp ON rp.id=aml.partner_id
                JOIN account_journal aj ON aj.id = am.journal_id
                JOIN account_account aa ON aa.id = aml.account_id
                LEFT JOIN res_currency rc ON rc.id = aml.currency_id
                LEFT JOIN account_full_reconcile rec ON rec.id = aml.full_reconcile_id
            WHERE
                am.date >= %s
                AND am.date <= %s
                AND am.company_id = %s
                {"AND am.state = 'posted'" if self.export_type == 'official' else ""}
                {"AND am.exported_date IS NULL" if self.unique_export else ""}
            ORDER BY
                am.date,
                am.name,
                aml.id
            LIMIT %s
            OFFSET %s
            '''
            #######################
            # PATCH ENDs HERE     
            # #
            #######################

            with io.BytesIO() as fecfile:
                csv_writer = pycompat.csv_writer(fecfile, delimiter='|', lineterminator='')

                # Write header and initial balances
                for initial_row in rows_to_write:
                    initial_row = list(initial_row)
                    # We don't skip \n at then end of the file if there are only initial balances, for simplicity. An empty period export shouldn't happen IRL.
                    initial_row[-1] += u'\r\n'
                    csv_writer.writerow(initial_row)

                # Write current period's data
                query_offset = 0
                has_more_results = True
                while has_more_results:
                    self._cr.execute(
                        sql_query,
                        (self.date_from, self.date_to, company.id, query_limit + 1, query_offset)
                    )
                    query_offset += query_limit
                    has_more_results = self._cr.rowcount > query_limit # we load one more result than the limit to check if there is more
                    query_results = self._cr.fetchall()
                    for i, row in enumerate(query_results[:query_limit]):
                        if i < len(query_results) - 1:
                            # The file is not allowed to end with an empty line, so we can't use lineterminator on the writer
                            row = list(row)
                            row[-1] += u'\r\n'
                        csv_writer.writerow(row)

                base64_result = base64.encodebytes(fecfile.getvalue())

            end_date = fields.Date.to_string(self.date_to).replace('-', '')
            suffix = ''
            if self.export_type == "nonofficial":
                suffix = '-NONOFFICIAL'

            self.write({
                'fec_data': base64_result,
                # Filename = <siren>FECYYYYMMDD where YYYMMDD is the closing date
                'filename': '%sFEC%s%s.csv' % (company_legal_data, end_date, suffix),
                })

            # Set fiscal year lock date to the end date (not in test)
            fiscalyear_lock_date = self.env.company.fiscalyear_lock_date
            if not self.test_file and (not fiscalyear_lock_date or fiscalyear_lock_date < self.date_to):
                self.env.company.write({'fiscalyear_lock_date': self.date_to})
            
            #######################
            # PATCH STARTS HERE   #
            #######################
            
            # Mark as exported all accounting entries that have been exported
            self.mark_exported_unique()

            #######################
            # PATCH ENDS HERE     #
            #######################
        
            return {
                'name': 'FEC',
                'type': 'ir.actions.act_url',
                'url': "web/content/?model=account.fr.fec&id=" + str(self.id) + "&filename_field=filename&field=fec_data&download=true&filename=" + self.filename,
                'target': 'self',
            }
        else: 
            return super(AccountFrFecUnique, self).generate_fec()
    
