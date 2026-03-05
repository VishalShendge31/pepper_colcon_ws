from setuptools import find_packages, setup

package_name = 'pepper_audio_transcriber'

setup(
    name=package_name,
    version='0.0.0',
    packages=find_packages(exclude=['test']),
    data_files=[
        ('share/ament_index/resource_index/packages',
            ['resource/' + package_name]),
        ('share/' + package_name, ['package.xml']),
    ],
    install_requires=['setuptools'],
    zip_safe=True,
    maintainer='Vishal_Shendge',
    maintainer_email='shendge.vishal.vilas@gmail.com',
    description='ROS 2 package for transcribing audio data from the Pepper robot using Whisper.',
    license='MIT',
    # REMOVED: tests_require=['pytest'] - Line 18 DELETED
    entry_points={
        'console_scripts': [
            'whisper_transcriber = pepper_audio_transcriber.whisper_transcriber:main',
        ],
    },
)
