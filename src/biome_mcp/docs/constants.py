from typing import Literal

type Section = Literal["cli", "configuration", "linter"]

DOCUMENTATION_SECTIONS: tuple[Section, ...] = ("cli", "configuration", "linter")

DOCS_URLS: dict[Section, str] = {
    "cli": "https://biomejs.dev/reference/cli/",
    "configuration": "https://biomejs.dev/reference/configuration/",
    "linter": "https://biomejs.dev/linter/javascript/rules/",
}

NPM_BIOME_URL = "https://registry.npmjs.org/@biomejs/biome/latest"
CLI_PREFIX = "biome "
HTTP_TIMEOUT = 30.0
VERSION_FILE = "version.json"
