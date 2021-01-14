from odoo import fields, models, api, _
from odoo.exceptions import UserError
from datetime import datetime
import os
import logging

_logger = logging.getLogger(__name__)

INVOICE_TYPE = {
    'out_invoice': 'FC',
    'in_invoice': 'FF',
    'out_refund': 'AC',
    'in_refund': 'AF',
    '_other_': 'OD',
    }
EMAIL_FROM = "No Reply<noc@nuxly.com>"
EMAIL_TO_DEFAULT = "<contact@nuxly.com>"


class AccountExport(models.TransientModel):
    _name = "account.export"
    _description = "Export QUADRA"
    _inherit = ['mail.thread']

    def export_quadra(self):

        obj_company = self.env['res.company']
        obj_move = self.env['account.move']
        obj_users = self.env['res.users']
        filename = []
        errors_moves = [] #tableau d'erreur empêchant la génération du fichier d'export
        moves_exported_ids = self.env['account.move'] #id des mouv exportés pour flaguer

        #tableau des types de journaux qui sont exportés
        # types possibles : sale / sale_refund / purchase / purchase_refund / cash / bank / general / situation
        journal_types = ['sale','sale_refund','purchase','purchase_refund', 'bank']
        export_date = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        charset = 'utf8'
        # récupération de ID du User courant
        current_user = self.env.user

        # Nombre d'écriture
        nbEcriture = 0

        # Export pour la compagnie en cour uniquement
        company = current_user.company_id

        #_logger.debug('DEBUG export_quadra > company = [{} - {} - {}]'.format(company.id, company.partner_id.name, company))
        ids_move = obj_move.search([('state','=','posted'),('exported_date','=',False),('company_id','=', company.id)], order="name")
        if not ids_move:
            _logger.info('Sorry: No item to export for "{}" company.'.format(company.name))
            return

        filename.append('/tmp/{}_export_{}.csv'.format(datetime.now().strftime("%Y-%m-%d_%H-%M-%S"), company.partner_id.name))

        try:
            f = open(filename[0], 'w')
        except Exception:
            raise UserError(_('Impossible de creer le fichier !'))


        # Liste des colonnes
        s = "Date;CJ;FOL;CPT. CODE;CPT. NOM;LIBELLE;PIECE;DT. ECH.;DEBIT;CREDIT"
        f.write('{}\n'.format(s.encode(charset)))


        erreurs = ''

        # Parcours des mouv
        for move in ids_move:
            # ne traite que les moves appartennant à une liste précise de type de journal. cf référence journal_types initiée
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
                    _logger.info('[nuxly-log] /// export_quadra /// ligne without debit : {} neigther  credit : {} '.format(line.debit, line.credit))
                else :

                    # Date
                    s += line.date.strftime('%d/%m/%y')+";"

                    # CJ (journal)
                    s += line.journal_id.code[:2]+";"

                    # Fol
                    s += "000;"

                    # Compte et Nom de comtpe
                    #### quadra_customer_code // Compte / Alphanumérique
                    # cas client
                    if (line.account_id.code[:3] == '411') and (line.partner_id):
                        # vérif sur code client saisi
                        if(line.partner_id.ref is None) or (line.partner_id.ref =='') or (line.partner_id.ref ==0):
                            #errors_moves.append(u"Facture {} : code client manquant pour la société {}".format(move.name, line.partner_id.name))
                            erreurs += "ERROR : 137 - Invoice " + format(move.name) + " : missing client code for the company " + format(line.partner_id.name) +"\n"
                            s += "undefined;"
                        else:
                            s += line.partner_id.ref.upper().replace(';', ',') +";"

                            if (line.partner_id.parent_id):
                                s+= line.partner_id.parent_id.name.upper().replace(';', ',') +";"
                            else:
                                s+= line.partner_id.name.upper().replace(';', ',') +";"


                     # cas fournisseur
                    elif (line.account_id.code[:3] == '401') and (line.partner_id):
                        # vérif sur code fournisseur saisi
                        if(line.partner_id.quadra_supplier_code == False) or (line.partner_id.quadra_supplier_code ==''):
                            # errors_moves.append(u"Facture {} : code fournisseur manquant pour la société {}".format(move.name, line.partner_id.name))
                            erreurs += "ERROR : 146 - Invoice " + format(move.name) + " : missing supplier code for the company " + format(line.partner_id.name)  + "\n"
                            s += "undefined;"
                        else:
                            s += line.partner_id.quadra_supplier_code.upper().replace(';', ',') + ";"

                            if (line.partner_id.parent_id):
                                s+= line.partner_id.parent_id.name.upper().replace(';', ',') + ";"
                            else:
                                s+= line.partner_id.name.upper().replace(';', ',') + ";"

                    # cas compte comptable - 8 caractères
                    else:
                        s += (format(line.account_id.code) + "000")[0:8].upper().replace(';', ',') + ";"
                        s += line.account_id.name.upper().replace(';', ',') + ";"

                    # Libelle
                    # Si il s'agit d'un achat avec facture
                    libelle  = " "
                    if(line.journal_id.type in ['purchase','purchase_refund'] and line.move_id):
                        # Journal d'achat
                        if(line.move_id.invoice_origin):
                            libelle += line.move_id.invoice_origin
                        if(line.move_id.ref):
                            libelle += " "+line.move_id.ref
                    # Si il s'agit d'un journal de Bank
                    elif(line.journal_id.type in ['bank']):
                        if(move.ref):
                            libelle = move.ref
                        else:
                            # On cherche la première ligne qui n'est pas le
                            for lineBis in move.line_id:
                                _logger.info("%s != %s ?", lineBis.account_id.name, move.journal_id.default_credit_account_id.name)
                                if(lineBis.account_id.name != move.journal_id.default_credit_account_id.name):
                                    libelle = lineBis.account_id.name
                                    _logger.info("IF : %s", 2)
                                    break
                    # Tout autre types de comptes (factures d'achats)
                    else:
                        if line.ref:
                            libelle += line.ref
                    s += libelle.upper().replace(';', ',') +";"


                    # Piece
                    s += format(move.name)+";"

                    # Date échéance
                    if(line.date_maturity):
                        s += line.date_maturity.strftime('%d/%m/%y')
                    s += ";"

                    #### debit et crédit - remplace les . par des ,
                    s += format('{:.2f}'.format(line.debit)).replace(".", ",")+";"
                    s += format('{:.2f}'.format(line.credit)).replace(".", ",") # Pas de ; à la fin de la ligne

                    ## Lettrage
                    # if(line.reconcile_ref):
                    #    s += format(line.reconcile_ref)

                    # Test de caractères
                    # test = "€ … « $ µ"; #
                    # test = test.decode('utf-8')
                    # _logger.info("my variable : %s", test)
                    # s += ";" + unicodedata.normalize('NFKD', format(test)).encode('ascii', 'ignore').upper() + ";"

                    # Si il y a des erreurs
                    if (erreurs != ''):
                        raise UserError(_(erreurs))

                    # Ecriture de la ligne du mouv dans le fichier
                    f.write('{}\n'.format(s.encode(charset)))

        # Fin des mouv, on ferme le fichier
        f.close()


        ### ENVOI DE L'EMAIL
        # check is testing mode is enable
        if company.expc_testing == False:
             try:
                 moves_exported_ids.write({'exported_date': export_date}) # flag des mouv comme étant "exported" car pas d'erreur
             except Exception:
                 raise UserError(_('Impossible to write on the database : exported_date !'))
        else:
             raise UserError(_("Le mode bac-à-sable est activé, aucun export n'a été réalisé. \n A noter qu'aucune erreur n'a été identifier lors des vérifications. \n Veuillez désactiver le mode bac-à-sable dans la configuration de la société : 'testing mode for quadra export'"))

        if nbEcriture > 0:
            ir_mail_server = self.env['ir.mail_server'].search([], limit=1)
            sender = EMAIL_FROM
            recepicient = [self.env.user.partner_id.email or EMAIL_TO_DEFAULT]

            # Pendant la phase de débug
            recepicient_bcc = [EMAIL_TO_DEFAULT]
            subject = "Odoo - Export QUADRA du " + format(datetime.now().strftime("%d/%m/%Y à %Hh%M"))
            body = "<Email envoyé par Odoo>\n\nBonjour,\n\nDans l'email il y a 1 fichier CSV à intégrer dans QUADRA :\n"
            attachments = []
            for fname in filename:
                if os.path.exists(fname):
                    fsname = fname.split('/')[-1]
                    body += " >> fichier : {}".format(fsname) + "\n"
                    f = open(fname)
                    file_data = ""
                    while 1:
                        line = f.readline()
                        file_data += line
                        if not line:
                            break
                    attachments.append((fsname, file_data, 'text/plain'))
            body += "\n\n Bonne intégration dans QUADRA."
            msg = ir_mail_server.build_email(sender, recepicient, subject, body, email_bcc=recepicient_bcc ,subtype='plain', attachments=attachments)
            ir_mail_server.send_email(msg)
        else:
            raise UserError(_("Pas d'écriture à exporter."))

        # Retour ok à améliorer pour fenêtre de confirmation utilisateur
        return {}

