from setuptools import setup
import complex_model
import oasislmf.utils 

setup(
    name='RiskFrontiers_HailAUS',
    version='0.0.1',
    entry_points={
        'console_scripts': [
            'complex_itemtobin=oasislmf.model_execution.complex_items_to_bin:main',
            'complex_itemtocsv=oasislmf.model_execution.complex_items_to_csv:main',
            'RiskFrontiers_HailAUS_gulcalc=complex_model.RiskFrontiers_HailAUS_gulcalc:main'
        ]
    }
)
