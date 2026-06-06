"""Compile the project's SCSS sources to CSS.

Run as part of the build (before ``collectstatic``):

    python manage.py compile_scss

Every top-level ``.scss`` file in ``staticfiles/css/`` (i.e. files whose name
does not start with ``_``) is compiled to a sibling ``.css`` file. Partials
(``_color.scss``, ``_generic.scss``, ...) are imported by those entry points
and are not compiled on their own.
"""

from pathlib import Path

import sass
from django.conf import settings
from django.core.management.base import BaseCommand


class Command(BaseCommand):
    help = 'Compiles staticfiles/css/*.scss into matching .css files.'

    def add_arguments(self, parser):
        parser.add_argument(
            '--output-style',
            default='compressed',
            choices=['nested', 'expanded', 'compact', 'compressed'],
            help='libsass output style (default: compressed).',
        )

    def handle(self, *args, **options):
        css_dir = Path(settings.BASE_DIR) / 'staticfiles' / 'css'
        if not css_dir.is_dir():
            self.stderr.write(f'No SCSS directory found at {css_dir}')
            return

        entries = sorted(
            p for p in css_dir.glob('*.scss') if not p.name.startswith('_')
        )
        if not entries:
            self.stdout.write('No SCSS entry points found.')
            return

        # Remove previously generated CSS so that a compiled file (e.g.
        # base.css) does not make an ``@import "base"`` ambiguous during this run.
        for scss_path in entries:
            scss_path.with_suffix('.css').unlink(missing_ok=True)

        # Compile everything in memory first, then write — keeps the source tree
        # free of .css files while imports are being resolved.
        compiled = {}
        for scss_path in entries:
            compiled[scss_path.with_suffix('.css')] = sass.compile(
                filename=str(scss_path),
                output_style=options['output_style'],
                include_paths=[str(css_dir)],
            )

        for css_path, css in compiled.items():
            css_path.write_text(css, encoding='utf-8')
            self.stdout.write(self.style.SUCCESS(f'  {css_path.stem}.scss -> {css_path.name}'))

        self.stdout.write(self.style.SUCCESS(f'Compiled {len(entries)} stylesheet(s).'))
