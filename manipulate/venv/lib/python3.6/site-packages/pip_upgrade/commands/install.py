from pip.commands import InstallCommand


def display_version(version):
    if isinstance(version, tuple):  # Support older pip versions
        return ".".join(part.lstrip('0') or '0' for part in version)
    return version.public


class InstallCmd(object):
    def __init__(self):
        self.cmd = InstallCommand()

    def dry_run(self, name, local, remote):
        print("Would update {0} {1} -> {2}".format(
            name, display_version(local), display_version(remote)))

    def upgrade(self, name):
        options, args = self.cmd.parser.parse_args(['-U', name])
        self.cmd.run(options, args)