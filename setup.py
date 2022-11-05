from setuptools import setup,find_packages

setup(
    name='listing_scraper',
    version='0.1.0',
    author='Kobakhit',
    author_email='kobakhit@gmail.com',
    packages=find_packages(),
    # packages=['listing_scraper','listing_scraper.st','listing_scraper.sg'],
    scripts=[],
    url='',
    license='LICENSE.txt',
    description='Tool to scrape listings from major online exchanges.',
    long_description=open('README.md').read(),
    install_requires=[
        "tqdm",
        "pytest",
    ]
)