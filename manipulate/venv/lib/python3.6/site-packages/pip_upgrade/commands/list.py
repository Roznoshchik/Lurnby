from pip.commands import ListCommand


class ListCmd(object):
    def __init__(self):
        self.cmd = ListCommand()
        self.options, self.args = self.cmd.parser.parse_args(['-o'])

    @property
    def outdated_packages(self):
        for package_data in self.cmd.find_packages_latests_versions(
                self.options):
            dist, remote = package_data[0], package_data[1:]
            if len(remote) == 1:  # Later versions of pip
                remote_parsed = remote[0]
            else:
                remote_parsed = remote[-1]
            if remote_parsed > dist.parsed_version:
                yield dist.project_name, dist.parsed_version, remote_parsed