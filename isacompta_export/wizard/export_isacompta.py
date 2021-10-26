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
    dossier_number = fields.Text('Dossier', required=True, default="TEST")
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
        filename = []

        test = unicodedata.normalize('NFKD', "détour @ eurors €").encode(
            'ascii', 'ignore')
        _logger.info(test)

        moves_exported_ids = self.env['account.move']  # id des mouv exportés pour flaguer

        # tableau des types de journaux qui sont exportés
        # types possibles : sale / sale_refund / purchase / purchase_refund / cash / bank / general / situation
        journal_types = ['sale', 'sale_refund', 'purchase', 'purchase_refund', 'bank', 'general']
        export_date = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

        # récupération de ID du User courant
        current_user = self.env.user

        # Nombre d'écriture
        nbEcriture = 0

        company = current_user.company_id

        ids_move = obj_move.search([('state', '=', 'posted'), ('exported_date', '=', False),
                                    ('company_id', '=', company.id)], order="name")
        # _logger.info('Id_move : "{}" : "{}" .'.format(type(ids_move), ids_move))

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

        filename.append('/tmp/odoo/{}_isacompta_{}.isa'.format(datetime.now().strftime("%Y-%m-%d_%H-%M-%S"),
                                                               company.partner_id.name))
        try:
            fcompta = open(filename[0], 'w')
        except Exception:
            raise UserError(_('Impossible de creer le fichier !'))

        erreurs = ''

        plan_ecr_comptable = {}
        plan_cpt_comptable = {}
        plan_jrn_comptable = {}

        # Echéance des mouvements
        ecr_echmvt = b""

        # (Entête) Création de version (obligatoire au début du fichier comptable)
        ecr_ln = b"VER   0200000"
        ecr_ln += b"0000"
        ecr_ln += self.largeur_fixe(" ", 1, ' ', 'l')
        ecr_ln += self.largeur_fixe(unicodedata.normalize('NFKD', company.partner_id.name).encode(
                                'ascii', 'ignore'), 30, ' ', 'l')
        ecr_ln += self.largeur_fixe(" ", 1, ' ', 'l')
        fcompta.write(ecr_ln.decode('ascii') + '\n')

        # Création de dossier isacompta
        dos_ecr = b"DOS   "
        dos_ecr += self.largeur_fixe(self.dossier_number, 8, ' ', 'l')
        dos_ecr += self.largeur_fixe(unicodedata.normalize('NFKD', company.partner_id.name).encode(
                                'ascii', 'ignore'), 30, ' ', 'l')
        dos_ecr += self.largeur_fixe(" ", 8, ' ', 'l')
        dos_ecr += self.largeur_fixe(" ", 13, ' ', 'l')
        # code étalon 1, 2 et ana
        # dos_ecr += self.largeur_fixe(" ", 21, ' ', 'l')
        fcompta.write(dos_ecr.decode('ascii') + '\n')

        # Crétaion d'exercice
        now = datetime.now()
        exo_ecr = b"EXO   0101"
        exo_ecr += now.strftime('%Y').encode()
        exo_ecr += b"3112"
        exo_ecr += now.strftime('%Y').encode()
        exo_ecr += b"0"  # Flag de destruction des écritures
        exo_ecr += self.largeur_fixe(" ", 15, ' ', 'l')
        exo_ecr += self.largeur_fixe(" ", 8, ' ', 'l')
        exo_ecr += self.largeur_fixe(" ", 1, ' ', 'l')
        fcompta.write(exo_ecr.decode('ascii') + '\n')

        last_ecr = None
        ar = []
        # Parcours les mouvements
        for move in ids_move:
            _logger.info('move : "{}" : "{}" .'.format(type(move), move))
            # ne traite que les moves appartennant à une liste précise de type de journal
            if move.journal_id.type not in journal_types:
                continue

            # Ajout de l'ID du move dans le tab pour flagger en "exported" si pas d'erreur au global
            moves_exported_ids += move

            # Création d'une pièce comptable
            ecr_ecr = b"ECR   "
            ecr_ecr += self.largeur_fixe(move.line_ids[0].journal_id.code, 2, ' ', 'l')
            ecr_ecr += move.line_ids[0].date.strftime('%d%m%Y').encode()
            # Numero de pièce
            if move.line_ids[0].ref:
                ecr_ecr += self.largeur_fixe(move.line_ids[0].ref, 8, ' ', 'l')
            else:
                ecr_ecr += self.largeur_fixe(" ", 8, ' ', 'l')
            # Libellé de l'écriture
            if move.line_ids[0].name:
                ecr_ecr += self.largeur_fixe(unicodedata.normalize('NFKD', move.line_ids[0].name).encode(
                                'ascii', 'ignore'), 30, ' ', 'l')
            else:
                ecr_ecr += self.largeur_fixe(" ", 30, ' ', 'l')
            # champ 55, 63, 70, 77, 80, 82
            ecr_ecr += self.largeur_fixe(" ", 38, ' ', 'l')
            ecr_ecr += self.largeur_fixe(" ", 8, ' ', 'l')
            ecr_ecr += self.largeur_fixe(" ", 8, ' ', 'l')
            # cahmp 109, 120, 121, 124, 126, 127, 137, 138
            ecr_ecr += self.largeur_fixe(" ", 40, ' ', 'l')
            ecr_ecr += self.largeur_fixe(" ", 30, ' ', 'l')
            # champ 179, 182, 187, 189, 190
            ecr_ecr += self.largeur_fixe(" ", 18, ' ', 'l')
            ecr_ecr += self.largeur_fixe(" ", 38, ' ', 'l')
            # champ 235, 237
            ecr_ecr += self.largeur_fixe(" ", 12, ' ', 'l')
            ecr_ecr += self.largeur_fixe(" ", 9, ' ', 'l')
            ecr_ecr += self.largeur_fixe(" ", 8, ' ', 'l')
            ecr_ecr += self.largeur_fixe(" ", 8, ' ', 'l')
            if move.line_ids[0].ref:
                ecr_ecr += self.largeur_fixe(unicodedata.normalize('NFKD', move.line_ids[0].ref).encode(
                                'ascii', 'ignore'), 15, ' ', 'l')
            else:
                ecr_ecr += self.largeur_fixe(" ", 15, ' ', 'l')
            ecr_ecr += self.largeur_fixe(" ", 10, ' ', 'l')

            # ajout des journaux
            ecr_jrn = b"JRN   "
            ecr_jrn += self.largeur_fixe(move.line_ids[0].journal_id.code, 2, ' ', 'l')
            ecr_jrn += self.largeur_fixe(unicodedata.normalize('NFKD', move.line_ids[0].journal_id.name).encode(
                                'ascii', 'ignore'), 30, ' ', 'r')
            ecr_jrn += self.largeur_fixe(" ", 2, ' ', 'l')
            ecr_jrn += self.largeur_fixe(" ", 2, ' ', 'l')
            ecr_jrn += self.largeur_fixe(" ", 12, ' ', 'l')
            ecr_jrn += self.largeur_fixe(" ", 26, ' ', 'l')
            ecr_jrn += self.largeur_fixe(" ", 5, ' ', 'l')
            if not move.line_ids[0].journal_id.code in plan_jrn_comptable:
                plan_jrn_comptable[move.line_ids[0].journal_id.code] = ecr_jrn

            # new entrie
            new_ecr = True
            # Parcours des lignes du mouvement courant
            for line in move.line_ids:
                _logger.info('move_line_ids : "{}" : "{}" .'.format(type(line), line))
                # _logger.info('Line of ove : {} - [{}]\n'.format(type(line), line))

                # Incrémente le nombre d'écritude
                nbEcriture += 1

                isCptTiers = False
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
                        if not line.partner_id.z_code_client:
                            erreurs += "ERROR : Invoice " + move.name + " : missing isacompta customer code (see Accounting tab) for company " + line.partner_id.name + "\n"
                            compte_tmp += b'undefined'
                        else:
                            compte_tmp += unicodedata.normalize('NFKD', line.partner_id.z_code_client).encode(
                                'ascii', 'ignore')
                            isCptTiers = True

                    # cas fournisseur
                    elif (line.account_id.code[:3] == '401') and (line.partner_id):
                        # vérif sur code fournisseur saisi
                        if not line.partner_id.z_code_fournisseur:
                            erreurs += "ERROR : Invoice " + move.name + " : missing isacompta supplier code (see Accounting tab) for company " + line.partner_id.name + "\n"
                            compte_tmp += b'undefined'
                        else:
                            compte_tmp += unicodedata.normalize('NFKD', line.partner_id.z_code_fournisseur).encode(
                                'ascii', 'ignore')
                            isCptTiers = True

                    # cas compte comptable - 8 caractères
                    else:
                        compte_tmp += unicodedata.normalize('NFKD', (line.account_id.code + "000")[0:8]).encode('ascii',
                                                                                                                'ignore')

                    # Création de mouvement
                    # doc : 286 et fichier exemple 285
                    ecr_mvt = b"MVT   "
                    ecr_mvt += self.largeur_fixe(compte_tmp, 10, ' ', 'l')
                    # libellé mouvement
                    _logger.info(line.name)
                    ecr_mvt += self.largeur_fixe(unicodedata.normalize('NFKD', line.name).encode(
                                'ascii', 'ignore'), 30, ' ', 'l')

                    # Montant débit et crédit
                    if int(line.debit * 100) > 0:
                        ecr_mvt += self.largeur_fixe(str(line.debit), 13, '0', 'r')
                        # ecr_mvt += self.largeur_fixe(str(int(line.debit * 100)), 13, '0', 'r')
                        ecr_mvt += self.largeur_fixe(" ", 13, ' ', 'l')
                    elif int(line.credit * 100) > 0:
                        ecr_mvt += self.largeur_fixe(str(line.credit), 26, '0', 'r')
                        # ecr_mvt += self.largeur_fixe(str(int(line.credit * 100)), 26, '0', 'r')

                    # Autre informations (quantité 1 et 2 + numéro)
                    ecr_mvt += self.largeur_fixe(" ", 30, ' ', 'l')
                    # champ 103, 105, 107, 108
                    ecr_mvt += self.largeur_fixe(" ", 8, ' ', 'l')
                    ecr_mvt += self.largeur_fixe(" ", 8, ' ', 'l')
                    # champ 119, 123, 124
                    ecr_mvt += self.largeur_fixe(" ", 13, ' ', 'l')

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
                    """

                    # date déclaration et code TVA 2, 3
                    ecr_mvt += self.largeur_fixe(" ", 4, ' ', 'l')
                    # Filler (*3 : 3, 5, 8)
                    ecr_mvt += self.largeur_fixe(" ", 16, ' ', 'l')
                    # Date de valeur et libres
                    ecr_mvt += self.largeur_fixe(" ", 24, ' ', 'l')
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
                            # ecr_mvt += self.largeur_fixe(str(abs(int(line.amount_currency * 100))), 11, '0', 'r')
                            ecr_mvt += self.largeur_fixe(str(line.amount_currency), 11, '0', 'r')
                            ecr_mvt += self.largeur_fixe(" ", 11, ' ', 'l')
                        else:
                            ecr_mvt += self.largeur_fixe(str(line.amount_currency), 22, '0', 'r')
                            # ecr_mvt += self.largeur_fixe(str(abs(int(line.amount_currency * 100))), 22, '0', 'r')
                    else:
                        ecr_mvt += self.largeur_fixe(" ", 22, ' ', 'l')
                    # Taux de change
                    ecr_mvt += self.largeur_fixe(" ", 8, ' ', 'l')
                    # Filler (*7 : 5, 5, 5, 2, 8, 3, 1)
                    # todo pour correspondre au fichier exemple, la derniere caractères n'est pas prise en comptes
                    ecr_mvt += self.largeur_fixe(" ", 28, ' ', 'l')
                    # ecr_mvt += self.largeur_fixe(" ", 1, ' ', 'l')

                    _logger.info('line.partner_id : "{}" : "{}" .'.format(type(line.partner_id), line.partner_id))
                    # if not line.account_id.code in plan_cpt_comptable:
                    if line.account_id.code:
                        if isCptTiers:
                            if not line.account_id.code in plan_cpt_comptable:
                                plan_cpt_comptable[line.account_id.code] = self.create_cpt('ce', line.account_id.code,
                                                                                       line.account_id.code,
                                                                                       line.account_id.name)
                            if not compte_tmp in plan_cpt_comptable:
                                plan_cpt_comptable[compte_tmp] = self.create_cpt('au', line.account_id.code, compte_tmp,
                                                                             line.partner_id.name)
                        else:
                            if not line.account_id.code in plan_cpt_comptable:
                                plan_cpt_comptable[line.account_id.code] = self.create_cpt('ge', line.account_id.code,
                                                                                       line.account_id.code,
                                                                                       line.account_id.name)

                    # S'l y a des erreurs
                    if erreurs:
                        raise UserError(_(erreurs))

                    # Ecriture de la ligne du mouvement dans le fichier
                    # _logger.info('Type of line : {} - LINE [{}]\n'.format(type(ecr_mvt), ecr_mvt))
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
                    # fcompta.write(ecr_mvt.decode('ascii') + '\n')
                    # ajout d'échéance
                    if ecr_echmvt != b"":
                        ar.append(ecr_echmvt)
                        # fcompta.write(ecr_echmvt.decode('ascii') + '\n')

        # add the last entries
        if len(ar) != 0:
            plan_ecr_comptable[last_ecr] = ar
        _logger.info("ecr '{}', '{}'".format(last_ecr, len(ar)))

        for cpt in plan_cpt_comptable:
            fcompta.write(plan_cpt_comptable[cpt].decode('ascii') + '\n')

        for jrn in plan_jrn_comptable:
            _logger.info(plan_jrn_comptable[jrn])
            fcompta.write(plan_jrn_comptable[jrn].decode("ascii") + '\n')

        _logger.info("\nstarting liste ecritures")
        # _logger.info(len(plan_ecr_comptable))
        # _logger.info(plan_ecr_comptable)
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

    def create_cpt(self, type, compte, compte_tmp, compte_name):
        ecr_cpt = b"CPT   "
        ecr_cpt += self.largeur_fixe(compte_tmp, 10, ' ', 'r')
        ecr_cpt += self.largeur_fixe(unicodedata.normalize('NFKD', compte_name).encode(
                                'ascii', 'ignore'), 30, ' ', 'r')
        # champ 47, 57, 60, 70, 73, 83
        ecr_cpt += self.largeur_fixe("", 36, ' ', 'l')
        ecr_cpt += self.largeur_fixe("", 1, ' ', 'l')  # 0
        ecr_cpt += self.largeur_fixe("", 3, ' ', 'l')
        # champ 87
        ecr_cpt += self.largeur_fixe(type, 2, ' ', 'l')
        ecr_cpt += self.largeur_fixe("", 7, ' ', 'l')
        # champ 96, 106, 116, 117, 119, 121, 122, 132, 142, 152, 153, 154
        ecr_cpt += self.largeur_fixe("", 20, ' ', 'l')
        ecr_cpt += self.largeur_fixe("", 1, ' ', 'l')
        ecr_cpt += self.largeur_fixe("", 2, ' ', 'l')  # in
        ecr_cpt += self.largeur_fixe("", 23, ' ', 'l')
        ecr_cpt += self.largeur_fixe(unicodedata.normalize('NFKD', compte).encode(
                                'ascii', 'ignore'), 10, '0', 'r')  # compte lié
        ecr_cpt += self.largeur_fixe("", 3, ' ', 'l')
        # libellé
        ecr_cpt += self.largeur_fixe(unicodedata.normalize('NFKD', compte_name).encode(
                                'ascii', 'ignore'), 30, ' ', 'r')
        # champ 185, 189, 192, 193, 194, 195, 196 à 202
        ecr_cpt += self.largeur_fixe("", 28, ' ', 'l')
        # champ 213, 227, 228, 231
        ecr_cpt += self.largeur_fixe("", 19, ' ', 'l')
        # libellé numero et date 1 et 2
        ecr_cpt += self.largeur_fixe("", 30, ' ', 'l')
        # champ 262, 263
        ecr_cpt += self.largeur_fixe("", 8, ' ', 'l')
        ecr_cpt += self.largeur_fixe("", 8, ' ', 'l')
        ecr_cpt += self.largeur_fixe("", 2, ' ', 'l')
        # champ 280, 282, 284
        ecr_cpt += self.largeur_fixe("", 6, ' ', 'l')
        ecr_cpt += self.largeur_fixe("", 3, ' ', 'l')
        ecr_cpt += self.largeur_fixe("", 3, ' ', 'l')

        return ecr_cpt
