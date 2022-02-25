import os
import shutil
import tempfile
from pathlib import Path
from typing import Dict

from aws_lambda_powertools.event_handler.exceptions import BadRequestError
from aws_lambda_powertools.logging.correlation_paths import API_GATEWAY_REST
from aws_lambda_powertools import Tracer, Logger
from aws_lambda_powertools.event_handler.api_gateway import (
    APIGatewayRestResolver,
    Response,
    CORSConfig,
)
from cookiecutter.config import DEFAULT_CONFIG
from cookiecutter.main import cookiecutter

TEMPLATE_DIR = os.environ["TEMPLATE_DIR"]
DEFAULT_CONFIG["cookiecutters_dir"] = "/tmp/cookiecutters/"
DEFAULT_CONFIG["replay_dir"] = "/tmp/cookiecutter_replay/"
SUPPORTED_TRIGGERS = ["rest-api", "s3", "s3-object-lambda"]
tracer = Tracer()
logger = Logger()
app = APIGatewayRestResolver(cors=CORSConfig(allow_origin="*"))


@tracer.capture_method()
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
@tracer.capture_method()
def build() -> Response:
    """Standard set of PowerTools cookiecutter templates"""
    trigger = app.current_event.get_query_string_value("trigger") or "rest-api"
    if trigger not in SUPPORTED_TRIGGERS:
        raise BadRequestError(f"Unsupported trigger: {trigger}")
    project_name = app.current_event.get_query_string_value("name") or "hello-world"

    if trigger == "rest-api":
        # Temp solution to support "cookiecutter-aws-sam-python"
        template_name = "cookiecutter-aws-sam-python"
        context = {"project_name": project_name, "include_safe_deployment": "n"}
    else:
        template_name = "cookiecutter-aws-lambda-powertools"
        service_name = app.current_event.get_query_string_value("service_name") or "example"
        runtime = app.current_event.get_query_string_value("runtime") or "python3.9"
        architecture = app.current_event.get_query_string_value("architecture") or "x86_64"
        memory = app.current_event.get_query_string_value("memory") or "512"
        timeout = app.current_event.get_query_string_value("timeout") or "25"
        context = {
            "project_name": project_name,
            "service_name": service_name,
            "runtime": runtime,
            "timeout": timeout,
            "memory": memory,
            "trigger": trigger,
            "architecture": architecture,
        }
    logger.debug(f"Building project {template_name} with template {context}")
    return build_template(template_name=template_name, context=context)


@app.get("/sam-project.zip", cors=True)
@tracer.capture_method()
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


@tracer.capture_lambda_handler()
@logger.inject_lambda_context(correlation_id_path=API_GATEWAY_REST)
def lambda_handler(event, context):
    return app(event, context)
