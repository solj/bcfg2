import logging
import Bcfg2.Server.Plugin
from Bcfg2.Server.Plugins.Cfg import CfgGenerator, SETUP
try:
    from Bcfg2.Encryption import ssl_decrypt, EVPError
    have_crypto = True
except ImportError:
    have_crypto = False

logger = logging.getLogger(__name__)

class CfgEncryptedGenerator(CfgGenerator):
    __extensions__ = ["crypt"]

    def __init__(self, fname, spec, encoding):
        CfgGenerator.__init__(self, fname, spec, encoding)
        if not have_crypto:
            msg = "Cfg: M2Crypto is not available: %s" % entry.get("name")
            logger.error(msg)
            raise Bcfg2.Server.Plugin.PluginExecutionError(msg)

    @property
    def passphrases(self):
        section = "cfg:encryption"
        if SETUP.cfp.has_section(section):
            return dict([(o, SETUP.cfp.get(section, o))
                         for o in SETUP.cfp.options(section)])
        else:
            return dict()

    def handle_event(self, event):
        if event.code2str() == 'deleted':
            return
        try:
            crypted = open(self.name).read()
        except UnicodeDecodeError:
            crypted = open(self.name, mode='rb').read()
        except:
            logger.error("Failed to read %s" % self.name)
            return
        # todo: let the user specify a passphrase by name
        self.data = None
        for passwd in self.passphrases.values():
            try:
                self.data = ssl_decrypt(crypted, passwd)
                return
            except EVPError:
                pass
        logger.error("Failed to decrypt %s" % self.name)

    def get_data(self, entry, metadata):
        if self.data is None:
            raise Bcfg2.Server.Plugin.PluginExecutionError("Failed to decrypt %s" % self.name)
        return CfgGenerator.get_data(self, entry, metadata)
