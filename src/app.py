import os
import shutil
import tempfile
from pathlib import Path
from typing import Dict

from aws_lambda_powertools.event_handler.exceptions import BadRequestError
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
def build_template(template_name: str, context: Dict[str, str]) -> Response:
    project_name = context["project_name"]
    full_template_dir = os.path.realpath(f"{TEMPLATE_DIR}/{template_name}")
    if TEMPLATE_DIR != os.path.commonpath((TEMPLATE_DIR, full_template_dir)):
        raise BadRequestError(f"Invalid template name: {template_name}")

    with tempfile.TemporaryDirectory() as tmp_dir:
        os.chdir(tmp_dir)
        output = cookiecutter(
            template=full_template_dir,
            checkout=None,
            no_input=True,
            directory=".",
            overwrite_if_exists=False,
            replay=False,
            config_file=None,
            default_config=True,
            extra_context=context,
        )

        zip_file = shutil.make_archive(
            base_name=project_name,
            format="zip",
            root_dir=".",
            base_dir=project_name,
        )
        zip_contents: bytes = Path(zip_file).read_bytes()

        shutil.rmtree(output)
        os.unlink(zip_file)

        return Response(status_code=200, content_type="application/zip", body=zip_contents)


@app.get("/project.zip", cors=True)
def build() -> Response:
    """Standard set of PowerTools cookiecutter templates"""
    project_name = app.current_event.get_query_string_value("name") or "hello-world"
    context = {"project_name": project_name, "include_safe_deployment": "n"}
    return build_template(template_name="cookiecutter-aws-sam-python", context=context)


@app.get("/sam-project.zip", cors=True)
def sam_build() -> Response:
    """Builds aws-sam-cli-app-templates based projects"""
    project_name = app.current_event.get_query_string_value("name") or "hello-world"
    runtime = app.current_event.get_query_string_value("runtime")
    architecture = app.current_event.get_query_string_value("architecture")
    template_name = app.current_event.get_query_string_value("template")
    if None in (runtime, architecture, template_name):
        raise BadRequestError("Missing a required parameter")
    context = {
        "project_name": project_name,
        "runtime": runtime,
        "architectures": {"value": [architecture]},
    }
    return build_template(template_name=template_name, context=context)


@tracer.capture_lambda_handler(capture_response=False)
@logger.inject_lambda_context(log_event=True)
def lambda_handler(event, context):
    return app(event, context)
