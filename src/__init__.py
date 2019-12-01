
import sys
from os.path import join, dirname, abspath


__version__ = '2.1.1'

IN_EXE = hasattr(sys, 'frozen')
pkg_direc = dirname(dirname(abspath(__file__)))
# if IN_EXE:
#     base_direc = src_direc
# else:
#     base_direc = dirname(src_direc)
img_direc = join(pkg_direc, 'images')
file_direc = join(pkg_direc, 'files')

diff_values = {
    'b': ( 8,  8,  10),
    'i': (16, 16,  40),
    'e': (30, 16,  99),
    'm': (30, 30, 200),
    'c': None
}
default_settings = {
    'x_size': 8,
    'y_size': 8,
    'mines': 10,
    'diff': 'b',
    'first_success': True,
    'per_cell': 1,
    # 'radius': 1,    # Implement later
    'drag_select': False,
    'btn_size': 16, #pixels
    'name': '',
    'styles': {
        'buttons': 'Standard',
        'numbers': 'Standard',
        'markers': 'Standard'
        },
    'hscore_sort': 'time',
    'hscore_filters': {
        'name': '',
        'flagging': '',
    }
}
