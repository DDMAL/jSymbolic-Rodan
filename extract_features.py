import os
import shutil

import sys

import jsymbolic_utilities

from rodan.jobs.base import RodanTask
from django.conf import settings


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
        music_file = inputs['jSymbolic Music File Input'][0]['resource_path']

        config_file = None
        try:
            config_file = inputs['jSymbolic Configuration File Input'][0]['resource_path']
        except:
            pass

        # Get the path of the jsymbolic jar on the system
        java_directory = settings.JSYMBOLIC_JAR
        base_name = os.path.basename(music_file)
        music_name, ext = os.path.splitext(base_name)
        value_file_name = music_name + "_jSymbolic_feature_values.xml"
        definition_file_name = music_name + "_jSymbolic_feature_definitions.xml"

        if config_file:
            config_input = ['java', '-jar', 'jSymbolic.jar', '-configrun', config_file, music_file,
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
            raise Exception(stderr)

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
