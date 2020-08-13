"""
Generate LPDAAC manifests for HLS products

Usage: create_manifest [OPTIONS]

  Translate a file to a COG.


Example:
$ create_manifest ./hlsdata hlsmanifest.json hls-global HLSS30
HLS.S30.T01LAH.2020097T222759.v1.5 aeere-33-cssdr

"""
import click
import os
import json
import hashlib
from datetime import datetime
from pkg_resources import resource_stream
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
    type=click.Choice(["HLSS30", "HLSL30"]),
)
@click.argument(
    "product",
    type=click.STRING,
)
@click.argument(
    "jobid",
    type=click.STRING,
)
def main(inputdir, outputfile, bucket, collection, product, jobid):
    """
    BUCKET is the target LPDAAC S3 bucket.

    PRODUCT is the root product identifier with no extension.
    """
    manifest = {}
    manifest["collection"] = collection
    manifest["identifier"] = jobid
    manifest["version"] = "1.4"
    manifest["submissionTime"] = datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%S")
    files = []
    for filename in os.listdir(inputdir):
        if filename.endswith(".tif") or filename.endswith(".jpg") or filename.endswith(".xml"):
            file_item = {}
            file_item["name"] = filename
            file_item["dataVersion"] = "1.5"
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
            file_item["checksumType"] = "SHA-512"

            normal_bucket = urlparse(bucket).geturl()
            file_item["uri"] = "%s/%s" % (normal_bucket, filename)

            if filename.endswith(".tif"):
                file_item["type"] = "data"
            if filename.endswith(".xml"):
                file_item["type"] = "metadata"
            if filename.endswith(".jpg"):
                file_item["type"] = "browse"

            files.append(file_item)
            continue
        else:
            continue

    manifest["product"] = {
        "name": product,
        "filegroups": [
            {
                "id": product,
                "files": files
            }
        ]
    }

    schema = json.load(
        resource_stream("hls_manifest", "schema/cnm.json")
    )

    validate(instance=manifest, schema=schema)
    with open(outputfile, 'w') as out:
        json.dump(manifest, out)

if __name__ == "__main__":
    main()
