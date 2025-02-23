provider "aws" {
  region = "us-east-2"
}


resource "aws_s3_bucket" "bucket_flask" {
  bucket = "your-bucket-name/" 

  tags = {
    Name        = "Health App"
    Environment = "Project"
  }

  provisioner "local-exec" {
    command = "${path.module}/upload_to_s3.sh"
  }

  provisioner "local-exec" {
    when    = destroy
    command = "aws s3 rm s3://your-bucket-name/ --recursive"
  }
}

resource "aws_instance" "flask_app" {
  ami           = "ami-0a0d9cf81c479446a"
  instance_type = "t2.micro"

  security_groups = [aws_security_group.app_sg.name]

  iam_instance_profile = aws_iam_instance_profile.ec2_s3_profile.name

  # Initialization script
  user_data = <<-EOF
              #!/bin/bash
              sudo yum update -y
              sudo yum install -y python3 python3-pip awscli
              sudo pip3 install flask joblib numpy gunicorn werkzeug psycopg2-binary pandas
              sudo pip3 install 'requests<2.29.0'

              # Create directory for app
              sudo mkdir -p /app

              # Check if the instance has permission to access S3
              aws sts get-caller-identity >> /home/ec2-user/debug.log 2>&1

              # Sync files from the S3 bucket
              aws s3 sync s3://your-bucket-name/ /app >> /home/ec2-user/debug.log 2>&1

              # Start Flask app with Gunicorn
              cd /app
              nohup gunicorn -w 4 -b 0.0.0.0:5001 wsgi:app &
            EOF

  tags = {
    Name = "FlaskApp"
  }
}

resource "aws_security_group" "app_sg" {
  name        = "flask_app_sg"
  description = "Allow traffic for Flask and PostgreSQL"

  # Allow SSH access
  ingress {
    from_port   = 22
    to_port     = 22
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]  # Restrict to your IP later
  }

  # Allow HTTP access to the Flask app
  ingress {
    from_port   = 5001
    to_port     = 5001
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]  # Restrict as needed
  }

  # Allow the app to access the database on your local IP
  ingress {
    from_port   = 5959
    to_port     = 5959
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/32"]  # Local IP of your PostgreSQL
  }

  egress {
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }
}

resource "aws_iam_role" "ec2_s3_access_role" {
  
  name = "ec2_s3_access_role"

  assume_role_policy = jsonencode({
    Version = "2012-10-17",
    Statement = [
      {
        Action = "sts:AssumeRole",
        Effect = "Allow",
        Principal = {
          Service = "ec2.amazonaws.com"
        }
      },
    ]
  })
}

resource "aws_iam_role_policy" "s3_access_policy" {
  
  name = "s3_access_policy"
  
  role = aws_iam_role.ec2_s3_access_role.id

  policy = jsonencode({
    Version = "2012-10-17",
    Statement = [
      {
        Action = [
          "s3:GetObject",
          "s3:PutObject",
          "s3:ListBucket"
        ],
        Effect = "Allow",
        Resource = [
          "${aws_s3_bucket.bucket_flask.arn}/*",
          "${aws_s3_bucket.bucket_flask.arn}"
        ]
      },
    ]
  })
}

resource "aws_iam_instance_profile" "ec2_s3_profile" {
  name = "ec2_s3_profile"
  role = aws_iam_role.ec2_s3_access_role.name
}
