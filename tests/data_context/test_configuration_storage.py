import logging

logger = logging.getLogger(__name__)
import os


def read_config_file_from_disk(config_filepath):
    with open(config_filepath, "r") as infile:
        config_file = infile.read()
        return config_file


def test_preserve_comments_in_yml_after_adding_datasource(data_context):
    config_filepath = os.path.join(
        data_context.root_directory, "great_expectations.yml"
    )
    initial_config = read_config_file_from_disk(config_filepath)
    print("++++++++++++++++ initial config +++++++++++++++++++++++")
    print(initial_config)
    print("----------------------------------------")

    data_context.add_datasource(
        "test_datasource",
        module_name="great_expectations.datasource",
        class_name="PandasDatasource",
        base_directory="../data",
    )

    # TODO The comments on lines 1,2 & 4 of the fixture exposes the bug.
    expected = """# This is a basic configuration for testing.
# It has comments that should be preserved.
ge_config_version: 1
# Here's a comment between the config version and the datassources
datasources:
  # For example, this one.
  mydatasource:
    module_name: great_expectations.datasource
    class_name: PandasDatasource
    data_asset_type:
      class_name: PandasDataset
    generators:
      # The name default is read if no datasource or generator is specified
      mygenerator:
        class_name: SubdirReaderGenerator
        base_directory: ../data
        reader_options:
          sep:
          engine: python


  test_datasource:
    module_name: great_expectations.datasource
    class_name: PandasDatasource
    data_asset_type:
      class_name: PandasDataset
    generators:
      default:
        class_name: SubdirReaderGenerator
        base_directory: ../data
        reader_options:
          sep:
          engine: python
config_variables_file_path: uncommitted/config_variables.yml
expectations_store:
  class_name: ExpectationStore
  store_backend:
    class_name: FixedLengthTupleFilesystemStoreBackend
    base_directory: expectations/

plugins_directory: plugins/
evaluation_parameter_store_name: evaluation_parameter_store
data_docs:
  sites:
stores:
  evaluation_parameter_store:
    module_name: great_expectations.data_context.store
    class_name: EvaluationParameterStore
"""

    print("++++++++++++++++ expected +++++++++++++++++++++++")
    print(expected)
    print("----------------------------------------")

    observed = read_config_file_from_disk(config_filepath)

    print("++++++++++++++++ observed +++++++++++++++++++++++")
    print(observed)
    print("----------------------------------------")

    assert observed == expected
