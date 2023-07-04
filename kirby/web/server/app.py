import os
import tempfile
import datetime
import subprocess
from quart import Quart, send_file
from kirby.util.item_rando_caller import ItemRandoCaller
from kirby.cli import CLI


def escape(s: str):
    return s.replace('\n', '<br>')


def make_app(args: CLI):
    app = Quart('kirby')
    rando = ItemRandoCaller(args)

    @app.route('/')
    async def landing():
        return 'Hello world!'

    @app.route('/generate/<zx_preset>/<item_preset>')
    async def generate(*, zx_preset, item_preset, item_seed=None, zx_seed=None):
        outfname = tempfile.mktemp(suffix='.ips')
        try:
            await rando(zx_preset=zx_preset, zx_seed=zx_seed, item_preset=item_preset, item_seed=item_seed, outfile=outfname)
            return await send_file(outfname, as_attachment=True, attachment_filename=f'rando-patch-{datetime.datetime.now().timestamp()}.ips')
        except subprocess.CalledProcessError as e:
            return f'<b>Error generating the ROM</b><br><br>' \
                   f'stdout:<br><font style="font-family:\'Courier New\'">{escape(e.stdout)}</font><br><br>' \
                   f'stderr:<br><font style="font-family:\'Courier New\'">{escape(e.stderr)}</font>'

    return app
