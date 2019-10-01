#!/usr/bin/env python3
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

from functools import partial
from collections import defaultdict

from ..util import *
from PyQt5.QtCore import Qt, pyqtSignal
from PyQt5.QtGui import QFont, QColor, QKeySequence, QCursor, QIcon
from PyQt5.QtWidgets import *
from electroncash.i18n import _
from electroncash.address import Address
from electroncash.plugins import run_hook
import electroncash.web as web
from electroncash.util import profiler
from electroncash import networks
from enum import IntEnum

class KSAddressList(MyTreeWidget):
    filter_columns = [0, 1]  # Address, Label, Balance

    _ca_minimal_chash_updated_signal = pyqtSignal(object, str)
    _cashacct_icon = None

    class DataRoles(IntEnum):
        address = Qt.UserRole + 0
        can_edit_label = Qt.UserRole + 1
        cash_accounts = Qt.UserRole + 2

    def __init__(self, parent):
        super().__init__(parent, lambda x: None, [], 2, deferred_updates=True)
        self.refresh_headers()
        self.setSelectionMode(QAbstractItemView.SingleSelection)
        self.editable_columns = []
        self.setSortingEnabled(True)
        self.wallet = self.parent.wallet
        self.monospace_font = QFont(MONOSPACE_FONT)
        assert self.wallet

    def filter(self, p):
        ''' Reimplementation from superclass filter.  Chops off the
        "bitcoincash:" prefix so that address filters ignore this prefix.
        Closes #1440. '''
        cashaddr_prefix = f"{networks.net.CASHADDR_PREFIX}:".lower()
        p = p.strip()
        if len(p) > len(cashaddr_prefix) and p.lower().startswith(cashaddr_prefix):
            p = p[len(cashaddr_prefix):]  # chop off prefix
        super().filter(p)  # call super on chopped-off-piece

    def refresh_headers(self):
        headers = [_('Address'), _('Index'), _('Label')]
        fx = self.parent.fx
        if fx and fx.get_fiat_address_config():
            headers.insert(4, '{} {}'.format(fx.get_currency(), _('Balance')))
        self.update_headers(headers)

    # We rate limit the address list refresh no more than once every second
    @rate_limited(1.0, ts_after=True)
    def update(self):
        super().update()

    @profiler
    def on_update(self):
        def item_path(item):  # Recursively builds the path for an item eg 'parent_name/item_name'
            return item.text(0) if not item.parent() else item_path(item.parent()) + "/" + item.text(0)

        def remember_expanded_items(root):
            # Save the set of expanded items... so that address list updates don't annoyingly collapse
            # our tree list widget due to the update. This function recurses. Pass self.invisibleRootItem().
            expanded_item_names = set()
            for i in range(0, root.childCount()):
                it = root.child(i)
                if it and it.childCount():
                    if it.isExpanded():
                        expanded_item_names.add(item_path(it))
                    expanded_item_names |= remember_expanded_items(
                        it)  # recurse
            return expanded_item_names

        def restore_expanded_items(root, expanded_item_names):
            # Recursively restore the expanded state saved previously. Pass self.invisibleRootItem().
            for i in range(0, root.childCount()):
                it = root.child(i)
                if it and it.childCount():
                    # recurse, do leaves first
                    restore_expanded_items(it, expanded_item_names)
                    old = bool(it.isExpanded())
                    new = bool(item_path(it) in expanded_item_names)
                    if old != new:
                        it.setExpanded(new)
        sels = self.selectedItems()
        addresses_to_re_select = {
            item.data(0, self.DataRoles.address) for item in sels}
        expanded_item_names = remember_expanded_items(self.invisibleRootItem())
        del sels  # avoid keeping reference to about-to-be delete C++ objects
        self.clear()
        # Note we take a shallow list-copy because we want to avoid
        # race conditions with the wallet while iterating here. The wallet may
        # touch/grow the returned lists at any time if a history comes (it
        # basically returns a reference to its own internal lists). The wallet
        # may then, in another thread such as the Synchronizer thread, grow
        # the receiving or change addresses on Deterministic wallets.  While
        # probably safe in a language like Python -- and especially since
        # the lists only grow at the end, we want to avoid bad habits.
        # The performance cost of the shallow copy below is negligible for 10k+
        # addresses even on huge wallets because, I suspect, internally CPython
        # does this type of operation extremely cheaply (probably returning
        # some copy-on-write-semantics handle to the same list).
        receiving_addresses = list(self.wallet.get_receiving_addresses())
        change_addresses = list(self.wallet.get_change_addresses())

        if self.parent.fx and self.parent.fx.get_fiat_address_config():
            fx = self.parent.fx
        else:
            fx = None
        account_item = self
        items_to_re_select = []

        seq_item = account_item
        addr_list = receiving_addresses + change_addresses

        for n, address in enumerate(addr_list):
            num = len(self.wallet.get_address_history(address))
            balance = sum(self.wallet.get_addr_balance(address))
            address_text = address.to_ui_string()
            label = self.wallet.labels.get(address.to_storage_string(), '')
            balance_text = self.parent.format_amount(balance, whitespaces=True)
            columns = [address_text, str(n), label, balance_text, str(num)]
            if fx:
                rate = fx.exchange_rate()
                fiat_balance = fx.value_str(balance, rate)
                columns.insert(4, fiat_balance)
            address_item = SortableTreeWidgetItem(columns)
            address_item.setTextAlignment(3, Qt.AlignRight)
            address_item.setFont(3, self.monospace_font)
            if fx:
                address_item.setTextAlignment(4, Qt.AlignRight)
                address_item.setFont(4, self.monospace_font)

            # Set col0 address font to monospace
            address_item.setFont(0, self.monospace_font)

            # Set UserRole data items:
            address_item.setData(0, self.DataRoles.address, address)
            # label can be edited
            address_item.setData(0, self.DataRoles.can_edit_label, True)

            seq_item.addChild(address_item)
            if address in addresses_to_re_select:
                items_to_re_select.append(address_item)

        for item in items_to_re_select:
            # NB: Need to select the item at the end becasue internally Qt does some index magic
            # to pick out the selected item and the above code mutates the TreeList, invalidating indices
            # and other craziness, which might produce UI glitches. See #1042
            item.setSelected(True)

        # Now, at the very end, enforce previous UI state with respect to what was expanded or not. See #1042
        restore_expanded_items(self.invisibleRootItem(), expanded_item_names)

    def keyPressEvent(self, event):
        if event.matches(QKeySequence.Copy) and self.currentColumn() == 0:
            addrs = [i.data(0, self.DataRoles.address)
                     for i in self.selectedItems()]
            if addrs and isinstance(addrs[0], Address):
                text = addrs[0].to_full_string(fmt=Address.FMT_CASHADDR)
                self.parent.app.clipboard().setText(text)
        else:
            super().keyPressEvent(event)

    def update_labels(self):
        if self.should_defer_update_incr():
            return

        def update_recurse(root):
            child_count = root.childCount()
            for i in range(child_count):
                item = root.child(i)
                addr = item.data(0, self.DataRoles.address)
                if isinstance(addr, Address):
                    label = self.wallet.labels.get(
                        addr.to_storage_string(), '')
                    item.setText(2, label)
                if item.childCount():
                    update_recurse(item)
        update_recurse(self.invisibleRootItem())

    def on_doubleclick(self, item, column):
        if self.permit_edit(item, column):
            super(KSAddressList, self).on_doubleclick(item, column)
        else:
            addr = item.data(0, self.DataRoles.address)
            if isinstance(addr, Address):
                self.parent.show_address(addr)

    #########################
    # Cash Accounts related #
    #########################
    def _ca_set_item_tooltip(self, item, ca_info):
        minimal_chash = getattr(ca_info, 'minimal_chash', None)
        info_str = self.wallet.cashacct.fmt_info(ca_info, minimal_chash)
        item.setToolTip(0, "<i>" + _("Cash Account:") + "</i><p>&nbsp;&nbsp;<b>"
                           + f"{info_str}</b>")

    def _ca_update_chash(self, ca_info, minimal_chash):
        ''' Called in GUI thread as a result of the cash account subsystem
        figuring out that a collision_hash can be represented shorter.
        Kicked off by a get_minimal_chash() call that results in a cache miss. '''
        if self.cleaned_up:
            return
        items = self.findItems(ca_info.address.to_ui_string(
        ), Qt.MatchContains | Qt.MatchWrap | Qt.MatchRecursive, 0) or []
        for item in items:  # really items should contain just 1 element...
            ca_list = item.data(0, self.DataRoles.cash_accounts) or []
            ca_info_default = self._ca_get_default(ca_list)
            for ca_info_saved in ca_list:
                if ((ca_info_saved.name.lower(), ca_info_saved.number, ca_info_saved.collision_hash)
                        == (ca_info.name.lower(), ca_info.number, ca_info.collision_hash)):
                    ca_info_saved.minimal_chash = minimal_chash  # save minimal_chash as a property
                    if ca_info_saved == ca_info_default:
                        # this was the default one, also set the tooltip
                        self._ca_set_item_tooltip(item, ca_info)

    def _ca_updated_minimal_chash_callback(self, event, *args):
        ''' Called from the cash accounts minimal_chash thread after a network
        round-trip determined that the minimal collision hash can be shorter.'''
        if (event == 'ca_updated_minimal_chash'
                and not self.cleaned_up
                and args[0] is self.wallet.cashacct):
            self._ca_minimal_chash_updated_signal.emit(args[1], args[2])

    def _ca_get_default(self, ca_list):
        ''' Alias for self.wallet.cashacct.get_address_default '''
        return self.wallet.cashacct.get_address_default(ca_list)

    def _ca_set_default(self, ca_info, show_tip=False):
        ''' Similar to self.wallet.cashacct.set_address_default, but also
        shows a tooltip optionally, and updates self. '''
        self.wallet.cashacct.set_address_default(ca_info)
        if show_tip:
            QToolTip.showText(QCursor.pos(), _(
                "Cash Account has been made the default for this address"), self)
        self.parent.ca_address_default_changed_signal.emit(
            ca_info)  # eventually calls self.update

    def _ca_on_address_default_change(self, ignored):
        self.update()


def pick_ks_address(parent, external=False) -> str:
    ''' Returns None on user cancel, or a full address string
    from the Address list. '''

    # Show user address picker
    d = WindowModalDialog(parent.top_level_window(), _('Choose an address'))
    d.setObjectName("Window Modal Dialog - " + d.windowTitle())
    destroyed_print_error(d)  # track object lifecycle
    d.setMinimumWidth(parent.width()-150)
    vbox = QVBoxLayout(d)
    vbox.addWidget(QLabel(_('Choose an address') + ':'))
    l = KSAddressList(parent)

    l.setObjectName("AddressList - " + d.windowTitle())
    destroyed_print_error(l)  # track object lifecycle
    l.update()
    if external:
        def on_text_changed(text):
            nonlocal addr
            if text != "":
                if Address.is_valid(text):
                    # TODO: Fix clunky way to add prefix
                    addr = Address.from_string(text).to_full_string(fmt=Address.FMT_CASHADDR)
                    ok.setEnabled(True)
                else:
                    ok.setEnabled(False)
                l.clearSelection()
            else:
                addr = None
                ok.setEnabled(False)
        text_input = QLineEdit()
        text_input.textChanged.connect(on_text_changed)
        vbox.addWidget(text_input)
    vbox.addWidget(l)

    ok = OkButton(d)
    ok.setDisabled(True)

    addr = None

    def on_item_changed(current, previous):
        nonlocal addr
        addr = current and current.data(0, l.DataRoles.address)
        addr = addr.to_full_string(fmt=Address.FMT_CASHADDR)
        ok.setEnabled(addr is not None)
    l.currentItemChanged.connect(on_item_changed)

    cancel = CancelButton(d)

    vbox.addLayout(Buttons(cancel, ok))

    res = d.exec_()
    if res == QDialog.Accepted:
        return addr
    return None
