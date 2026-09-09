"""
Generate LPDAAC manifests for HLS products

Usage: create_manifest [OPTIONS]


Example:
$ create_manifest ./hlsdata hlsmanifest.json hls-global HLSS30
HLS.S30.T01LAH.2020097T222759.v1.5 aeere-33-cssdr false

"""

import hashlib
import json
import os
from datetime import UTC, datetime
from importlib.resources import files as resource_files
from typing import Any
from urllib.parse import urlparse

import click
from jsonschema import validate

PRODUCT_EXTENSIONS: tuple[str, ...] = (".tif", ".jpg", ".xml", "_stac.json")


def _file_type_fields(filename: str, gibs: bool) -> dict[str, str]:
    """Return the CNM type and subtype fields for a product file.

    GIBS deliveries carry browse imagery, so the same extensions are
    typed differently than in a science delivery.
    """
    if filename.endswith(".tif"):
        if gibs:
            return {"type": "browse", "subtype": "geotiff"}
        return {"type": "data"}
    if filename.endswith(".xml"):
        if gibs:
            return {"type": "metadata", "subtype": "ImageMetadata-v1.2"}
        return {"type": "metadata"}
    if filename.endswith(".jpg"):
        return {"type": "browse"}
    if filename.endswith("_stac.json"):
        return {"type": "metadata"}
    return {}


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
    type=click.Choice(["HLSS30", "HLSL30", "HLSS30_VI", "HLSL30_VI", "HLSM30"]),
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
def main(
    inputdir: str,
    outputfile: str,
    bucket: str,
    collection: str,
    product: str,
    jobid: str,
    gibs: bool,
) -> None:
    """
    BUCKET is the target LPDAAC S3 bucket.

    PRODUCT is the root product identifier with no extension.
    """
    manifest = build_manifest(inputdir, bucket, collection, product, jobid, gibs)
    with open(outputfile, "w") as out:
        json.dump(manifest, out)


def build_manifest(
    inputdir: str,
    bucket: str,
    collection: str,
    product: str,
    jobid: str,
    gibs: bool,
) -> dict[str, Any]:
    """Build a validated CNM manifest for the products in inputdir.

    Separated from the command so callers can build a manifest in process
    rather than through the shell.

    Returns the manifest as a dict.

    Raises FileNotFoundError if inputdir holds no product files, since a
    manifest listing nothing would ask the DAAC to ingest an empty granule.
    """
    manifest: dict[str, Any] = {}
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
    manifest["submissionTime"] = datetime.now(UTC).strftime("%Y-%m-%dT%H:%M:%SZ")

    if gibs:
        product_name = product.split("_")[0]
    else:
        product_name = product

    files: list[dict[str, Any]] = []
    for filename in os.listdir(inputdir):
        if filename.endswith(PRODUCT_EXTENSIONS):
            file_item: dict[str, Any] = {}
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
            file_item["uri"] = f"{normal_bucket}/{filename}"
            file_item.update(_file_type_fields(filename, gibs))

            files.append(file_item)

    if not files:
        raise FileNotFoundError(f"no product files ({', '.join(PRODUCT_EXTENSIONS)}) in {inputdir}")

    manifest["product"] = {"name": product_name, "dataVersion": "2.0", "id": product, "files": files}

    schema_resource = resource_files("hls_manifest").joinpath("schema/cumulus_sns_schema_v1.4.1.json")
    with schema_resource.open("rb") as schema_file:
        schema = json.load(schema_file)
    validate(instance=manifest, schema=schema)
    return manifest


if __name__ == "__main__":
    main()
