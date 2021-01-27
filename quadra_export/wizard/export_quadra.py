from odoo import fields, models, api, _
from odoo import SUPERUSER_ID
from datetime import datetime
from odoo.exceptions import UserError
import logging
import tempfile
import email
import mimetypes
import base64
import os
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
    _description = "Export QUADRA"
    _inherit = ['mail.thread']

    """
    This wizard to export posted account move
    """

    def largeur_fixe(self, string, size, patern, align):
        if isinstance(string, str):
            string = string.encode()
        if align == 'r':
            return string[0:size].rjust(size, patern.encode())
        else:
            return string[0:size].ljust(size, patern.encode())

    simulation = fields.Boolean(
        'Simulate the export',
        help="If true, moves will not be tagged as 'exported', but QUADRATUS file will be generated.")

    def export_quadra(self):

        obj_company = self.env['res.company']
        obj_move = self.env['account.move']
        obj_users = self.env['res.users']
        filename = []
        errors_moves = []  # tableau d'erreur empêchant la génération du fichier d'export
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
        if not ids_move:
            _logger.info('Sorry: No item to export for "{}" company.'.format(company.name))
            #raise osv.except_osv(_('Sorry!'), _('No item to export.'))
            return

        filename.append('/tmp/{}_export_{}.txt'.format(datetime.now().strftime("%Y-%m-%d_%H-%M-%S"), company.partner_id.name))

        try:
            f = open(filename[0], 'w')
        except Exception:
            raise UserError(_('Impossible de creer le fichier !'))

        erreurs = ''

        # En-tête du fichier
        s_lf = b"MCOMPTE C  000JJMMAA LIBELLE             C+000000000000        301015                                      EURJOU   LIBELLE                         REF PIECE                                                                                                   "
        f.write('{}\n'.format(s_lf.decode('ascii')))

        # Parcours des mouv
        for move in ids_move:
            # ne traite que les moves appartennant à une liste précise de type de
            # journal. cf référence journal_types initiée
            if move.journal_id.type not in journal_types:
                continue

            # Ajout de l'ID du move dans le tab pour flagger en "exported" si pas d'erreur au global
            moves_exported_ids += move

            # Parcours des lignes du mouv courant
            for line in move.line_ids:

                # Incrémente le nombre d'écritude
                nbEcriture += 1

                s = ''
                # Les lignes de titres/sous-titres ne sont pas saisis dans l'export
                if (line.debit == 0) and (line.credit == 0):
                    _logger.info('export_quadra // line ignored because debit and credit are null')
                else:

                    # Type de compte
                    s_lf = b"M"

                    # Compte et Nom de comtpe
                    compte_tmp = b''
                    plan_comptable = {}
                    # client_code // Compte / Alphanumérique
                    # cas client
                    if (line.account_id.code[:3] == '411') and (line.partner_id):
                        # vérif sur code client saisi
                        if not line.partner_id.quadra_customer_code:
                            #errors_moves.append(u"Facture {} : code client manquant pour la société {}".format(move.name, line.partner_id.name))
                            erreurs += "ERROR : Invoice " + move.name + " : missing quadra customer code (see Accounting tab) for company " + line.partner_id.name + "\n"
                            compte_tmp += b'undefined'
                        else:
                            compte_tmp += unicodedata.normalize('NFKD',
                                                                line.partner_id.quadra_customer_code).encode('ASCII',
                                                                                                             'ignore')

                    # cas fournisseur
                    elif (line.account_id.code[:3] == '401') and (line.partner_id):
                        # vérif sur code fournisseur saisi
                        if not line.partner_id.quadra_supplier_code:
                            # errors_moves.append(u"Facture {} : code fournisseur manquant pour la société {}".format(move.name, line.partner_id.name))
                            erreurs += "ERROR : Invoice " + move.name + " : missing quadra supplier code (see Accounting tab) for company " + line.partner_id.name + "\n"
                            compte_tmp += b'undefined'
                        else:
                            compte_tmp += unicodedata.normalize('NFKD',
                                                                line.partner_id.quadra_supplier_code).encode('ASCII',
                                                                                                             'ignore')

                    # cas compte comptable - 8 caractères
                    else:
                        compte_tmp += unicodedata.normalize('NFKD',
                                                            (line.account_id.code + "000")[0:8]).encode('ASCII',
                                                                                                        'ignore')

                    s_lf += self.largeur_fixe(compte_tmp, 8, ' ', 'l')
                    if not compte_tmp in plan_comptable:
                        plan_comptable[compte_tmp] = line.partner_id.name

                    # CJ (journal)
                    s_lf += self.largeur_fixe(line.journal_id.code, 2, '0', 'l')

                    # Folio
                    s_lf += b"000"

                    # Date - A VALIDER
                    s_lf += line.date.strftime('%d%m%y').encode()

                    # Filler 1
                    s_lf += b' '

                    # Libellé - 20 chars
                    s_lf += self.largeur_fixe(" ", 20, ' ', 'l')

                    # Sens de l'écriture
                    if int(line.debit * 100) > 0:
                        _logger.info(format(line.debit))
                        s_lf += b'D'
                    elif int(line.credit * 100) > 0:
                        _logger.info(format(line.credit))
                        s_lf += b'C'

                    # Signe du montant
                    s_lf += b'+'

                    # Montant
                    if int(line.debit * 100) > 0:
                        s_lf += self.largeur_fixe(str(int(line.debit * 100)), 12, '0', 'r')
                    elif int(line.credit * 100) > 0:
                        s_lf += self.largeur_fixe(str(int(line.credit * 100)), 12, '0', 'r')

                    # Compte de contrepartie - position 56, 8 caract.
                    s_lf += self.largeur_fixe(" ", 8, ' ', 'l')

                    # Date échéance
                    if line.date_maturity:
                        s_lf += line.date_maturity.strftime('%d%m%y').encode()
                    else:
                        s_lf += b"000000"

                    # Code lettrage (2 caractères) et code statistique (3 caract.)
                    s_lf += self.largeur_fixe(" ", 5, ' ', 'l')

                    # Numéro de pièce - position 75, 5 caract.
                    s_lf += self.largeur_fixe(" ", 5, ' ', 'l')

                    # Filler
                    s_lf += self.largeur_fixe(" ", 20, ' ', 'l')

                    # Numéro de pièce - position 100, 8 caract.
                    s_lf += self.largeur_fixe(" ", 8, ' ', 'l')

                    # Code devise - position 108, 3 caract.
                    if move.currency_id:
                        s_lf += self.largeur_fixe(move.currency_id.name, 3, ' ', 'l')
                    else:
                        s_lf += b"EUR"

                    # Code journal 2 - sur 3 caract.
                    s_lf += self.largeur_fixe(line.journal_id.code[:2], 3, ' ', 'l')

                    # Filler 2 - 3 char
                    s_lf += self.largeur_fixe(" ", 3, ' ', 'l')

                    # Libelle - 32 chars
                    # Si il s'agit d'un achat avec facture
                    # Normalise en remplaçant les accents & en supprimant les caractères autre que ASCII
                    s_lf += self.largeur_fixe(unicodedata.normalize('NFKD', line.name.replace("\n","")).encode('ascii','ignore'), 32, ' ', 'l')

                    # Numéro de pièce - 10 chars
                    # Si len(n° pièce) <= 10 caractère alors on conserve en partant de la droite
                    # Facture client CI2101-0034 >> CI21010034
                    # Remplace esapce et "/" et "-" par rien si besoin 
                    if(len(move.name) <= 10):
                        s_lf += self.largeur_fixe(move.name, 10, ' ', 'l')
                    elif(len(move.name.replace('-','').replace('/','').replace(' ','')) <= 10):
                        s_lf += self.largeur_fixe(move.name.replace('-','').replace('/','').replace(' ',''), 10, ' ', 'l')
                    else:
                        s_lf += self.largeur_fixe(move.name.replace('-','').replace('/','').replace(' ','')[-10:], 10, ' ', 'l')

                    # Filler - 10 chars - zone réservée
                    s_lf += self.largeur_fixe(" ", 10, ' ', 'l')

                    # Montant en devise (position 169 sur 13 caract). Position 169 : signe
                    if move.currency_id and move.currency_id.name != "EUR":
                        # Signe du montant
                        if int(line.amount_currency) > 0:
                            s_lf += b'+'
                        else:
                            s_lf += b'-'
                        s_lf += self.largeur_fixe(str(abs(int(line.amount_currency * 100))), 12, '0', 'r')
                    else:
                        s_lf += self.largeur_fixe(" ", 13, ' ', 'l')

                    # Filler - 50 chars pour finir le fichier
                    s_lf += self.largeur_fixe(" ", 50, ' ', 'l')

                    # Si il y a des erreurs
                    if erreurs:
                        raise UserError(_(erreurs))

                    # Formater la chaine pour supprimer les accents car Quadra les gère pas
                    # s_lf = unicodedata.normalize('NFKD', s_lf).encode('ascii', 'ignore')
                    # Ecriture de la ligne du mouv dans le fichier
                    _logger.info('Type of line : {} - LINE [{}]\n'.format(type(s_lf), s_lf))
                    f.write('{}\n'.format(s_lf.decode('ascii')))

        # Fin des moves, on ferme le fichier
        f.close()

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
        if nbEcriture > 0:
            ir_mail_server = self.env['ir.mail_server'].search([], limit=1)
            sender = EMAIL_FROM
            recepicient = [self.env.user.partner_id.email or EMAIL_TO_DEFAULT]

            # Pendant la phase de débug
            recepicient_bcc = [EMAIL_TO_DEFAULT]
            subject = "Odoo - Export QUADRATUS du " + datetime.now().strftime("%d/%m/%Y à %Hh%M")
            body = "<Email envoyé par Odoo>\n\nBonjour,\n\nDans l'email il y a 1 fichier ASCII à intégrer dans QUADRATUS :\n"
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
                    attachments.append((fsname, file_data, 'text/plain'))
            body += "\n\n Bonne intégration dans QUADRATUS."
            msg = ir_mail_server.build_email(
                sender,
                recepicient,
                subject,
                body,
                email_bcc=recepicient_bcc,
                subtype='plain',
                attachments=attachments)
            ir_mail_server.send_email(msg)
        else:
            raise UserError(_("Pas d'écriture à exporter."))

        # Retour ok à améliorer pour fenêtre de confirmation utilisateur
        return {}
