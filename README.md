# ComplexModelMDK
Run complex models via the MDK

To run:
* Install OasisLmf from the branch feature/new_custom_model
* Install the custom item commands and the example custom GulCalc:
'''
pip install -e .
'''
* Run the MDK commands, for example:
'''
oasislmf model run -C oasislmf.json --verbose
'''
