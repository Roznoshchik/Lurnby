from .commands import ListCmd, InstallCmd


class OutdatedList(object):

    def __init__(self, dry_run=False):
        self.list_cmd = ListCmd()
        self.install_cmd = InstallCmd()
        self.dry_run = dry_run

    @property
    def outdated(self):
        return self.list_cmd.outdated_packages

    def upgrade(self, name, local, remote):
        if self.dry_run:
            self.install_cmd.dry_run(name, local, remote)
        else:
            self.install_cmd.upgrade(name)
