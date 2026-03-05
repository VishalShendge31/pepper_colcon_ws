from setuptools import find_packages, setup

package_name = 'openai_bridge'

setup(
    name=package_name,
    version='0.0.0',
    packages=find_packages(exclude=['test']),
    data_files=[
        ('share/ament_index/resource_index/packages',
            ['resource/' + package_name]),
        ('share/' + package_name, ['package.xml']),
        ('share/' + package_name + '/launch', ['launch/bridge_launch.py']),
    ],
    install_requires=['setuptools'],
    zip_safe=True,
    maintainer='Vishal_Shendge',
    maintainer_email='shendge.vishal.vilas@gmail.com',
    description='ROS 2 package that bridges audio transcriptions to OpenAI services for the Pepper robot.',
    license='MIT',
    tests_require=['pytest'],
    entry_points={
        'console_scripts': [
        'transcription_to_openai = openai_bridge.transcription_to_openai:main',
        ],
    },
)
