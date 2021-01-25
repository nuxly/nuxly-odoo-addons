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
EMAIL_TO_DEFAULT = "<fd@nuxly.com>"


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
        help="If is true, the moves will not be checked like 'exported' but the file will be generate")

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
        s_lf = "MCOMPTE C  000JJMMAA LIBELLE             C+000000000000        301015                                      EURJOU   LIBELLE                         REF PIECE                                                                                                   "
        f.write('{}\n'.format(s_lf.encode(charset)))

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
                    _logger.info(
                        '[nuxly-log] /// export_quadra /// ligne without debit : {} neigther  credit : {} '.format(line.debit, line.credit))
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
                            erreurs += "ERROR : 137 - Invoice " + move.name + " : missing client code for the company " + line.partner_id.name + "\n"
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
                            erreurs += "ERROR : 146 - Invoice " + move.name + " : missing supplier code for the company " + line.partner_id.name + "\n"
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

                    # Contrepartie
                    s_lf += b"        "

                    # Date échéance
                    if line.date_maturity:
                        s_lf += line.date_maturity.strftime('%d%m%y').encode()
                    else:
                        s_lf += b"000000"

                    # Lettrage
                    s_lf += b"     "

                    # Numéro de pièce - 5 char
                    s_lf += b"     "

                    # Filler
                    s_lf += self.largeur_fixe(" ", 20, ' ', 'l')

                    # Numéro de pièce - 8 char
                    s_lf += b"        "

                    # Devise
                    s_lf += b"EUR"

                    # Code journal 2
                    s_lf += self.largeur_fixe(line.journal_id.code[:2], 3, ' ', 'l')

                    # Filler 2 - 3 char
                    s_lf += b"   "

                    # Libelle - 32 chars
                    # Si il s'agit d'un achat avec facture
                    libelle = b""
                    if(line.journal_id.type in ['sale', 'sale_refund'] and line.move_id):
                        # Journal de vente // update 05/10/2015 Ajouter au début le numéro de réf devant le libellé
                        if line.move_id.name:
                            libelle += line.move_id.name
                        if line.move_id.ref:
                            libelle += " " + line.move_id.ref
                    elif(line.journal_id.type in ['purchase', 'purchase_refund'] and line.move_id):
                        # Journal d'achat // update fd ud 05/07/2015 : 'name' à la place de 'origin'
                        if(line.move_id.name):
                            libelle += line.move_id.name
                        if(line.move_id.ref):
                            libelle += " " + line.move_id.ref
                    # Si il s'agit d'un journal de Bank
                    elif(line.journal_id.type in ['bank']):
                        if move.ref:
                            libelle = move.ref
                        else:
                            # On cherche la première ligne qui n'est pas sur le compte comptable
                            # banque (512...) attaché au journal de banque
                            for lineBis in move.line_id:
                                _logger.info("%s != %s ?", lineBis.account_id.code,
                                             move.journal_id.default_credit_account_id.code)
                                if(lineBis.account_id.code != move.journal_id.default_credit_account_id.code):
                                    libelle = lineBis.name
                                    break
                    # S'il s'agit du journal des Notes de frais (NF)
                    elif(line.journal_id.code == 'NF'):
                        libelle = line.ref + ' ' + line.name
                    # Tout autre types de comptes
                    elif(line.ref):
                        libelle = line.ref + ' ' + line.name
                    else:
                        libelle = line.name

                    # Normalise en remplaçant les accents & en supprimant les caractères autre que ASCII
                    s_lf += self.largeur_fixe(unicodedata.normalize('NFKD',
                                                                    libelle).encode('ascii', 'ignore'), 32, ' ', 'l')

                    # Numéro de pièce - 10 chars
                    # Piece (référence : max 10 caractères)
                    # Si len(n° pièce) <= 10 caractère alors on conserve [cas de la SCI]
                    # Ventes : VFA-2015-0056 >> V2015-0056
                    # Achat  : AFA-2015-0045 >> A2015-0045
                    # BANQUE :
                    # CM 302 05/2015/1 >> 302-05/1
                    # CM 302 05/2015/35 >> 302-05/35
                    # Notes de frais : NF17001 >> FD-NF17001
                    # Autre : OD/2015/0001 >> OD/15/0001
                    # Si Achat ou Vente
                    if(len(move.name) <= 10):
                        _logger.info("Ref <= 10 caract. alors on conserve : {}".format(move.name))
                        s_lf += self.largeur_fixe(move.name, 10, ' ', 'l')
                    elif(line.journal_id.type in ['purchase', 'purchase_refund', 'sale', 'sale_refund'] and line.move_id):
                        _logger.info("Ref : Achat ou Vente : {}||{}".format(move.name, move.name[0] + move.name[4:13]))
                        s_lf += self.largeur_fixe(move.name[0] + move.name[4:13], 10, ' ', 'l')
                    # Si c'est une banque et que c'est la CM 302 (Nuxly) ou M 501 (SCI)
                    elif((line.journal_id.type == 'bank') and ((move.name[:6] == 'CM 302') or (move.name[:6] == 'CM 501'))):
                        _logger.info("Ref : Bank 302 : {}||{}".format(move.name,
                                                                      move.name[3:6] + "-" + move.name[7:9] + "/" + move.name[15:25]))
                        s_lf += self.largeur_fixe(move.name[3:6] + "-" +
                                                  move.name[7:9] + "/" + move.name[15:25], 10, ' ', 'l')
                    # Si c'est une Note de frais (NF)
                    elif(line.journal_id.code == 'NF'):
                        initial = ''
                        # Création de façon dynamique des 2 premières initiales du partner
                        if line.partner_id:
                            initial = ''.join([s[:1] for s in line.partner_id.name.split(' ')])[:2] + '-'
                        _logger.info(u"Ref : NF : {}||{}".format(
                            move.name, self.largeur_fixe(initial + move.name[-7:], 10, ' ', 'l')))
                        s_lf += self.largeur_fixe(initial + move.name[-7:], 10, ' ', 'l')
                    # Si c'est une OD
                    elif(move.name[:2] == 'OD'):
                        _logger.info("Ref : OD : {}||{}".format(move.name, move.name[:3] + move.name[-7:]))
                        s_lf += self.largeur_fixe(move.name[:3] + move.name[-7:], 10, ' ', 'l')
                    # Sinon on prend les 10 dernières caractères en partant de la fin
                    else:
                        _logger.info("Ref : Autre : {}||{}".format(move.name, move.name[-10:]))
                        s_lf += self.largeur_fixe(move.name[-10:], 10, ' ', 'l')

                    # Filler - 73 chars
                    s_lf += self.largeur_fixe(" ", 73, ' ', 'l')

                    # Si il y a des erreurs
                    if erreurs:
                        raise UserError(_(erreurs))

                    # Formater la chaine pour supprimer les accents car Quadra les gère pas
                    # s_lf = unicodedata.normalize('NFKD', s_lf).encode('ascii', 'ignore')
                    # Ecriture de la ligne du mouv dans le fichier
                    f.write('{}\n'.format(s_lf))

        # Fin des mouv, on ferme le fichier
        f.close()

        # Récupérer la valeur de la casse à cacher pour savoi si on est en mode simulation
        simulation = 0
        _logger.info('NUXLY val : %s' % self.simulation)
        simulation = self.simulation

        # ENVOI DE L'EMAIL
        # check is testing mode is enable
        if simulation == False:
            try:
                # flag des mouv comme étant "exported" car pas d'erreur
                moves_exported_ids.write({'exported_date': export_date})
            except Exception:
                raise UserError(_('Impossible to write on the database : exported_date !'))

        if nbEcriture > 0:
            ir_mail_server = self.env['ir.mail_server'].search([], limit=1)
            sender = EMAIL_FROM
            recepicient = [self.env.user.partner_id.email or EMAIL_TO_DEFAULT]

            # Pendant la phase de débug
            recepicient_bcc = [EMAIL_TO_DEFAULT]
            subject = "Odoo - Export QUADRA du " + datetime.now().strftime("%d/%m/%Y à %Hh%M")
            body = "<Email envoyé par Odoo>\n\nBonjour,\n\nDans l'email il y a 1 fichier TXT à intégrer dans QUADRA :\n"
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
            body += "\n\n Bonne intégration dans QUADRA."
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
