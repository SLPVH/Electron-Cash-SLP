#!/usr/bin/env python
#
# Electrum - lightweight Bitcoin client
# Copyright (C) 2015 Thomas Voegtlin
#
# Permission is hereby granted, free of charge, to any person
# obtaining a copy of this software and associated documentation files
# (the "Software"), to deal in the Software without restriction,
# including without limitation the rights to use, copy, modify, merge,
# publish, distribute, sublicense, and/or sell copies of the Software,
# and to permit persons to whom the Software is furnished to do so,
# subject to the following conditions:
#
# The above copyright notice and this permission notice shall be
# included in all copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND,
# EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF
# MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND
# NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS
# BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN
# ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN
# CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.
import webbrowser

from electroncash.i18n import _
import electroncash.web as web
from electroncash.address import Address
from electroncash.plugins import run_hook
from electroncash.util import FileImportFailed
from PyQt5.QtGui import *
from PyQt5.QtCore import *
from PyQt5.QtWidgets import (
    QAbstractItemView, QFileDialog, QMenu, QTreeWidgetItem)
from .util import *

from electroncash.util import format_satoshis_nofloat
from .slp_add_token_dialog import SlpAddTokenDialog
from .slp_create_token_genesis_dialog import SlpCreateTokenGenesisDialog
from .slp_create_token_mint_dialog import SlpCreateTokenMintDialog
from .slp_burn_token_dialog import SlpBurnTokenDialog

from electroncash.slp import SlpNoMintingBatonFound

class SlpMgt(MyTreeWidget):
    filter_columns = [0, 1,2]  # Key, Value

    def slp_validity_slot(self, txid, validity):
        self.update()

    def __init__(self, parent):
        MyTreeWidget.__init__(self, parent, self.create_menu, [_('Token ID'), _('Token Name'), _('Dec.'),_('Balance'),_('Baton'), _('Token Type')], 0, [0], deferred_updates=True)
        self.slp_validity_signal = parent.slp_validity_signal
        self.slp_validity_signal.connect(self.slp_validity_slot, Qt.QueuedConnection)
        self.setSelectionMode(QAbstractItemView.ExtendedSelection)
        self.setSortingEnabled(True)
        self.editable_columns=[1]
        self.sortByColumn(1, Qt.AscendingOrder)

    def on_permit_edit(self, item, column):
        # openalias items shouldn't be editable
        return item.text(1) != "openalias"

    def on_edited(self, item, column, prior):
        token_id = item.text(0)
        d = self.parent.wallet.token_types[token_id]

        if self.parent.add_token_type(d['class'], token_id, item.text(1), d['decimals'], allow_overwrite=True):
            # successfully changed
            pass
        else:
            # revert back to original
            item.setText(1,d['name'])

    def on_doubleclick(self, item, column):
        if self.permit_edit(item, column):
            self.editItem(item, column)
        else:
            token_id = item.data(0, Qt.UserRole)
            if('unknown-' in item.text(1)):
                SlpAddTokenDialog(self.parent, token_id_hex = token_id, allow_overwrite=True)
            else:
                SlpAddTokenDialog(self.parent, token_id_hex = token_id, token_name=item.text(1))

    def create_menu(self, position):
        menu = QMenu()
        selected = self.selectedItems()
        if len(selected) == 1:
            keys = [item.text(0) for item in selected]
            if self.parent.wallet.token_types[keys[0]]['decimals'] == "?":
                menu.addAction(_("Add this token"), lambda: SlpAddTokenDialog(self.parent, token_id_hex = keys[0], allow_overwrite=True))
                menu.addAction(_("Remove this token"), lambda: self.parent.delete_slp_token(keys))
            else:
                if self.parent.wallet.token_types[keys[0]]['class'] == 'SLP129':
                    menu.addAction(_("Create new NFT"), lambda: SlpCreateTokenGenesisDialog(self.parent, nft_parent_id=keys[0]))
                    menu.addSeparator()
                try:
                    self.parent.wallet.get_slp_token_baton(keys[0])
                    menu.addAction(_("Mint Tool"), lambda: SlpCreateTokenMintDialog(self.parent, keys[0]))
                except SlpNoMintingBatonFound:
                    pass
                column = self.currentColumn()
                column_title = self.headerItem().text(column)
                column_data = '\n'.join([item.text(column) for item in selected])
                menu.addAction(_("Copy {}").format(column_title), lambda: self.parent.app.clipboard().setText(column_data))
                menu.addAction(_("Remove this token"), lambda: self.parent.delete_slp_token(keys))
                if self.currentItem():
                    menu.addAction(_("View Token Details"), lambda: self.onViewTokenDetails())
                menu.addAction(_("View Token Metadata"), lambda: self.onViewTokenMetadata())
                menu.addSeparator()
                menu.addAction(_("Burn Tool"), lambda: self.onBurnDialog())
            menu.addSeparator()

        menu.addAction(_("Add existing token"), lambda: SlpAddTokenDialog(self.parent,))
        menu.addAction(_("Create a new token"), lambda: SlpCreateTokenGenesisDialog(self.parent,))

        run_hook('create_contact_menu', menu, selected)
        menu.exec_(self.viewport().mapToGlobal(position))

    def onViewTokenDetails(self):
        current = self.currentItem()
        if current:
            SlpAddTokenDialog(self.parent, token_id_hex = current.data(0, Qt.UserRole), token_name=current.text(1))

    def onViewTokenMetadata(self):
        from electroncash.slp import SlpMessage, SlpUnsupportedSlpTokenType, SlpInvalidOutputMessage

        current = self.currentItem()
        token_id_hex = current.data(0, Qt.UserRole)
        tx = self.parent.wallet.transactions[token_id_hex]
        if current:
            try:
                slpMsg = SlpMessage.parseSlpOutputScript(tx.outputs()[0][1])
            except SlpUnsupportedSlpTokenType as e:
                return self.fail_genesis_info(_("Unsupported SLP token version/type - %r.")%(e.args[0],))
        addr = slpMsg.op_return_fields["token_doc_url"].decode()
        try:
            index = self.parent.tabs.indexOf(self.parent.keyserver_tab)
        except:
            print("TODO")
        self.parent.tabs.setCurrentIndex(index)
        self.parent.ks_addr_download_e.setText(addr)
        self.parent.pick_address_download(picker=False)


    def onBurnDialog(self):
        current = self.currentItem()
        if current:
            SlpBurnTokenDialog(self.parent, token_id_hex = current.data(0, Qt.UserRole), token_name=current.text(1))

    def get_balance_from_token_id(self,slpTokenId):
        # implement by looking at UTXO for this token!
        # for now return dummy value.
        bal=self.parent.wallet.get_slp_token_balance(slpTokenId, self.parent.config)[0]
        return bal

    @rate_limited(.333, classlevel=True, ts_after=True) # We rate limit the slp mgt refresh no more than 3 times every second, app-wide
    def update(self):
        if self.parent and self.parent.cleaned_up:
            # short-cut return if window was closed and wallet is stopped
            return
        super().update()

    def on_update(self):
        self.clear()

        tokens = self.parent.wallet.token_types.copy()
        for token_id, i in tokens.items():
            name     = i["name"]
            decimals = i["decimals"]
            calculated_balance= self.get_balance_from_token_id(token_id)
            if decimals != "?":
                balancestr = format_satoshis_nofloat(calculated_balance, decimal_point=decimals, num_zeros=decimals)
                balancestr += ' '*(9-decimals)
            else:
                balancestr = "double-click to add"

            typestr = "?"
            if i['class'] == "SLP1":
                typestr = "Type 1"
            elif i['class'] == "SLP65":
                typestr = "NFT1 Child"
            elif i['class'] == "SLP129":
                typestr = "NFT1 Parent"

            try:
                self.parent.wallet.get_slp_token_baton(token_id)
                item = QTreeWidgetItem([str(token_id),str(name),str(decimals),balancestr,"★", typestr])
            except SlpNoMintingBatonFound:
                item = QTreeWidgetItem([str(token_id),str(name),str(decimals),balancestr,"", typestr])

            squishyfont = QFont(MONOSPACE_FONT)
            squishyfont.setStretch(85)
            item.setFont(0, squishyfont)
            #item.setTextAlignment(2, Qt.AlignRight)
            item.setTextAlignment(3, Qt.AlignRight)
            item.setFont(3, QFont(MONOSPACE_FONT))
            item.setData(0, Qt.UserRole, token_id)
            if decimals == "?":
                item.setForeground(0, QBrush(QColor("#BC1E1E")))
                item.setForeground(1, QBrush(QColor("#BC1E1E")))
                item.setForeground(2, QBrush(QColor("#BC1E1E")))
                item.setForeground(3, QBrush(QColor("#BC1E1E")))
                item.setForeground(4, QBrush(QColor("#BC1E1E")))
                item.setForeground(5, QBrush(QColor("#BC1E1E")))
            if i["class"] == "SLP129":
                for _token_id, _i in self.parent.wallet.token_types.items():
                    if _i["class"] == "SLP65" and _i.get("group_id", None) == token_id:
                        name =     _i["name"]
                        decimals = _i["decimals"]
                        calculated_balance= self.get_balance_from_token_id(_token_id)
                        if decimals != "?":
                            balancestr = format_satoshis_nofloat(calculated_balance, decimal_point=decimals, num_zeros=decimals)
                            balancestr += ' '*(9-decimals)
                        else:
                            balancestr = "double-click to add"
                        _nft_item = QTreeWidgetItem([str(_token_id),str(name),str(decimals),balancestr,"", "NFT1 Child"])
                        squishyfont = QFont(MONOSPACE_FONT)
                        squishyfont.setStretch(85)
                        _nft_item.setFont(0, squishyfont)
                        #item.setTextAlignment(2, Qt.AlignRight)
                        _nft_item.setTextAlignment(3, Qt.AlignRight)
                        _nft_item.setFont(3, QFont(MONOSPACE_FONT))
                        _nft_item.setData(0, Qt.UserRole, _token_id)
                        if decimals == "?":
                            _nft_item.setForeground(0, QBrush(QColor("#BC1E1E")))
                            _nft_item.setForeground(1, QBrush(QColor("#BC1E1E")))
                            _nft_item.setForeground(2, QBrush(QColor("#BC1E1E")))
                            _nft_item.setForeground(3, QBrush(QColor("#BC1E1E")))
                        item.addChild(_nft_item)
                self.addTopLevelItem(item)
            elif i["class"] == "SLP65" and i.get("group_id", "?") == "?":
                self.addTopLevelItem(item)
            elif i["class"] == "SLP1":
                self.addTopLevelItem(item)
        self.expandAll()
