# Pokemon Crystal Item Rando Seed Generation Bot

A Discord bot to generate patch files that, when applied to a vanilla copy of Pokemon Crystal (U)(1.1), will randomize the locations of all monsters and items according to user preferences.

## Setup

Create a Python virtual environment with the packages outlined in `requirements.txt`.

You will need to provide the following resources:

- Discord bot token, required for the bot to login to discord
- Vanilla copy of [Pokemon Crystal (U)(1.1)](/pret/pokecrystal)
- Unmodified copy of [Pokemon Crystal Speedchoice v7.4.13 or later](/choatix/pokecrystal-speedchoice/releases/tag/latest)
- [Universal Pokemon Randomizer ZX v0.1.2.1 or later](/choatix/zxplus/releases/tag/latest)
- [Pokemon Crystal Item Randomizer v7.1.19 or later](/choatix/Pokemon-Crystal-Item-Randomizer/releases/tag/latest)

Download the four files and make note of where they were downloaded to. In the case of vanilla Pokemon Crystal, you may compile it from the linked source (requires a *NIX commandline with rgbds v0.6.0 or later) or obtain a legitimate copy of US version 1.1 by any means.

The five required resources may be supplied in one of three ways with decreasing priority:

1. As parameters to the bot itself (run `python -m kirby --help` for details)
2. Via a `.env` file (see [`kirby.example.env`](blob/master/kirby.example.env))
3. Via environment variables of the same names as in 2.

## Running

Your host should execute:

```python
python -m kirby [PARAMS]
```
