from PyQt5.QtWidgets import *
from ..util import *
from electroncash.i18n import _
from electroncash.keyserver.metadata_tools import *


class UKeyserverForm(QWidget):
    inputs_changed = pyqtSignal()

    def is_full(self):
        raise NotImplementedError

    def clear(self):
        raise NotImplementedError

    def construct_entry(self, addr):
        raise NotImplementedError


class UPlainTextForm(UKeyserverForm):
    def __init__(self, *args, **kwargs):
        super(UPlainTextForm, self).__init__(*args, **kwargs)
        plain_text_grid = QGridLayout()
        msg = _('Plain text to be uploaded.')
        description_label = HelpLabel(_('&Text'), msg)
        plain_text_grid.addWidget(description_label, 0, 0)
        self.upload_plain_text_e = QTextEdit()
        description_label.setBuddy(self.upload_plain_text_e)
        plain_text_grid.addWidget(self.upload_plain_text_e, 0, 1, 1, -1)

        self.setLayout(plain_text_grid)

        self.upload_plain_text_e.textChanged.connect(self.inputs_changed.emit)

    def is_full(self):
        return bool(self.upload_plain_text_e.toPlainText())

    def clear(self):
        self.upload_plain_text_e.clear()

    def construct_entry(self):
        data = self.upload_plain_text_e.toPlainText()
        return plain_text_entry(data)


class UTelegramForm(UKeyserverForm):
    def __init__(self, *args, **kwargs):
        super(UTelegramForm, self).__init__(*args, **kwargs)
        plain_text_grid = QGridLayout()
        msg = _('Telegram handle to be uploaded.')
        description_label = HelpLabel(_('&Handle'), msg)
        plain_text_grid.addWidget(description_label, 0, 0)
        self.upload_telegram_e = QLineEdit()
        description_label.setBuddy(self.upload_telegram_e)
        plain_text_grid.addWidget(self.upload_telegram_e, 0, 1, 1, -1)

        self.setLayout(plain_text_grid)

        self.upload_telegram_e.textChanged.connect(self.inputs_changed.emit)

    def is_full(self):
        return bool(self.upload_telegram_e.text())

    def clear(self):
        self.upload_telegram_e.clear()

    def construct_entry(self):
        text = self.upload_telegram_e.text()
        return telegram_entry(text)


class UPubkeyForm(UKeyserverForm):
    def __init__(self, parent, *args, **kwargs):
        super(UPubkeyForm, self).__init__(*args, **kwargs)
        pubkey_grid = QGridLayout()
        self.parent = parent

        def pick_address():
            from .address_list import pick_ks_address
            addr = pick_ks_address(parent)
            if addr:
                addr = Address.from_string(addr)
                self.upload_pubkey_e.setText(
                    self.parent.wallet.get_public_key(addr))

        msg = _(
            'Public key to uploaded.  Use the tool button on the right to pick a wallet address.')
        description_label = HelpLabel(_('&Public Key'), msg)
        pubkey_grid.addWidget(description_label, 1, 0)
        self.upload_pubkey_e = ButtonsLineEdit()
        self.upload_pubkey_e.setReadOnly(True)
        self.upload_pubkey_e.setPlaceholderText(_("Specify a wallet address"))
        self.upload_pubkey_e.addButton(
            ":icons/tab_addresses.png", on_click=pick_address, tooltip=_("Pick an address from your wallet"))
        description_label.setBuddy(self.upload_pubkey_e)
        pubkey_grid.addWidget(self.upload_pubkey_e, 1, 1, 1, -1)

        self.setLayout(pubkey_grid)

        self.upload_pubkey_e.textChanged.connect(self.inputs_changed.emit)

    def is_full(self):
        return bool(self.upload_pubkey_e.text())

    def clear(self):
        self.upload_telegram_e.clear()

    def construct_entry(self):
        pubkey = bytes.fromhex(self.upload_pubkey_e.text())
        return pubkey_entry(pubkey)


class UKeyserverURLForm(UKeyserverForm):
    def __init__(self, *args, **kwargs):
        super(UKeyserverURLForm, self).__init__(*args, **kwargs)
        plain_text_grid = QGridLayout()
        msg = _('Keyserver list to be uploaded. Line delimited.')
        description_label = HelpLabel(_('&Servers'), msg)
        plain_text_grid.addWidget(description_label, 0, 0)
        self.upload_ks_urls_e = QTextEdit()
        description_label.setBuddy(self.upload_ks_urls_e)
        plain_text_grid.addWidget(self.upload_ks_urls_e, 0, 1, 1, -1)

        self.setLayout(plain_text_grid)

        self.upload_ks_urls_e.textChanged.connect(self.inputs_changed.emit)

    def is_full(self):
        return bool(self.upload_ks_urls_e.toPlainText())

    def clear(self):
        self.upload_ks_urls_e.clear()

    def construct_entry(self):
        urls = self.upload_ks_urls_e.toPlainText().split("\n")
        return ks_urls_entry(urls)


class UVCardForm(UKeyserverForm):
    def __init__(self, *args, **kwargs):
        super(UVCardForm, self).__init__(*args, **kwargs)
        vcard_grid = QGridLayout()

        msg = _('Name of contact.')
        description_label = HelpLabel(_('&Name'), msg)
        vcard_grid.addWidget(description_label, 0, 0)
        self.upload_vName_e = QLineEdit()
        description_label.setBuddy(self.upload_vName_e)
        vcard_grid.addWidget(self.upload_vName_e, 0, 1, 1, -1)

        msg = _('Mobile number of contact.')
        description_label = HelpLabel(_('&Mobile'), msg)
        vcard_grid.addWidget(description_label, 1, 0)
        self.upload_vMobile_e = QLineEdit()
        description_label.setBuddy(self.upload_vMobile_e)
        vcard_grid.addWidget(self.upload_vMobile_e, 1, 1, 1, -1)

        msg = _('Email of contact.')
        description_label = HelpLabel(_('&Email'), msg)
        vcard_grid.addWidget(description_label, 2, 0)
        self.upload_vEmail_e = QLineEdit()
        description_label.setBuddy(self.upload_vEmail_e)
        vcard_grid.addWidget(self.upload_vEmail_e, 2, 1, 1, -1)

        self.setLayout(vcard_grid)

        self.upload_vName_e.textChanged.connect(self.inputs_changed.emit)
        self.upload_vMobile_e.textChanged.connect(self.inputs_changed.emit)
        self.upload_vEmail_e.textChanged.connect(self.inputs_changed.emit)

    def is_full(self):
        # Name is required
        return bool(self.upload_vName_e.text())

    def clear(self):
        self.upload_vName_e.clear()
        self.upload_vMobile_e.clear()
        self.upload_vEmail_e.clear()

    def construct_entry(self):
        card = {
            "name": self.upload_vName_e.text(),
            "mobile": self.upload_vMobile_e.text(),
            "email": self.upload_vEmail_e.text()
        }
        return vcard_entry(card)


class UIconForm(UKeyserverForm):
    def __init__(self, *args, **kwargs):
        super(UIconForm, self).__init__(*args, **kwargs)
        logo_grid = QGridLayout()
        self.img_data = None

        def pick_logo():
            file_name, _ = QFileDialog.getOpenFileName(self, 'Find icon', '/home')
            self.upload_logo_e.setText(file_name)
            pixel_map = QPixmap(file_name).scaled(128, 128, Qt.KeepAspectRatio)
            byte_array = QByteArray()
            buf = QBuffer(byte_array)
            buf.open(QIODevice.WriteOnly)
            if pixel_map.save(buf, "PNG"):
                self.img_data = byte_array.data()
            else:
                self.img_data = None
            self.inputs_changed.emit()
            self.preview_logo.setPixmap(pixel_map)
            return file_name

        msg = _(
            'Icon to be uploaded.  Use the tool button on the right to upload from your local disk.')
        description_label = HelpLabel(_('&Icon'), msg)
        logo_grid.addWidget(description_label, 1, 0)
        self.upload_logo_e = ButtonsLineEdit()
        self.upload_logo_e.setReadOnly(True)
        self.upload_logo_e.setPlaceholderText(_("Specify an icon"))
        self.upload_logo_e.addButton(
            ":icons/tab_addresses.png", on_click=pick_logo, tooltip=_("Pick an icon from your local disk"))
        description_label.setBuddy(self.upload_logo_e)
        logo_grid.addWidget(self.upload_logo_e, 1, 1, 1, -1)
        self.preview_logo = QLabel(self)
        pixel_map = QPixmap(":icons/file.png").scaled(128, 128, Qt.KeepAspectRatio)
        self.preview_logo.setAlignment(Qt.AlignCenter)
        self.preview_logo.setPixmap(pixel_map)
        logo_grid.addWidget(self.preview_logo, 2, 1, 1, -1)

        self.setLayout(logo_grid)

    def is_full(self):
        return bool(self.upload_logo_e.text()) and (self.img_data is not None)

    def clear(self):
        self.upload_logo_e.clear()

    def construct_entry(self):
        return icon_entry(self.img_data)

class UHTMLForm(UKeyserverForm):
    def __init__(self, *args, **kwargs):
        super(UHTMLForm, self).__init__(*args, **kwargs)
        plain_text_grid = QGridLayout()
        msg = _('HTML to be uploaded.')
        description_label = HelpLabel(_('&HTML'), msg)
        plain_text_grid.addWidget(description_label, 0, 0)
        self.upload_html_e = QTextEdit()
        description_label.setBuddy(self.upload_html_e)
        plain_text_grid.addWidget(self.upload_html_e, 0, 1, 1, -1)

        self.setLayout(plain_text_grid)

        self.upload_html_e.textChanged.connect(self.inputs_changed.emit)

    def is_full(self):
        return bool(self.upload_html_e.toPlainText())

    def clear(self):
        self.upload_html_e.clear()

    def construct_entry(self):
        data = self.upload_html_e.toPlainText()
        return plain_text_entry(data)
