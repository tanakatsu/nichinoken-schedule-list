from typing import Optional

import os
import re
from google.api_core.client_options import ClientOptions
from google.cloud import documentai

DEFAULT_PROCESSOR_VERSION = "pretrained-form-parser-v2.0-2022-11-10"


class Ocr:
    def __init__(self, project_id: str,
                 location: str,
                 processor_id: str,
                 processor_version: str = DEFAULT_PROCESSOR_VERSION):
        self.project_id = project_id
        self.location = location
        self.processor_id = processor_id
        self.processor_version = processor_version

    def process_document(self,
                         file_path: str,
                         process_options: Optional[documentai.ProcessOptions] = None,
                         ) -> documentai.Document:
        # You must set the `api_endpoint` if you use a location other than "us".
        client = documentai.DocumentProcessorServiceClient(
            client_options=ClientOptions(
                api_endpoint=f"{location}-documentai.googleapis.com"
            )
        )

        # The full resource name of the processor version, e.g.:
        # `projects/{project_id}/locations/{location}/processors/{processor_id}/processorVersions/{processor_version_id}`
        # You must create a processor before running this sample.
        name = client.processor_version_path(
            self.project_id, self.location, self.processor_id, self.processor_version
        )

        # Read the file into memory
        with open(file_path, "rb") as image:
            image_content = image.read()

        mime_type = self.__guess_mimetype(file_path)

        # Configure the process request
        request = documentai.ProcessRequest(
            name=name,
            raw_document=documentai.RawDocument(content=image_content, mime_type=mime_type),
            # Only supported for Document OCR processor
            process_options=process_options,
        )

        result = client.process_document(request=request)

        # For a full list of `Document` object attributes, reference this page:
        # https://cloud.google.com/document-ai/docs/reference/rest/v1/Document
        return result.document

    def save_response_to_jsonfile(self, response, output_filename):
        json = response.__class__.to_json(response)
        with open(output_filename, 'w') as f:
            f.write(json)

    def __guess_mimetype(self, file_path):
        ext_name = os.path.splitext(file_path)[1]
        if re.match(r'\.[jJ][pP][gG]$', ext_name):
            return "image/jpeg"
        elif re.match(r'\.[jJ][pP][eE][gG]$', ext_name):
            return "image/jpeg"
        elif re.match(r'\.[pP][nN][gG]$', ext_name):
            return "image/png"
        elif re.match(r'\.[pP][dD][fF]$', ext_name):
            return "application/pdf"
        else:
            raise ValueError(f"Cannot guess mime_type: {file_path}")

