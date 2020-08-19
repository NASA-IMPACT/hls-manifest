import os
from click.testing import CliRunner
from hls_manifest.hls_manifest import main


current_dir = os.path.dirname(__file__)
test_dir = os.path.join(current_dir, "data")


def test_hls_manifest():
    product = "HLS.S30.T01LAH.2020097T222759.v1.5"
    outputfile = os.path.join(test_dir, product.format(".json"))
    bucket = "s3://hls-global"
    collection = "HLSS30"
    jobid = "test"
    gibs = "false"
    runner = CliRunner(echo_stdin=True)
    result = runner.invoke(main, [
        test_dir,
        outputfile,
        bucket,
        collection,
        product,
        jobid,
        gibs
    ], catch_exceptions=False)
    assert result.exit_code == 0


def test_hls_gibs_manifest():
    product = "HLS.S30.2020116.099152_6"
    outputfile = os.path.join(test_dir, product.format(".json"))
    bucket = "s3://hls-global"
    collection = "HLSS30"
    jobid = "test"
    gibs = "true"
    runner = CliRunner(echo_stdin=True)
    result = runner.invoke(main, [
        test_dir,
        outputfile,
        bucket,
        collection,
        product,
        jobid,
        gibs
    ], catch_exceptions=False)
    assert result.exit_code == 0
