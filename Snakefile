#!/usr/bin/env snakemake

import platform
import requests
import pathlib
import os
import tempfile
import atexit
import shutil

configfile: 'snakeconf.yml'

is_windows = platform.system() == 'Windows'

_exe_extension = '.exe' if is_windows else ''
_zip_name = f'ItemRando{"" if is_windows else "CLI-Linux"}'
_flips = 'floating\\flips.exe' if is_windows else 'floating/flips-linux'

config['outfile'] = pathlib.Path(config['outfile']).resolve()
os.makedirs(config['outfile'].parent, exist_ok=True)
resources_path = pathlib.Path('resources').resolve()

if 'tempdir' not in config:
    config['tempdir'] = tempfile.mkdtemp()
else:
    config['tempdir'] = pathlib.Path(config['tempdir']).resolve()
os.makedirs(config['tempdir'], exist_ok=True)


rule all:
    input:
        config['outfile']

rule install_zx:
    output:
        resources_path / 'zxplus' / 'universal-pokemon-randomizer-zx.jar'
    shell:
        'wget -O {output} https://github.com/choatix/zxplus/releases/download/v0.1.2.2/universal-pokemon-randomizer-zx.jar'

rule install_item_rando:
    params:
        exe_extension = _exe_extension,
        zip_name = _zip_name
    output:
        expand(resources_path / 'item-rando' / 'Pokemon Crystal Item Randomizer{exe_extension}', exe_extension=_exe_extension)
    shell:
        'wget -q -nc https://github.com/choatix/Pokemon-Crystal-Item-Randomizer/releases/download/v7.1.19/{params.zip_name}.zip ' \
        '&& unzip -oqq {params.zip_name}.zip '
        '&& rsync -dru "Pokemon Crystal Item Randomizer"/* resources/item-rando/ ' \
        '&& rm -rf "Pokemon Crystal Item Randomizer"'

rule build_baserom:
    output:
        resources_path / 'vanilla-rom' / 'pokecrystal11.gbc'
    shell:
        'docker -v {pathlib.Path(output).parent.resolve()}:/rom -w /rom kemenaran/rgbds:0.6.0 make crystal11'

rule download_flips:
    output:
        _flips
    shell:
        'wget -q -nc https://dl.smwcentral.net/11474/floating.zip ' \
        '&& unzip -qqo floating.zip -d floating ' \
        '&& rm floating.zip'

rule download_speedchoice:
    input:
        baserom=resources_path / 'vanilla-rom' / 'pokecrystal11.gbc',
        flips=_flips
    output:
        resources_path / 'speedchoice-rom' / 'crystal-speedchoice.gbc'
    shell:
        'wget -q -nc https://github.com/choatix/pokecrystal-speedchoice/releases/download/v7.4.13/Speedchoice.zip ' \
        '&& unzip -qqo Speedchoice.zip -d Speedchoice ' \
        '&& "{input.flips}" -a Speedchoice/Patches/VTo7413.ips {input.baserom} {output} ' \
        '&& rm -rf Speedchoice Speedchoice.zip'

rule invoke_zx:
    input:
        baserom=resources_path / 'speedchoice-rom' / 'crystal-speedchoice.gbc',
        jar=resources_path / 'zxplus' / 'universal-pokemon-randomizer-zx.jar',
        settings=expand(resources_path / 'zxplus/settings' / '{zx_preset}.rnqs', zx_preset=config['zx_preset']),
    params:
        seed=expand('{zx_seed}', zx_seed=config['zx_seed'])
    output:
        zxrom=temporary(expand('{tempdir}/step1.gbc', tempdir=config['tempdir']))
    shell:
        'java -Xmx768M -jar {input.jar} cli -i {input.baserom} -o {output.zxrom} -s {input.settings}'

rule invoke_itemrando:
    input:
        zxrom=expand('{tempdir}/step1.gbc', tempdir=config['tempdir']),
        cli=expand(resources_path / 'item-rando' / 'Pokemon Crystal Item Randomizer{exe_extension}', exe_extension=_exe_extension),
        settings=expand(resources_path / 'item-rando/Modes' / '{item_preset}.yml', item_preset=config['item_preset']),
    output:
        temporary(expand('{tempdir}/step2.gbc', tempdir=config['tempdir']))
    params:
        seed=expand('{item_seed}', item_seed=config['item_seed']),
    shell:
        'cd resources/item-rando && "{input.cli}" cli -i {input.zxrom} -o {output} -m {input.settings}' + (' -s {params.seed}' if config['item_seed'] else '')

rule create_patchfile:
    input:
        randorom=expand('{tempdir}/step2.gbc', tempdir=config['tempdir']),
        baserom=resources_path / 'vanilla-rom' / 'pokecrystal11.gbc',
        flips=_flips
    output:
        config['outfile']
    shell:
        '"{input.flips}" -c {input.baserom} {input.randorom} {output}'
