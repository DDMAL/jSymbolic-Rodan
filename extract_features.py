import os
import jsymbolic_utilities

from rodan.jobs.base import RodanTask
from django.conf import settings
from music21 import *


class extract_features(RodanTask):
    name = 'jSymbolic Feature Extractor'
    author = 'Cory McKay and Tristano Tenaglia'
    description = 'Extract features from a music file using the jSymbolic feature extractor'
    settings = {}
    enabled = True
    category = "jSymbolic - Feature Extraction"
    interactive = False

    input_port_types = (
        {
            'name': 'jSymbolic Music File Input',
            'minimum': 1,
            'maximum': 1,
            'resource_types': ['application/mei+xml', 'application/midi']
        },

        {
            'name': 'jSymbolic Configuration File Input',
            'minimum': 0,
            'maximum': 1,
            'resource_types': ['application/jsc+txt']
        },
    )
    output_port_types = (
        {
            'name': 'jSymbolic ACE XML Value Output',
            'minimum': 1,
            'maximum': 1,
            'resource_types': ['application/ace+xml']
        },

        {
            'name': 'jSymbolic ACE XML Definition Output',
            'minimum': 1,
            'maximum': 1,
            'resource_types': ['application/ace+xml']
        },

        {
            'name': 'jSymbolic ARFF Output',
            'minimum': 0,
            'maximum': 1,
            'resource_types': ['application/arff']
        },

        {
            'name': 'jSymbolic ARFF CSV Output',
            'minimum': 0,
            'maximum': 1,
            'resource_types': ['application/arff+csv']
        },
    )

    def run_my_task(self, inputs, job_settings, outputs):
        # Get the path of the jsymbolic jar on the system
        java_directory = settings.JSYMBOLIC_JAR

        music_file = inputs['jSymbolic Music File Input'][0]['resource_path']

        config_file_path = None
        stderr_valid = None
        try:
            config_file_path = inputs['jSymbolic Configuration File Input'][0]['resource_path']
            config_validate_input = ['java', '-jar', 'jSymbolic.jar', '-validateconfigfeatureoption', config_file_path]
            return_valid, stdout_valid, stderr_valid = jsymbolic_utilities.execute(config_validate_input,
                                                                                   java_directory)
        except:
            pass

        # If configuration file is not valid then output the standard error to the user
        if stderr_valid:
            self.my_error_information(None, stderr_valid)
            return False

        # If everything is valid in configuration file, then make sure CSV and ARFF are true
        # if they are not, then force to be false to accommodate Rodan output ports
        csv_false = 'convert_to_csv=false'
        csv_true = 'convert_to_csv=true'
        arff_false = 'convert_to_arff=false'
        arff_true = 'convert_to_arff=true'
        jsymbolic_utilities.replace(config_file_path, csv_false, csv_true)
        jsymbolic_utilities.replace(config_file_path, arff_false, arff_true)

        if config_file_path:
            config_input = ['java', '-jar', 'jSymbolic.jar', '-configrun', config_file_path, music_file,
                            outputs['jSymbolic ACE XML Value Output'][0]['resource_path'],
                            outputs['jSymbolic ACE XML Definition Output'][0]['resource_path']]
            return_value, stdout, stderr = jsymbolic_utilities.execute(config_input, java_directory)
        else:
            default_input = ['java', '-jar', 'jSymbolic.jar', '-csv', '-arff', music_file,
                             outputs['jSymbolic ACE XML Value Output'][0]['resource_path'],
                             outputs['jSymbolic ACE XML Definition Output'][0]['resource_path']]
            return_value, stdout, stderr = jsymbolic_utilities.execute(default_input, java_directory)

        # TODO What to do with the error output from jSymbolic?
        # Return if jsymbolic experienced an error so no further file processing is done
        if stderr:
            self.my_error_information(None, stderr)
            return False

        # Split up filename and extension for arff and csv files
        pre, ext = os.path.splitext(outputs['jSymbolic ACE XML Value Output'][0]['resource_path'])

        try:
            # Try to get arff file if it exists, otherwise continue
            src_arff_file_path = "{0}.arff".format(pre)
            jsymbolic_utilities.copy_when_exists(src_arff_file_path,
                                                 outputs['jSymbolic ARFF Output'][0]['resource_path'])
        except:
            pass

        try:
            # Try to get csv file if it exists, otherwise continue
            src_csv_file_path = "{0}.csv".format(pre)
            jsymbolic_utilities.copy_when_exists(src_csv_file_path,
                                                 outputs['jSymbolic ARFF CSV Output'][0]['resource_path'])
        except:
            pass

        return return_value

    def test_my_task(self, testcase):
        # No tests for now
        pass

    # TODO implement this maybe to output error as a traceback
    # TODO this might work now but it double check with Ryan on Rodan client
    # TODO should either return traceback or exc (Exception) in error_details
    def my_error_information(self, exc, traceback):
        return {'error_summary': 'jSymbolic Standard Error', 'error_details': traceback}
