# Quick start for AWS Lambda

## Backend service

- Builds a layer for the different cookiecutter times. This will be limited in size.
- Webservice includes a number of parameters:
  - `name`: defaults to `hello-world`, is the name of the project
  - `runtime`: defaults to python3.9, is the laguage runtime version
  - `memory`: defaults 512, is the memory size of the lambda
  - `timeout`: defaults to 30, is the timeout of the lambda
  - `trigger`: defaults to rest api (S3 also supported), is the type of service calling the lambda function
  - `type`: defaults to `sam` and can support `cdk`, is the IaC type
- Template name structure: `quickstart-<name>-<sam>-<language>`

## UI

```javascript
fetch('https://<FINAL_URL>/project.zip?name=mouse')
  .then(resp => resp.blob())
  .then(blob => {
    const url = window.URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.style.display = 'none';
    a.href = url;
    a.download = 'generated-project.zip';
    document.body.appendChild(a);
    a.click();
    window.URL.revokeObjectURL(url);
  })
  .catch(() => alert('Failed to generate project!'));
```

## TODO

- [X] Initial protoype webservice
- [ ] Add cookiecutter template for rest api (quickstart-rest-api-python)
- [ ] Add cookiecutter template for S3 trigger (quickstart-s3-python)
- [ ] Create basic UI and deploy to S3
