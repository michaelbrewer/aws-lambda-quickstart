import os
import shutil
import tempfile
from pathlib import Path
from typing import Dict
from cookiecutter.config import DEFAULT_CONFIG
from cookiecutter.main import cookiecutter
from aws_lambda_powertools import Tracer, Logger
from aws_lambda_powertools.event_handler.api_gateway import (
    APIGatewayRestResolver,
    Response,
    CORSConfig,
)

TEMPLATE_DIR = os.environ["TEMPLATE_DIR"]
DEFAULT_CONFIG["cookiecutters_dir"] = "/tmp/cookiecutters/"
DEFAULT_CONFIG["replay_dir"] = "/tmp/cookiecutter_replay/"
tracer = Tracer()
logger = Logger()
app = APIGatewayRestResolver(cors=CORSConfig(allow_origin="*"))


@tracer.capture_method(capture_response=False)
def build_project(template_name: str, context: Dict[str, str]) -> bytes:
    with tempfile.TemporaryDirectory() as tmp_dir:
        # Execute cookiecutter
        os.chdir(tmp_dir)
        output = cookiecutter(
            template=TEMPLATE_DIR + "/" + template_name,
            checkout=None,
            no_input=True,
            directory=".",
            overwrite_if_exists=False,
            replay=False,
            config_file=None,
            default_config=True,
            extra_context=context,
        )
        logger.debug(f"output file: {output}")

        # Make zip for downloading
        zip_file = shutil.make_archive(
            base_name=context["project_name"],
            format="zip",
            root_dir=".",
            base_dir=context["project_name"],
        )
        logger.debug(f"zip file: {zip_file}")
        zip_contents: bytes = Path(zip_file).read_bytes()

        # Clean up
        shutil.rmtree(output)
        os.unlink(zip_file)

        return zip_contents


@app.get("/project.zip", cors=True)
def build() -> Response:
    """Standard set of PowertTools cookiecutter templates"""
    project_name = app.current_event.get_query_string_value("name", "helloWorld")
    context = {
        "project_name": project_name,
        "include_safe_deployment": "n",
    }
    zip_contents = build_project(template_name="cookiecutter-aws-sam-python", context=context)
    return Response(status_code=200, content_type="application/zip", body=zip_contents)


@app.get("/sam-project.zip", cors=True)
def sam_build() -> Response:
    """Builds aws-sam-cli-app-templates based projects"""
    project_name = app.current_event.get_query_string_value("name") or "helloWorld"
    runtime = app.current_event.get_query_string_value("runtime")
    architecture = app.current_event.get_query_string_value("architecture") or "x86_64"
    template_name = (
        app.current_event.get_query_string_value("template")
        or "aws-sam-cli-app-templates/python3.9/cookiecutter-aws-sam-hello-python"
    )
    context = {
        "project_name": project_name,
        "runtime": runtime,
        "architectures": {"value": [architecture]},
    }
    zip_contents = build_project(template_name=template_name, context=context)
    return Response(status_code=200, content_type="application/zip", body=zip_contents)


@tracer.capture_lambda_handler(capture_response=False)
@logger.inject_lambda_context(log_event=True)
def lambda_handler(event, context):
    return app(event, context)
