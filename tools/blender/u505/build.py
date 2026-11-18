# U-505 exterior model: build script.
#
# In Blender's Python console or Text Editor (or via MCP):
#   D = r"<repo>\tools\blender\u505\\"
#   G = {'__name__': 'u505', 'D': D}
#   exec(open(D + 'build.py').read(), G)
#   G['build']()                       # everything
#   G['build'](['tower', 'deck'])      # selected parts only (each rebuilds its own collection)
#
# Each part module defines build_<part>() and clears/recreates its own collection,
# so any part can be re-run on its own.

import os

PARTS = ['hull', 'casing', 'tower', 'stern', 'bow', 'deck', 'armament', 'rigging', 'materials', 'scene']


def load(D, G, name):
    exec(open(os.path.join(D, name + '.py')).read(), G)


def load_all():
    """Load every module's definitions (helpers such as use_set / shoot) without building."""
    G = globals()
    D = G['D']
    load(D, G, 'common')
    for p in PARTS:
        if os.path.exists(os.path.join(D, p + '.py')):
            load(D, G, p)


def build(parts=None):
    G = globals()
    load_all()
    todo = parts or PARTS
    for p in todo:
        fn = G.get('build_' + p)
        if fn is None:
            print('skip (no builder):', p)
            continue
        if fn:
            fn()
            print('built', p)
