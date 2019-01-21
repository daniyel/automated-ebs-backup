# Cloud Formation template for automating the EBS volume backup

Cloud Formation template for automating the EBS volume backup

## Getting Started

You need to zip the lambda function code within `lambda` folder and upload it to the S3 bucket<sup>*</sup>. On OSX you can do it with `zip automated_backup_handler.zip automated_backup_handler.py`.

(*) Same bucket name will be used for `S3BucketLambda` parameter for cloud formation template.

After uploading the zip file, login in to AWS Web Console, go to CloudFormation section and create new stack. Fill up the parameters accordingly.
