import pytest
from marshmallow import ValidationError

from moto import mock_s3
import boto3

from great_expectations.data_context.types.resource_identifiers import validationResultIdentifierSchema, \
    SiteSectionIdentifier, ValidationResultIdentifier, ExpectationSuiteIdentifier
from great_expectations.exceptions import MissingTopLevelConfigKeyError
from great_expectations.util import (
    gen_directory_tree_str,
)
from great_expectations.data_context.store import (
    HtmlSiteStore
)


def test_HtmlSiteStore_filesystem_backend(tmp_path_factory):

    path = str(tmp_path_factory.mktemp('test_HtmlSiteStore_with_TupleFileSystemStoreBackend__dir'))

    my_store = HtmlSiteStore(
        store_backend={
            "class_name": "TupleFilesystemStoreBackend",
            "base_directory": "my_store"
        },
        runtime_environment={
            "root_directory": path
        }
    )

    with pytest.raises(TypeError):
        my_store.get("not_a_ValidationResultIdentifier")

    with pytest.raises(ValidationError):
        my_store.get(validationResultIdentifierSchema.load({}))
    
    ns_1 = SiteSectionIdentifier(
        site_section_name="validations",
        resource_identifier=ValidationResultIdentifier.from_tuple(('a', 'b', 'c', 'quarantine', 'prod-100'))
    )
    my_store.set(ns_1, "aaa")
    # assert my_store.get(ns_1) == "aaa"

    ns_2 = SiteSectionIdentifier(
        site_section_name="validations",
        resource_identifier=ValidationResultIdentifier.from_tuple(('a', 'b', 'c', 'quarantine', 'prod-20'))
    )
    my_store.set(ns_2, "bbb")
    # assert my_store.get(ns_2) == {"B": "bbb"}

    print(my_store.list_keys())
    # WARNING: OBSERVE THAT SITE_SECTION_NAME IS LOST IN THE CALL TO LIST_KEYS
    assert set(my_store.list_keys()) == {
        ns_1.resource_identifier,
        ns_2.resource_identifier,
    }

    print(gen_directory_tree_str(path))
    assert gen_directory_tree_str(path) == """\
test_HtmlSiteStore_with_TupleFileSystemStoreBackend__dir0/
    my_store/
        validations/
            a/
                b/
                    c/
                        quarantine/
                            prod-100.html
                            prod-20.html
"""


@mock_s3
def test_HtmlSiteStore_S3_backend():
    bucket = "test_validation_store_bucket"
    prefix = "test/prefix"

    # create a bucket in Moto's mock AWS environment
    conn = boto3.resource('s3', region_name='us-east-1')
    conn.create_bucket(Bucket=bucket)

    my_store = HtmlSiteStore(
        store_backend={
            "class_name": "TupleS3StoreBackend",
            "bucket": bucket,
            "prefix": prefix
        }
    )

    with pytest.raises(TypeError):
        my_store.get("not_a_ValidationResultIdentifier")

    ns_1 = SiteSectionIdentifier(
        site_section_name="validations",
        resource_identifier=ValidationResultIdentifier(
            expectation_suite_identifier=ExpectationSuiteIdentifier(
                expectation_suite_name="asset.quarantine",
            ),
            run_id="20191007T151224.1234Z_prod_100",
            batch_identifier="1234"
        )
    )
    my_store.set(ns_1, "aaa")

    ns_2 = SiteSectionIdentifier(
        site_section_name="expectations",
        resource_identifier=ExpectationSuiteIdentifier(
            expectation_suite_name="asset.quarantine",
        )
    )
    my_store.set(ns_2, "bbb")

    assert set(my_store.list_keys()) == {
        ns_1.resource_identifier,
        ns_2.resource_identifier,
    }

    # This is a special un-store-like method exposed by the HtmlSiteStore
    my_store.write_index_page("index_html_string_content")

    # Verify that internals are working as expected, including the default filepath
    # paths below should include the batch_parameters
    assert set(
        [s3_object_info['Key'] for s3_object_info in
         boto3.client('s3').list_objects(Bucket=bucket, Prefix=prefix)['Contents']
         ]
    ) == {
        'test/prefix/index.html',
        'test/prefix/expectations/asset/quarantine.html',
        'test/prefix/validations/asset/quarantine/20191007T151224.1234Z_prod_100/1234.html'
    }

    index_content = boto3.client('s3').get_object(Bucket=bucket, Key='test/prefix/index.html')["Body"]\
        .read().decode('utf-8')
    assert index_content == "index_html_string_content"
