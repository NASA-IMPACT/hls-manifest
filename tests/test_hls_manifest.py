import os
from click.testing import CliRunner
import pytest

from hls_manifest.hls_manifest import build_manifest, main


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


def test_hls_L30_manifest():
    product = "HLS.L30.T01LAH.2020097T222759.v1.5"
    outputfile = os.path.join(test_dir, product.format(".json"))
    bucket = "s3://hls-global"
    collection = "HLSL30"
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


def test_build_manifest_rejects_an_empty_directory(tmp_path):
    """A manifest listing no files would ask for an empty granule."""
    with pytest.raises(FileNotFoundError, match="no product files"):
        build_manifest(
            str(tmp_path), "s3://hls-global", "HLSM30", "GRAN", "job", False
        )


def test_build_manifest_returns_a_dict():
    manifest = build_manifest(
        test_dir, "s3://hls-global", "HLSS30",
        "HLS.S30.T01LAH.2020097T222759.v1.5", "job", False,
    )
    assert manifest["collection"] == "HLSS30"
    assert manifest["product"]["files"]
