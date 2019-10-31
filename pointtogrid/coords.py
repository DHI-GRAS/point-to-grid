import affine
import numpy as np
import shapely.geometry
import rasterio.warp
import rasterio.crs

CRS_WGS = rasterio.crs.CRS({'init': 'epsg:4326'})


def get_utm_crs(lon_center, lat_center):
    """Derive CRS for UTM zone matching coordinates

    Parameters
    ----------
    lon_center, lat_center : float
        coordinates of center of image

    Returns
    -------
    dict
        init: epsg code
    """
    zone_base = 32700 if lat_center < 0 else 32600
    epsg_code = zone_base + 1 + int((180 + lon_center) / 6)
    return {'init': f'epsg:{epsg_code}'}


def transform_shape_from_bounds(xmin, ymin, xmax, ymax, res):
    """Generate transform and shape for bounds

    Parameters
    ----------
    xmin, ymin, xmax, ymax : float
        bounds coordinates
    res : float
        target resolution

    Returns
    -------
    dict
        rasterio profile-like dict
        with transform, width, and height
    """
    return {
        'transform': affine.Affine(res, 0, xmin, 0, -res, ymax),
        'width': int(np.ceil((xmax - xmin) / res)),
        'height': int(np.ceil((ymax - ymin) / res))
    }


def bounds_from_transform_shape(transform, width, height):
    xmin, ymax = transform * (0, 0)
    xmax, ymin = transform * (width, height)
    return (xmin, ymin, xmax, ymax)


def reproject_bounds(bbox, dst_crs, src_crs=CRS_WGS):
    geom_mapping = shapely.geometry.mapping(
        shapely.geometry.box(*bbox)
    )
    return shapely.geometry.shape(
        rasterio.warp.transform_geom(src_crs, dst_crs, geom_mapping)
    ).bounds
