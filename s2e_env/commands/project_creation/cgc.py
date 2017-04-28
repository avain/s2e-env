"""
Copyright (c) 2017 Dependable Systems Laboratory, EPFL

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
"""


import datetime
import logging
import os

from s2e_env.command import CommandError
from . import BaseProject


logger = logging.getLogger('cgc_project')


class CGCProject(BaseProject):
    """
    Create a CGC project.
    """

    # User instruction templates
    SEEDS_INSTS =                                                           \
        'Seed Files\n'                                                      \
        '==========\n\n'                                                    \
        'Seed files have been enabled. This means that seed files will be ' \
        'used to drive concolic execution. Please place seeds in '          \
        '{seeds_dir}. Seed files must be named using the following '        \
        'format:\n\n'                                                       \
        '\t``<index>-<priority>.pov``\n\n'                                  \
        'Where:\n'                                                          \
        '\t* <index> is a unique integer identifier starting from 0\n'      \
        '\t* <priority> is an integer priority, where 0 is the highest '    \
        'priorty\n'                                                         \
        'Examples:\n'                                                       \
        '\t0-1.pov, 1-1.pov, 2-0.pov, etc.\n\n'                             \
        'Seeds can be based on real files, generated by a fuzzer, or '      \
        'randomly.'

    def _validate_binary(self, target_arch, os_name, os_arch, os_binary_formats):
        # Check architecture consistency
        if 'decree' not in os_binary_formats:
            raise CommandError('Please use a CGC image for this binary')

    def handle(self, *args, **options):
        options['use_seeds'] = True

        return super(CGCProject, self).handle(**options)

    def _create_bootstrap(self):
        # Render the bootstrap script
        context = {
            'current_time': datetime.datetime.now(),
            'target': os.path.basename(self._target_path),
            'use_seeds': self._use_seeds,
        }

        output_path = os.path.join(self._project_path, 'bootstrap.sh')
        self._render_template(context, 'bootstrap.cgc.sh', output_path,
                              executable=True)

    def _create_config(self):
        # Render the config file
        context = {
            'current_time': datetime.datetime.now(),
            'project_dir': self._project_path,
            'target': os.path.basename(self._target_path),
            'use_seeds': self._use_seeds,
            'target_lua_template': 's2e-config.cgc.lua'
        }

        for f in ('s2e-config.lua', 'models.lua', 'library.lua'):
            output_path = os.path.join(self._project_path, f)
            self._render_template(context, f, output_path)

    def _create_dirs(self):
        recipes_path = self.install_path('share', 'decree-recipes')
        seeds_path = os.path.join(self._project_path, 'seeds')

        # Create a symlink to the recipes directory
        logger.info('Creating a symlink to %s', recipes_path)

        os.symlink(recipes_path, os.path.join(self._project_path, 'recipes'))

        # Since the Recipe plugin relies on SeedSearcher, we always need a
        # seeds directory
        os.mkdir(seeds_path)

    def _create_instructions(self):
        intro = 'Here are some hints to get started with your CGC project:'

        seeds = ''
        if self._use_seeds:
            seeds_dir = os.path.join(self._project_path, 'seeds')
            seeds = self.SEEDS_INSTS.format(seeds_dir=seeds_dir)

        # Remove empty instructions
        inst_list = [intro, seeds]
        return '\n\n'.join(inst for inst in inst_list if inst != '')
