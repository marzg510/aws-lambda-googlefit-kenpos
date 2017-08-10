# aws-lambda-googlefit-kenpos
AWS lambda for KENPOS to set my googlefit step data.

## setup
```
pip install mechanize
pip install --upgrade google-api-python-client
```

## Docker
```
docker build -t googlefit-to-kenpos .
docker run --rm -it -v ${PWD}:/opt/googlefit-to-kenpos googlefit-to-kenpos ./googlefit-to-kenpos.py
```
