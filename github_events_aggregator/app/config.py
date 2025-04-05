import toml


class Config:
    def __init__(self, path: str, spec_path):
        self.config = self._parse_config(path)
        self.spec = self._parse_config(spec_path)

        self._validate_toml()

        github = self.config.get("kafka")
        self.github_repositories = github.get("repositories")
        self.github_authentication_tokens = github.get("authentication_tokens")
        self.github_max_repositories = github.get("max_repositories")

        self.github_refresh_rate = github.get("refresh_rate_s", self.spec['github']['refresh_rate_s']['default'])
        self.github_max_retry = github.get("auto_offset_reset", self.spec['github']['max_retry']['default'])
        self.github_retry_attempts = github.get("retry_attempts", self.spec['github']['retry_attempts']['default'])
        self.github_backoff_factor = github.get("backoff_factor", self.spec['github']['backoff_factor']['default'])
        self.github_status_forcelist = github.get("status_forcelist", self.spec['github']['status_forcelist']['default'])

        aggregator = self.config.get("aggregator")
        self.aggregator_rolling_days = aggregator.get("rolling_days", self.spec['aggregator']['rolling_days']['default'])
        self.aggregator_rolling_events = aggregator.get("rolling_events", self.spec['aggregator']['rolling_events']['default'])

    @staticmethod
    def _parse_config(path: str) -> dict:
        with open(path, "r") as f:
            return toml.load(f)

    def _get_missing_required_params(self) -> set[str]:
        spec_required_params = []
        for spec_source, spec_attribute in self.spec.items():
            for spec_attribute_k, spec_attribute_v in spec_attribute.items():
                if spec_attribute_v["required"]:
                    spec_required_params.append(f"{spec_source}.{spec_attribute_k}")

        config_required_params = []
        for source, attribute in self.config.items():
            config_required_params = config_required_params + [
                f"{source}.{v}" for v in attribute.keys()
            ]

        return set(spec_required_params).difference(set(config_required_params))

    def _validate_toml(self):
        missing_required_params = self._get_missing_required_params()
        if len(missing_required_params) > 0:
            raise ValueError(
                "The following required parameters are not specified: "
                + ", ".join(missing_required_params)
            )

    def _validate_repositories(self):
        if type(self.github_repositories) != list:
            raise TypeError("Github repositories must be a list")
        if type(self.github_authentication_tokens) != list:
            raise TypeError("Github authentication_tokens must be a list")
        if len(self.github_repositories) == 0:
            raise ValueError("Github repositories must contain at least 1 repository")
        if len(self.github_authentication_tokens) == 0:
            raise ValueError("Github authentication_tokens must contain at least 1 authentication token")

if __name__ == "__main__":
    conf = Config("../../config.toml", "../../config.spec.toml")
