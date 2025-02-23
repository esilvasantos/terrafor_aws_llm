aws s3 cp ../app s3://your-bucket-name/ --recursive
aws s3 cp ../.env config.py wsgi.py s3://your-bucket-name//
aws s3 cp ../config.py s3://your-bucket-name//
aws s3 cp ../wsgi.py s3://your-bucket-name//