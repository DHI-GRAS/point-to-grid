from pointtogrid import coords


def resolve_inputs_to_profile(
    bounds_wgs=None, bounds_projected=None,
    dst_res=None, dst_crs=None, transform_shape=None,
):
    """Resolve grid-related input parameters to a definition of a target UTM grid

    Parameters
    ----------
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

    Returns
    -------
    profile : dict
        rasterio-like profile that contains any
        derived information, always
        [crs, transform, width, height]
    """
    if bounds_wgs is None:
        if bounds_projected is None:
            if transform_shape is not None:
                bounds_projected = coords.bounds_from_transform_shape(*transform_shape)
            else:
                raise ValueError(
                    'You must provide either bounds_projected, bounds_wgs and dst_crs, '
                    'or transform_shape.'
                )

    if bounds_projected is not None and dst_crs is None:
        raise ValueError('When you provide bounds_projected, please also provide dst_crs.')

    # derive crs if necessary
    if dst_crs is None:
        assert bounds_wgs is not None  # for sanity
        xmin, ymin, xmax, ymax = bounds_wgs
        dst_crs = coords.get_utm_crs(
            lon_center=((xmax + xmin) / 2),
            lat_center=((ymax + ymin) / 2)
        )

    if bounds_wgs is not None and bounds_projected is None:
        assert dst_crs is not None  # for sanity
        bounds_projected = coords.reproject_bounds(bounds_wgs, dst_crs)

    # derive transform and shape if necessary
    if transform_shape is not None:
        missing = {'transform', 'height', 'width'} - set(transform_shape)
        if missing:
            raise ValueError(f'transform_shape is missing keys: {missing}.')
        dst_res = transform_shape['transform'].a
    elif dst_res is None:
        raise ValueError('You must provide either target transform or dst_res.')

    if transform_shape is None:
        transform_shape = coords.transform_shape_from_bounds(*bounds_projected, res=dst_res)

    profile = dict(transform_shape, crs=dst_crs)
    return profile
