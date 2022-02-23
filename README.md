# Quick start for AWS Lambda

Create a mini [Spring initializer](https://start.spring.io/) for AWS Lambda functions.

## Backend service

- Builds a layer for the different cookiecutter templates. (NOTE: This will be limited for what we can bundle)
- Webservice includes a number of parameters:
  - `name`: defaults to `hello-world`, is the name of the project
  - `runtime`: defaults to python3.9, is the laguage runtime version (could also support typescript via nodejs)
  - `memory`: defaults 512, is the memory size of the lambda
  - `timeout`: defaults to 30, is the timeout of the lambda
  - `trigger`: defaults to `rest-api`, is the type of service calling the lambda function (could also support `s3`)
  - `type`: defaults to `sam`, is the IaC type (could also support `cdk`)
- Template repo name structure: `quickstart-<name>-<type>-<language>`

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
- [X] Create basic UI and deploy via github pages
- [ ] Build out a better UI mock using figma
- [ ] Add stricter cors policy
- [ ] Add cookiecutter template for rest api (`quickstart-rest-api-sam-python`)
- [ ] BONUS: Add cookiecutter template for S3 trigger (`quickstart-s3-sam-python`)
- [ ] BONUS: Add CDK templates
