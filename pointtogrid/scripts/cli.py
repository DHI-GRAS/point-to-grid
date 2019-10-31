import click

COG_PROFILE = {
    'driver': 'GTiff',
    'interleave': 'pixel',
    'tiled': True,
    'blockxsize': 256,
    'blockysize': 256,
    'photometric': 'MINISBLACK',
    'ZLEVEL': 1,
    'ZSTD_LEVEL': 9,
    'BIGTIFF': 'IF_SAFER',
    'compress': 'DEFLATE'
}


class BoundsType(click.ParamType):
    name = 'bounds'

    def convert(self, value, param, ctx):
        bounds = tuple(map(float, ','.split(value)))
        if not len(bounds) == 4:
            raise ValueError('Bounds must be comma-separated sequence of 4 floats')
        return bounds


class CRSType(click.ParamType):
    name = 'crs'

    def convert(self, value, param, ctx):
        import rasterio.crs
        return rasterio.crs.CRS({'init': f'epsg:{value}'})


@click.group()
def cli():
    """Grid huge point cloud to a regular UTM grid"""
    pass


@cli.command()
@click.argument('csvfile')
@click.argument('outfile')
@click.option('--data-col', default='z', show_default=True, help='Name of data column')
@click.option(
    '--bounds-wgs', type=BoundsType(),
    help='Target grid bounds in WGS84 (xmin,ymin,xmax,ymax; will be derived if not provided)'
)
@click.option(
    '--bounds-projected', type=BoundsType(),
    help='Target grid bounds in projected coordinates (xmin,ymin,xmax,ymax)'
)
@click.option(
    '--dst-res', type=click.FLOAT, required=True,
    help='Target grid resolution resolution in projection units'
)
@click.option('--dst-crs', type=CRSType(), help='Target coordinate reference system (epsg code)')
@click.option(
    '--chunksize', type=click.INT, default=100000, show_default=True,
    help='Process the CSV in chunks of this size'
)
def gridme(csvfile, outfile, chunksize, **kwargs):
    """Grid point cloud to UTM grid"""
    from pointtogrid import peskycsv

    import rasterio
    from rio_cogeo import cogeo

    data, profile = peskycsv.flow(
        path=csvfile, show_pbar=True,
        csvkw=dict(
            chunksize=chunksize
        ),
        **kwargs
    )

    profile = dict(profile, **COG_PROFILE)

    with rasterio.MemoryFile() as memfile:
        with memfile.open(**profile) as mem:
            mem.write(data, indexes=1)
            cogeo.cog_translate(mem, outfile, profile)


def fillme():
    """Fill holes in grid"""
    pass
