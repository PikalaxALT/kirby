import unittest
import snakemake
import pathlib
import os
import atexit
import shutil
import platform

package_dir = pathlib.Path(__file__).resolve().parent.parent
tempdir = package_dir / '.tmp'
tempdir.mkdir(parents=True, exist_ok=True)
atexit.register(shutil.rmtree, tempdir)


def call_snakemake(target: str | os.PathLike):
    return snakemake.snakemake(
        package_dir / 'Snakefile',
        targets=[str(target)],
        config={
            'tempdir': tempdir,
            'outfile': tempdir / 'outs.ips'
        },
        delete_temp_output=False,
        workdir=package_dir
    )


class TestWorkflow(unittest.TestCase):
    def test_workflow(self):
        self.assertTrue(call_snakemake('all'))


if __name__ == '__main__':
    unittest.main()
