import os
import shutil
import tempfile
from pathlib import Path
from cookiecutter.config import DEFAULT_CONFIG
from cookiecutter.main import cookiecutter
from aws_lambda_powertools import Tracer, Logger
from aws_lambda_powertools.event_handler.api_gateway import (
    APIGatewayRestResolver,
    Response,
)

tracer = Tracer()
logger = Logger()
app = APIGatewayRestResolver()
template_dir = os.environ["TEMPLATE_DIR"] + "/cookiecutter-aws-sam-python"
# Override the cookiecutter default config to not write to home dir
DEFAULT_CONFIG["cookiecutters_dir"] = "/tmp/cookiecutters/"
DEFAULT_CONFIG["replay_dir"] = "/tmp/cookiecutter_replay/"


@tracer.capture_method(capture_response=False)
def build_project(project_name: str) -> bytes:
    context = {
        "project_name": project_name,
        "include_safe_deployment": "n",
    }

    with tempfile.TemporaryDirectory() as tmp_dir:
        # Execute cookiecutter
        os.chdir(tmp_dir)
        output = cookiecutter(
            template=template_dir,
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
            base_name=project_name, format="zip", root_dir=".", base_dir=project_name
        )
        logger.debug(f"zip file: {zip_file}")
        zip_contents: bytes = Path(zip_file).read_bytes()

        # Clean up
        shutil.rmtree(output)
        os.unlink(zip_file)

        return zip_contents


@app.get("/project.zip")
def build():
    project_name = app.current_event.get_query_string_value("name", "helloWorld")
    zip_contents = build_project(project_name)
    return Response(
        status_code=200,
        content_type="application/zip",
        headers={"Content-Disposition": "attachment; filename=project.zip;"},
        body=zip_contents,
    )


@tracer.capture_lambda_handler(capture_response=False)
@logger.inject_lambda_context(log_event=True)
def lambda_handler(event, context):
    return app(event, context)
