from setuptools import setup
import os
from glob import glob

package_name = 'pepper_bringup'

setup(
    name=package_name,
    version='0.0.1',
    packages=[],
    data_files=[
        ('share/ament_index/resource_index/packages',
            ['resource/' + package_name]),
        ('share/' + package_name, ['package.xml']),
        (os.path.join('share', package_name, 'launch'),
            glob('launch/*.py')),
    ],
    install_requires=['setuptools'],
    zip_safe=True,
    maintainer='Vishal_Shendge',
    maintainer_email='shendge.vishal.vilas@gmail.com',
    description='Launch package that brings up all Pepper robot ROS2 nodes',
    license='MIT',
    tests_require=['pytest'],
    entry_points={},
)
