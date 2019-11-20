from setuptools import find_packages, setup

setup(
    name='pointtogrid',
    version='0.2.0',
    description='Grid a large point cloud to a regular UTM grid',
    author='Jonas Sølvsteen',
    author_email='josl@dhigroup.com',
    packages=find_packages(),
    install_requires=[
        'rasterio',
        'rio_cogeo',
        'affine',
        'numpy',
        'numba',
        'pandas',
        'shapely',
        'click',
        'tqdm',
    ],
    entry_points='''
    [console_scripts]
    pointtogrid=pointtogrid.scripts.cli:cli
    ''',
)
