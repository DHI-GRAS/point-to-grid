import numpy as np
import numba
import rasterio.warp
import rasterio.crs

CRS_WGS = rasterio.crs.CRS({'init': 'epsg:4326'})


@numba.jit('float32[:](float32[:], int64[:], int64)', nopython=True, parallel=True)
def map_reduce_nanmean(data, inverse, num_unique):
    out = np.full(fill_value=np.nan, shape=(num_unique, ), dtype=data.dtype)
    for k in numba.prange(num_unique):
        selection = np.where(inverse == k)
        out[k] = np.nanmean(data[selection])
    return out


def grid_chunk(lon, lat, data, dst_crs, transform, src_crs=CRS_WGS):
    """Average data into grid cells

    Parameters
    ----------
    lon, lat : 1D ndarray
        point coordinates
    data : ndarray (same shape as lat, lon)
        data to average for each grid cell
    dst_crs : dict or CRS
        target CRS
    transform : affine.Affine
        target grid transform
    src_crs : dict or CRS
        source CRS

    Returns
    -------
    unique_idx : ndarray shape (2, N)
        i, j indices of target grid cells to fill
    data : ndarray shape (N, )
        computed values to fill into grid
    """
    # transform coordinates
    xs, ys = map(np.asarray, rasterio.warp.transform(
        src_crs=src_crs,
        dst_crs=dst_crs,
        xs=lon,
        ys=lat
    ))

    # flooring the transformed (pixel center) point coords gives nearest
    # (0-based) grid cell center index
    idx = np.vstack([v.astype('int64') for v in (~transform * (xs, ys))])

    uidx, inverse = np.unique(idx, axis=1, return_inverse=True)
    datareduced = map_reduce_nanmean(data, inverse, num_unique=uidx.shape[1])

    return uidx, datareduced
