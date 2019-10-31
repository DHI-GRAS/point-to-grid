import pandas as pd
import numpy as np

from pointtogrid import griddef
from pointtogrid import process

PANDAS_READ_CSV_KW = dict(
    sep=';',
    decimal=',',
    dtype='float32',
    chunksize=100000
)


def get_bounds(dfiter):
    cmin = [1e9, 1e9]
    cmax = [-1e9, -1e9]
    for df in dfiter:

        if set(df.columns) != {'lon', 'lat'}:
            raise ValueError(set(df.columns))

        cmin = np.minimum(cmin, df.min().values)
        cmax = np.maximum(cmax, df.max().values)
    if (cmin > 1e4).any() or (cmax < -1e4).any():
        raise RuntimeError('Unable to get valid coordinate limits.')

    if tuple(df.columns) == ('lon', 'lat'):
        xmin, ymin = cmin
        xmax, ymax = cmax
    elif tuple(df.columns) == ('lat', 'lon'):
        ymin, xmin = cmin
        ymax, xmax = cmax
    else:
        raise ValueError(tuple(df.columns))

    return (xmin, ymin, xmax, ymax)


def flow(
    path, data_col,
    bounds_wgs=None, bounds_projected=None,
    dst_res=None, dst_crs=None,
    transform_shape=None,
    show_pbar=True,
    csvkw=None
):
    """Grid points from large CSV file of lat, lon, DATA_COL data

    Parameters
    ----------
    path : str or Path
        path to CSV file
    data_col : str
        name of data column
    bounds_wgs : tuple of floats (xmin, ymin, xmax, ymax), optional
        bounds in WGS84
    bounds_projected : tuple of floats (xmin, ymin, xmax, ymax), optional
        bounds in projected coordinates
    dst_res : float, optional
        target resolution
        if not provided, a transform must be provided
    dst_crs : dict, optional
        destination CRS
        must be in metric units, like UTM
        if not provided UTM for center coordinate
        will be computed
    transform_shape : dict with keys [transform, width, height], optional
        destination transform and shape to regrid to
    show_pbar : bool
        show progress bar while reading CSV
    csvkw : dict, optional
        keyword arguments to pass to pd.read_csv

    Returns
    -------
    data : ndarray shape (height, width)
        gridded data
    profile : dict
        rasterio-like profile that contains any
        derived information, always
        [crs, transform, width, height]
    """
    csvkw = csvkw or {}
    csvkw = dict(PANDAS_READ_CSV_KW, **csvkw)

    if (
        bounds_wgs is None and
        (bounds_projected is None or dst_crs is None) and
        transform_shape is None
    ):
        # need to read file to derive target grid
        dfiter = pd.read_csv(path, usecols=['lon', 'lat'], **csvkw)
        if show_pbar:
            import tqdm
            dfiter = tqdm.tqdm(dfiter, unit='chunk', desc='bounds')
        bounds_wgs = get_bounds(dfiter)

    profile = griddef.resolve_inputs_to_profile(
        bounds_wgs=bounds_wgs,
        bounds_projected=bounds_projected,
        dst_res=dst_res,
        dst_crs=dst_crs,
        transform_shape=transform_shape
    )

    dfiter = pd.read_csv(path, **PANDAS_READ_CSV_KW)

    def _process(df):
        return process.grid_chunk(
            lon=df['lon'].values,
            lat=df['lat'].values,
            data=df[data_col].values,
            dst_crs=profile['crs'],
            transform=profile['transform']
        )

    if show_pbar:
        import tqdm
        dfiter = tqdm.tqdm(dfiter, unit='chunk', desc='grid')

    out = np.full(fill_value=np.nan, shape=(profile['height'], profile['width']), dtype='float32')

    for df in dfiter:
        idx, data = _process(df)
        out[idx[1], idx[0]] = data

    profile.update({
        'count': 1,
        'dtype': out.dtype,
        'nodata': np.nan
    })

    return out, profile
