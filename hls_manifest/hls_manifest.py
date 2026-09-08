"""
Generate LPDAAC manifests for HLS products

Usage: create_manifest [OPTIONS]


Example:
$ create_manifest ./hlsdata hlsmanifest.json hls-global HLSS30
HLS.S30.T01LAH.2020097T222759.v1.5 aeere-33-cssdr false

"""
import click
import os
import json
import hashlib
from datetime import datetime, timezone
try:
    from importlib.resources import files as resource_files
except ImportError:  # Python < 3.9
    from importlib_resources import files as resource_files
from jsonschema import validate
from urllib.parse import urlparse


@click.command()
@click.argument(
    "inputdir",
    type=click.Path(dir_okay=True, file_okay=False, writable=True),
)
@click.argument(
    "outputfile",
    type=click.Path(dir_okay=False, file_okay=True, writable=True),
)
@click.argument(
    "bucket",
    type=click.STRING,
)
@click.argument(
    "collection",
    type=click.Choice(
        ["HLSS30", "HLSL30", "HLSS30_VI", "HLSL30_VI", "HLSM30"]
    ),
)
@click.argument(
    "product",
    type=click.STRING,
)
@click.argument(
    "jobid",
    type=click.STRING,
)
@click.argument(
    "gibs",
    type=click.BOOL,
)
def main(inputdir, outputfile, bucket, collection, product, jobid, gibs):
    """
    BUCKET is the target LPDAAC S3 bucket.

    PRODUCT is the root product identifier with no extension.
    """
    manifest = build_manifest(inputdir, bucket, collection, product, jobid, gibs)
    with open(outputfile, 'w') as out:
        json.dump(manifest, out)


def build_manifest(inputdir, bucket, collection, product, jobid, gibs):
    """Build a validated CNM manifest for the products in inputdir.

    Separated from the command so callers can build a manifest in process
    rather than through the shell.

    Returns the manifest as a dict.

    Raises FileNotFoundError if inputdir holds no product files, since a
    manifest listing nothing would ask the DAAC to ingest an empty granule.
    """
    manifest = {}
    if gibs:
        if collection == "HLSS30":
            manifest["collection"] = "HLS_S30_Nadir_BRDF_Adjusted_Reflectance_v2.0_STD"
        if collection == "HLSL30":
            manifest["collection"] = "HLS_L30_Nadir_BRDF_Adjusted_Reflectance_v2.0_STD"
    else:
        manifest["collection"] = collection

    manifest["identifier"] = jobid
    manifest["duplicationid"] = product
    manifest["version"] = "1.4"
    manifest["submissionTime"] = datetime.now(timezone.utc).strftime(
        "%Y-%m-%dT%H:%M:%SZ"
    )

    if gibs:
        product_name = product.split("_")[0]
    else:
        product_name = product

    files = []
    for filename in os.listdir(inputdir):
        if filename.endswith(".tif") or filename.endswith(".jpg") \
                or filename.endswith(".xml") or filename.endswith("_stac.json"):
            file_item = {}
            file_item["name"] = filename
            size = os.path.getsize(os.path.join(inputdir, filename))
            file_item["size"] = size
            with open(os.path.join(inputdir, filename), "rb") as f:
                file_hash = hashlib.sha512()
                while True:
                    chunk = f.read(8192)
                    if not chunk:
                        break
                    file_hash.update(chunk)
            file_item["checksum"] = file_hash.hexdigest()
            file_item["checksumType"] = "SHA512"

            normal_bucket = urlparse(bucket).geturl()
            file_item["uri"] = "%s/%s" % (normal_bucket, filename)
            if gibs:
                if filename.endswith(".tif"):
                    file_item["type"] = "browse"
                    file_item["subtype"] = "geotiff"
                if filename.endswith(".xml"):
                    file_item["type"] = "metadata"
                    file_item["subtype"] = "ImageMetadata-v1.2"
                if filename.endswith(".jpg"):
                    file_item["type"] = "browse"
                if filename.endswith("_stac.json"):
                    file_item["type"] = "metadata"
            else:
                if filename.endswith(".tif"):
                    file_item["type"] = "data"
                if filename.endswith(".xml"):
                    file_item["type"] = "metadata"
                if filename.endswith(".jpg"):
                    file_item["type"] = "browse"
                if filename.endswith("_stac.json"):
                    file_item["type"] = "metadata"

            files.append(file_item)

    if not files:
        raise FileNotFoundError(
            "no product files (.tif, .jpg, .xml, _stac.json) in %s" % inputdir
        )

    manifest["product"] = {
        "name": product_name,
        "dataVersion": "2.0",
        "id": product,
        "files": files
    }

    schema = json.load(
        resource_files("hls_manifest").joinpath(
            "schema/cumulus_sns_schema_v1.4.1.json"
        ).open("rb")
    )
    validate(instance=manifest, schema=schema)
    return manifest


if __name__ == "__main__":
    main()
