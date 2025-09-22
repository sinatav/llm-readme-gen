from jinja2 import Environment, FileSystemLoader, select_autoescape
from pathlib import Path
from typing import Dict


class TemplateEngine:
    def __init__(self, template_dir: Path):
        self.env = Environment(
            loader=FileSystemLoader(str(template_dir)),
            autoescape=select_autoescape(enabled_extensions=("html",))
        )

    def render(self, template_name: str, context: Dict) -> str:
        tpl = self.env.get_template(template_name)
        return tpl.render(**context)
