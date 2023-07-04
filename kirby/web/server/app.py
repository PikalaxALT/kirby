import os
import tempfile
import datetime
import subprocess
from quart import Quart, send_file, render_template, request, redirect, url_for
from kirby import __module_dir__
from kirby.util.item_rando_caller import ItemRandoCaller
from kirby.cli import CLI


def escape(s: str):
    return s.replace('\n', '<br>')


def make_app(args: CLI, rando: ItemRandoCaller):
    app = Quart(
        'kirby',
        template_folder=__module_dir__ / 'web/server/templates',
        static_folder=__module_dir__ / 'web/server/static'
    )

    @app.template_filter(name='basename')
    def basename(path):
        return os.path.basename(path)

    @app.route('/')
    async def generate_page():
        return await render_template(
            'rando_landing.html', 
            zx_presets=[x.stem for x in sorted(rando.upr_settings_files)], 
            item_presets=[x.stem for x in sorted(rando.item_rando_presets)]
        )

    @app.route('/', ['POST'])
    async def generate_route():
        form = await request.form
        outfname = tempfile.mktemp(suffix='.ips')
        try:
            await rando(outfile=outfname, **form)
            return await send_file(outfname)
        except Exception as e:
            if (subprocess_error := isinstance(e, subprocess.CalledProcessError)):
                e.stdout = escape(e.stdout)
                e.stderr = escape(e.stderr)
            return await render_template('generate_route_error.html', e=e, subprocess_error=subprocess_error)

    return app
