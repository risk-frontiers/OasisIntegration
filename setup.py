from setuptools import setup
import complex_model
import oasislmf.utils 

setup(
    name='RiskFrontiers_HailAUS',
    version='1.2.0',
    entry_points={
        'console_scripts': [
            'complex_itemtobin=oasislmf.execution.complex_items_to_bin:main',
            'complex_itemtocsv=oasislmf.execution.complex_items_to_csv:main',
            'RiskFrontiers_HailAUS_gulcalc=complex_model.RiskFrontiers_HailAUS_gulcalc:main'
        ]
    }
)
