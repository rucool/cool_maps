from ._version import get_versions
__version__ = get_versions()['version']
del get_versions

from .plot import (
    create,
    add_bathymetry,
    add_colorbar,
    add_currents,
    add_double_temp_colorbar,
    add_features,
    add_marker,
    add_ticks,
    export_fig,
    load_fig,
    save_fig,
    set_engine,
    get_engine,
    available_engines,
)
from .download import get_bathymetry
