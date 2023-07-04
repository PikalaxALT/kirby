# Pokemon Crystal Item Rando Seed Generation Bot

A Discord bot to generate patch files that, when applied to a vanilla copy of Pokemon Crystal (U)(1.1), will randomize the locations of all monsters and items according to user preferences.

## Setup

### Windows

You will need:
- MSYS2 on the path, this also puts the wget utility on the path. The following packages from pacman are also required:
  - rsync
- [unzip.exe](http://stahlworks.com/tool-zipunzip), the command-line interface for ZIP.

### Ubuntu

Add the [deadsnakes ppa](https://launchpad.net/~deadsnakes/+archive/ubuntu/ppa) package repositories, then install `gcc openjdk-17-jre-headless libgtk-3-dev unzip python3.11-dev python3.11-venv`

### Common

Create a Python virtual environment with the packages `snakemake python-dotenv discord.py pyyaml`. `wheel` is also required, to install `snakemake`.

You will need to provide the following resources:

- Java JRE-17 or newer
- Python 3.11 or newer (may also work on Python 3.10)
- Discord bot token, required for the bot to login to discord
- Optional: Docker, to build the base ROMs (Windows and WSL: install Docker Desktop and use WSL v2)

Install additional resources by running `snakemake --snakefile kirby/Snakefile -d kirby -c$(nproc) resources`. You should do this at least once before starting up the bot for the first time.

You will need to manually install settings files for the UPR-ZX into `kirby/resources

You can also manually download the following resources:
- Vanilla copy of Pokemon Crystal (U)(1.1) ([disassembly](https://github.com/pret/pokecrystal))
- [Floating IPS](https://www.smwcentral.net/?p=section&a=details&id=11474) (to apply the speedchoice patch and create rando patches)
- Unmodified copy of [Pokemon Crystal Speedchoice v7.4.13 or later](https://github.com/choatix/pokecrystal-speedchoice/releases)
- [Universal Pokemon Randomizer ZX v0.1.2.1 or later](https://github.com/choatix/zxplus/releases)
- [Pokemon Crystal Item Randomizer v7.1.19 or later](https://github.com/choatix/Pokemon-Crystal-Item-Randomizer/releases)

## Standalone randomizer invocation:

Create an IPS patch against vanilla crystal by running `snakemake -c1 -d kirby --snakefile kirby/Snakefile -C outfile=path/to/save/patch.ips`.

## Connecting the bot to Discord

This bot only has a command-line interface. The usage message is reproduced below.

```bash
usage: python -m kirby [-h] [--dotenv DOTENV_FILE] [--token TOKEN] [--prefix COMMAND_PREFIX] [--vanilla-rom VANILLA_ROM]
                       [--speedchoice-rom SPEEDCHOICE_ROM] [--upr-zx-jar UPR_ZX_JAR_PATH] [--upr-zx-settings UPR_ZX_SETTINGS_PATH]  
                       [--item-rando ITEM_RANDO_PATH] [--flips FLIPS_PATH] [--webapp-host WEBAPP_HOST] [--webapp-port WEBAPP_PORT]  

Launch the KIRBY Discord bot to generate key item rando ROMs

options:
  -h, --help            show this help message and exit
  --dotenv DOTENV_FILE  Path to a .env file defining the required variables. See kirby.example.env for details.
  --token TOKEN         Discord auth token (.env: KIRBY_DISCORD_TOKEN)
  --prefix COMMAND_PREFIX
                        Command prefix to use with the bot (.env: KIRBY_COMMAND_PREFIX)
  --vanilla-rom VANILLA_ROM
                        Path to a vanilla copy of Pokemon Crystal (U)(1.1) (.env: KIRBY_VANILLA_ROM)
  --speedchoice-rom SPEEDCHOICE_ROM
                        Path to a copy of Pokemon Crystal Speedchoice V7 Shopsanity (.env: KIRBY_SPEEDCHOICE_ROM)
  --upr-zx-jar UPR_ZX_JAR_PATH
                        Path to the Universal Pokemon Randomizer ZX JAR (.env: KIRBY_UPR_ZX_JAR)
  --upr-zx-settings UPR_ZX_SETTINGS_PATH
                        Path to the Universal Pokemon Randomizer ZX settings folder (.env: KIRBY_UPR_ZX_SETTINGS)
  --item-rando ITEM_RANDO_PATH
                        Path to the folder containing the item randomizer CLI and modes (.env: KIRBY_ITEM_RANDO_PATH)
  --flips FLIPS_PATH    Path to the Floating IPS binary (.env: KIRBY_FLOATING_IPS)
  --webapp-host WEBAPP_HOST
                        Address from which to host the web app (.env: KIRBY_WEBAPP_HOST)
  --webapp-port WEBAPP_PORT
                        Port over which to host the web app (.env: KIRBY_WEBAPP_PORT)

Parameter resolution order:
  1. Arguments passed via this interface will take top priority
  2. If --dotenv is passed, any arguments not defined in 1. will be taken from the dotenv file
  3. Otherwise, the same variables defined in the runtime environment will be used
  4. The final fallback value for path-like arguments is what is set in snakeconf.yml.
```

## Updating Speedchoice, ZXPlus, or the Item Randomizer

The maintainer of this bot's source code shall update the parameters in `snakeconf.yml` tagged "Version info" any time new versions of the underlying binaries are released.

## Web application

Launching the Discord bot will also launch a minimal web frontend that will generate a patch and send it to you as a file. By default, this app will be served locally on port 5000. You can change this to a public IP or domain using the `--webapp-host` and `--webapp-port` options or the corresponding environment variables. This application does not use cookies or store any user data.
