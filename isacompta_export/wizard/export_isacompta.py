from odoo import fields, models, _
from datetime import datetime
from odoo.exceptions import UserError
import logging
import unicodedata

_logger = logging.getLogger(__name__)

INVOICE_TYPE = {
    'out_invoice': 'FC',
    'in_invoice': 'FF',
    'out_refund': 'AC',
    'in_refund': 'AF',
    '_other_': 'OD',
}
EMAIL_FROM = "No Reply<noc@nuxly.com>"
EMAIL_TO_DEFAULT = "<clients@nuxly.com>"


class AccountExport(models.TransientModel):
    _name = "account.export"
    _description = "Export ISACOMPTA"
    _inherit = ['mail.thread']

    """
    This wizard to export posted account move
    """

    # Use to set confirm exported message
    #message = fields.Text('Message', required=True)
    simulation = fields.Boolean(
        'Simulate the export',
        help="If true, moves will not be tagged as 'exported', but ISACOMPTA file will be generated.")

    # Close confirm wizard
    def confirm_ok(self):
        return {'type': 'ir.actions.act_window_close'}

    def largeur_fixe(self, string, size, patern, align):
        if isinstance(string, str):
            string = string.encode()
        if align == 'r':
            return string[0:size].rjust(size, patern.encode())
        else:
            return string[0:size].ljust(size, patern.encode())

    def export_isacompta(self):

        _logger.info("debut d'export isacompta.......")
        obj_move = self.env['account.move']
        obj_partners = self.env['res.partner']
        filename = []

        moves_exported_ids = self.env['account.move']  # id des mouv exportés pour flaguer

        # tableau des types de journaux qui sont exportés
        # types possibles : sale / sale_refund / purchase / purchase_refund / cash / bank / general / situation
        journal_types = ['sale', 'sale_refund', 'purchase', 'purchase_refund', 'bank', 'general']
        export_date = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        charset = 'utf8'

        # récupération de ID du User courant
        current_user = self.env.user

        # Nombre d'écriture
        nbEcriture = 0

        company = current_user.company_id

        ids_move = obj_move.search([('state', '=', 'posted'), ('exported_date', '=', False),
                                    ('company_id', '=', company.id)], order="name")

        """ Get all partners
        ids_partner = obj_partners.search([('display_name', '!=', ' ')], order="name")
        for par in ids_partner:
            _logger.info('partner_display_name : "{}" .'.format(par.display_name))
        """

        if not ids_move:
            _logger.info('Sorry: No item to export for "{}" company.'.format(company.name))
            return {
                'name': _('Echec d\'opération'),
                'type': 'ir.actions.act_window',
                'view_mode': 'form',
                'res_model': 'account.export',
                'views': [(self.env.ref('isacompta_export.message_wizard_form').id, 'form')],
                'target': 'new'
            }

        filename.append('/tmp/odoo/{}_isacompta_{}.txt'.format(datetime.now().strftime("%Y-%m-%d_%H-%M-%S"),
                                                               company.partner_id.name))
        try:
            fcompta = open(filename[0], 'w')
        except Exception:
            raise UserError(_('Impossible de creer le fichier !'))

        erreurs = ''

        plan_ecr_comptable = {}
        plan_cpt_comptable = {}

        # Echéance des mouvements
        ecr_echmvt = b""

        # (Entête) Création de version (obligatoire au début du fichier comptable)
        ecr_ln = b"VER   02000000000"
        ecr_ln += self.largeur_fixe("0", 30, ' ', 'l')
        ecr_ln += self.largeur_fixe("0", 31, ' ', 'l')
        ecr_ln += b"0"
        fcompta.write(ecr_ln.decode('ascii') + '\n')

        # Création de dossier isacompta
        dos_ecr = b"DOS   88888880LibelleA30caracteresplusquedixc"
        dos_ecr += self.largeur_fixe(" ", 42, ' ', 'l')
        fcompta.write(dos_ecr.decode('ascii') + '\n')

        # Crétaion d'exercice
        now = datetime.now()
        exo_ecr = b"EXO   0101"
        exo_ecr += now.strftime('%Y').encode()
        exo_ecr += b"3112"
        exo_ecr += now.strftime('%Y').encode()
        exo_ecr += self.largeur_fixe("0", 24, ' ', 'l')
        fcompta.write(exo_ecr.decode('ascii') + '\n')

        last_ecr = None
        ar = []
        # Parcours les mouvements
        for move in ids_move:
            # ne traite que les moves appartennant à une liste précise de type de journal
            if move.journal_id.type not in journal_types:
                continue

            # Ajout de l'ID du move dans le tab pour flagger en "exported" si pas d'erreur au global
            moves_exported_ids += move

            # Création d'une pièce comptable
            ecr_ecr = b"ECR   " + self.largeur_fixe(move.line_ids[0].journal_id.code, 2, ' ', 'l')
            ecr_ecr += move.line_ids[0].date.strftime('%d%m%y').encode()
            if move.line_ids[0].ref:
                ecr_ecr += self.largeur_fixe(move.line_ids[0].ref, 8, ' ', 'l')
            else:
                ecr_ecr += self.largeur_fixe(" ", 8, ' ', 'l')
            if move.line_ids[0].name:
                ecr_ecr += self.largeur_fixe(move.line_ids[0].name, 30, ' ', 'l')
            else:
                ecr_ecr += self.largeur_fixe(" ", 30, ' ', 'l')
            ecr_ecr += self.largeur_fixe(" ", 187, ' ', 'l')
            ecr_ecr += self.largeur_fixe(" ", 10, ' ', 'l')
            ecr_ecr += self.largeur_fixe(" ", 25, ' ', 'l')
            if move.line_ids[0].ref:
                ecr_ecr += self.largeur_fixe(move.line_ids[0].ref, 15, ' ', 'l')
            else:
                ecr_ecr += self.largeur_fixe(" ", 15, ' ', 'l')
            # ecr_ecr += self.largeur_fixe(" ", 10, ' ', 'l')

            # new entrie
            new_ecr = True
            # Parcours des lignes du mouvement courant
            for line in move.line_ids:
                # Incrémente le nombre d'écritude
                nbEcriture += 1

                s = ''
                # Les lignes dont le montant est à 0 ne sont pas pris en compte dans l'export
                if (line.debit == 0) and (line.credit == 0):
                    _logger.info('export_isacompta // line ignored because debit and credit are null')
                else:
                    # Compte et Nom de comtpe
                    compte_tmp = b''
                    plan_comptable = {}

                    # cas client
                    if (line.account_id.code[:3] == '411') and (line.partner_id):
                        # vérif sur code client saisi
                        if not line.partner_id.isacompta_customer_code:
                            erreurs += "ERROR : Invoice " + move.name + " : missing isacompta customer code (see Accounting tab) for company " + line.partner_id.name + "\n"
                            compte_tmp += b'undefined'
                        else:
                            compte_tmp += unicodedata.normalize('NFKD', line.partner_id.isacompta_customer_code).encode(
                                'ASCII', 'ignore')

                    # cas fournisseur
                    elif (line.account_id.code[:3] == '401') and (line.partner_id):
                        # vérif sur code fournisseur saisi
                        if not line.partner_id.isacompta_supplier_code:
                            erreurs += "ERROR : Invoice " + move.name + " : missing isacompta supplier code (see Accounting tab) for company " + line.partner_id.name + "\n"
                            compte_tmp += b'undefined'
                        else:
                            compte_tmp += unicodedata.normalize('NFKD', line.partner_id.isacompta_supplier_code).encode(
                                'ASCII', 'ignore')

                    # cas compte comptable - 8 caractères
                    else:
                        compte_tmp += unicodedata.normalize('NFKD', (line.account_id.code + "000")[0:8]).encode('ASCII',
                                                                                                                'ignore')

                    # Création de mouvement
                    ecr_mvt = b"MVT   "
                    ecr_mvt += self.largeur_fixe(compte_tmp, 10, ' ', 'l')
                    # libellé mouvement
                    ecr_mvt += self.largeur_fixe(
                        unicodedata.normalize('NFKD', line.name.replace("\n", "")).encode('ascii', 'ignore'), 30, ' ',
                        'l')
                    # Montant débit et crédit
                    if int(line.debit * 100) > 0:
                        ecr_mvt += self.largeur_fixe(str(int(line.debit * 100)), 13, '0', 'r')
                        ecr_mvt += self.largeur_fixe(" ", 13, ' ', 'l')
                    elif int(line.credit * 100) > 0:
                        ecr_mvt += self.largeur_fixe(str(int(line.credit * 100)), 26, '0', 'r')

                    ecr_mvt += b"CNW50"
                    """
                    # Autre informations (quantité 1 et 2 + numéro)
                    ecr_mvt += self.largeur_fixe(" ", 30, ' ', 'l')
                    # TVA et lettrage
                    ecr_mvt += self.largeur_fixe(" ", 20, ' ', 'l')
                    """
                    # Date échéance et flag échéance
                    if line.date_maturity:
                        ecr_mvt += b'1'
                        ecr_echmvt = b"ECHMVT"
                        # Montant TTC
                        if int(line.debit * 100) > 0:
                            ecr_echmvt += self.largeur_fixe(str(int(line.debit * 100)), 13, '0', 'r')
                        elif int(line.credit * 100) > 0:
                            ecr_echmvt += self.largeur_fixe(str(int(line.credit * 100)), 13, '0', 'r')
                        # Taux TTC
                        ecr_echmvt += self.largeur_fixe(" ", 10, ' ', 'l')
                        # Date échéance
                        ecr_echmvt += line.date_maturity.strftime('%d%m%y').encode()
                    else:
                        ecr_mvt += b'0'

                    ecr_mvt += b"CNW+100"
                    
                    # date déclaration et code TVA 2, 3
                    ecr_mvt += self.largeur_fixe(" ", 12, ' ', 'l')
                    # Filler (*3 : 3, 5, 8)
                    ecr_mvt += self.largeur_fixe(" ", 16, ' ', 'l')
                    # Date de valeur et libre
                    ecr_mvt += self.largeur_fixe(" ", 25, ' ', 'l')
                    # Libellé de compte
                    ecr_mvt += self.largeur_fixe(" ", 30, ' ', 'l')
                    # Modification de mouvement
                    ecr_mvt += self.largeur_fixe(" ", 14, ' ', 'l')
                    # Taux TVA
                    ecr_mvt += self.largeur_fixe(" ", 5, ' ', 'l')
                    
                    # Code devise
                    if move.currency_id:
                        ecr_mvt += self.largeur_fixe(move.currency_id.name, 3, ' ', 'l')
                    else:
                        ecr_mvt += b"EUR"
                    # montant devise
                    if move.currency_id and move.currency_id.name != "EUR":
                        if int(line.amount_currency) > 0:
                            ecr_mvt += self.largeur_fixe(str(abs(int(line.amount_currency * 100))), 11, '0', 'r')
                            ecr_mvt += self.largeur_fixe(" ", 11, ' ', 'l')
                        else:
                            ecr_mvt += self.largeur_fixe(str(abs(int(line.amount_currency * 100))), 22, '0', 'r')
                    else:
                        ecr_mvt += self.largeur_fixe(" ", 22, ' ', 'l')
                    # Taux de change
                    ecr_mvt += self.largeur_fixe(" ", 8, ' ', 'l')
                    # Filler (*7 : 5, 5, 5, 2, 8, 3, 1)
                    ecr_mvt += self.largeur_fixe(" ", 29, ' ', 'l')

                    if not compte_tmp in plan_comptable:
                        plan_comptable[compte_tmp] = line.partner_id.name

                    if not line.partner_id.name in plan_cpt_comptable:
                        ecr_cpt = b"CPT   "
                        if line.partner_id.isacompta_customer_code:
                            ecr_cpt += self.largeur_fixe(line.account_id.code, 10, ' ', 'l')
                        else:
                            ecr_cpt += self.largeur_fixe(line.account_id.code, 10, ' ', 'l')
                        if line.partner_id.name:
                            ecr_cpt += self.largeur_fixe(line.partner_id.name, 30, ' ', 'l')
                        else:
                            ecr_cpt += self.largeur_fixe(" ", 30, ' ', 'l')
                        ecr_cpt += self.largeur_fixe("", 245, ' ', 'l')
                        if line.partner_id.name:
                            plan_cpt_comptable[line.partner_id.name] = ecr_cpt

                    # S'l y a des erreurs
                    if erreurs:
                        raise UserError(_(erreurs))

                    # Ecriture de la ligne du mouvement dans le fichier
                    if new_ecr:
                        if last_ecr is not None:
                            plan_ecr_comptable[last_ecr] = ar
                            last_ecr = None
                            ar = []
                        ar.append(ecr_mvt)
                        new_ecr = False
                    else:
                        ar.append(ecr_mvt)
                        last_ecr = ecr_ecr
                    # ajout d'échéance
                    if ecr_echmvt != b"":
                        ar.append(ecr_echmvt)

        # add the last entries
        if len(ar) != 0:
            plan_ecr_comptable[last_ecr] = ar

        # for cpt in plan_cpt_comptable:
            # fcompta.write(plan_cpt_comptable[cpt].decode('ascii') + '\n')

        _logger.info("\nstarting liste ecritures")
        for ecr in plan_ecr_comptable:
            fcompta.write(ecr.decode('ascii') + '\n')
            for e in plan_ecr_comptable[ecr]:
                fcompta.write(e.decode('ascii') + '\n')

        # Fin des mouvements, on ferme le fichier
        fcompta.close()

        # Récupérer la valeur de la casse à cacher pour savoi si on est en mode simulation
        simulation = 0
        simulation = self.simulation

        # Mark all moves lines as exported
        # check is testing mode is enable
        if simulation == False:
            try:
                # flag des mouv comme étant "exported" car pas d'erreur
                moves_exported_ids.write({'exported_date': export_date})
            except Exception:
                raise UserError(_('Impossible to write on the database : exported_date !'))

        # ENVOI DE L'EMAIL
        """
        if nbEcriture > 0:
            ir_mail_server = self.env['ir.mail_server'].search([], limit=1)
            sender = EMAIL_FROM
            recepicient = [self.env.user.partner_id.email or EMAIL_TO_DEFAULT]

            # Pendant la phase de débug
            recepicient_bcc = [EMAIL_TO_DEFAULT]
            subject = "Odoo - Export ISACOMPTA du " + datetime.now().strftime("%d/%m/%Y à %Hh%M")
            body = "<Email envoyé par Odoo>\n\nBonjour,\n\nDans l'email il y a 1 fichier ASCII à intégrer dans ISACOMPTA :\n"
            attachments = []
            for fname in filename:
                if os.path.exists(fname):
                    fsname = fname.split('/')[-1]
                    body += " >> fichier : {}".format(fsname) + "\n"
                    f = open(fname)
                    file_data = ""
                    while True:
                        line = f.readline()
                        file_data += line
                        if not line:
                            break
                    attachments.append((fsname, file_data, 'text'))
            body += "\n\n Bonne intégration dans ISACOMPTA."
            msg = ir_mail_server.build_email(
                sender,
                recepicient,
                subject,
                body,
                email_bcc=recepicient_bcc,
                subtype='text',
                attachments=attachments)
            ir_mail_server.send_email(msg)
        else:
            raise UserError(_("Pas d'écriture à exporter."))
        """
        # Confirmation par un messages
        return {
            'name': _('Opération réussi'),
            'type': 'ir.actions.act_window',
            'view_mode': 'form',
            'res_model': 'account.export',
            'views': [(self.env.ref('isacompta_export.message_export_confirm_wizard_form').id, 'form')],
            'target': 'new'
        }
