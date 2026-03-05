from setuptools import setup
import os
from glob import glob

package_name = 'pepper_teleop'

setup(
    name=package_name,
    version='0.0.1',
    packages=[package_name],
    data_files=[
        ('share/ament_index/resource_index/packages',
            ['resource/' + package_name]),
        ('share/' + package_name, ['package.xml']),
        (os.path.join('share', package_name, 'launch'), glob('pepper_teleop/launch/*.launch.py')),
    ],
    install_requires=['setuptools'],
    zip_safe=True,
    maintainer='Vishal_Shendge',
    maintainer_email='shendge.vishal.vilas@gmail.com',
    description='Keyboard teleop package for Pepper robot',
    license='MIT',
    tests_require=['pytest'],
    entry_points={
        'console_scripts': [
            'teleop_keyboard = pepper_teleop.teleop_keyboard:main',
        ],
    },
)
