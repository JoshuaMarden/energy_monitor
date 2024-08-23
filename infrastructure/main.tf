terraform {
  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.55.0"
    }
  }
  required_version = ">= 1.2.0"
}
provider "aws" {
  region  = var.AWS_REGION
}

# Lambda role to allow interactions
resource "aws_iam_role" "lambda" {
  name = "c12-energy-tracker-lambda-role"
  assume_role_policy = jsonencode({
    Statement = [{
      Action = "sts:AssumeRole"
      Effect = "Allow"
      Principal = {
        Service = "lambda.amazonaws.com"
      }
    }]
    Version = "2012-10-17"
  })
  managed_policy_arns = ["arn:aws:iam::aws:policy/AWSLambda_FullAccess", "arn:aws:iam::aws:policy/service-role/AWSLambdaBasicExecutionRole",  "arn:aws:iam::aws:policy/AmazonS3FullAccess"]
  max_session_duration = 3600
  path                  = "/"
}

# S3 bucket
resource "aws_s3_bucket" "extract" {
  bucket = "c12-energy-tracker"
  force_destroy = true
}
resource "aws_s3_bucket_notification" "trigger" {
  bucket = aws_s3_bucket.extract.id
  eventbridge = true
}

# ECS task definition and trigger
resource "aws_cloudwatch_event_rule" "to_tl" {
  name        = "c12-energy_consumption"
  force_destroy = true

  event_pattern = jsonencode({
    "source"      = ["aws.s3"],
    "detail-type" = ["Object Created"]
    "detail": {
      "bucket": {
      "name": [aws_s3_bucket.extract.id]
      },
      "object": {
      "key": [{
        "prefix": "raw_piechart"
      }]}
      
    }
  })
}
resource "aws_ecs_task_definition" "energy-pipeline" {
  family = "c12-energy-pipeline"
  cpu = 1024
  memory = 6144
  execution_role_arn = "arn:aws:iam::129033205317:role/ecsTaskExecutionRole"
  task_role_arn = "arn:aws:iam::129033205317:role/ecsTaskExecutionRole"
  requires_compatibilities = ["FARGATE"]
  network_mode = "awsvpc"
  runtime_platform {
    operating_system_family = "LINUX"
    cpu_architecture        = "X86_64"
  }
  container_definitions = jsonencode([
  {
    name: "c12-energy-tracker"
    image: "129033205317.dkr.ecr.eu-west-2.amazonaws.com/c12-energy-pipeline:latest"
    cpu: 0
    portMappings: [
    ]
    essential: true
    environment: [
      {name: "SECRET_KEY"
        value: tostring(var.AWS_SECRET_KEY)
      },
      {   name: "ACCESS_KEY"
        value: tostring(var.AWS_ACCESS_KEY)
      },
      {name: "DB_HOST"
        value: tostring(var.DB_HOST)
      },
      {   name: "DB_PORT"
        value: tostring(var.DB_PORT)
      },
      {name: "DB_PASSWORD"
        value: tostring(var.DB_PASSWORD)
      },
      {   name: "DB_USER"
        value: tostring(var.DB_USER)
      },
      {name: "DB_NAME"
        value: tostring(var.DB_NAME)
      }
    ]
    logConfiguration: {
      logDriver: "awslogs"
      options: {
        awslogs-group: "/ecs/c12-energy-tracker"
        awslogs-create-group: "true"
        awslogs-region: "eu-west-2"
        awslogs-stream-prefix: "ecs"
      }
    }
  }])
}
resource "aws_cloudwatch_event_target" "trigger-pipeline" {
  rule = aws_cloudwatch_event_rule.to_tl.name
  arn = "arn:aws:ecs:eu-west-2:129033205317:cluster/c12-ecs-cluster"
  force_destroy = true
  role_arn  = "arn:aws:iam::129033205317:role/service-role/Amazon_EventBridge_Invoke_ECS_314452386"
  ecs_target {
    task_definition_arn = aws_ecs_task_definition.energy-pipeline.arn
    launch_type = "FARGATE"

    network_configuration {
      subnets = ["subnet-058f02e41ee6a5439", "subnet-0c459ebb007081668", "subnet-0ff947058bbc1165d"]
      assign_public_ip = true	                            
    }
  }
}

# Lambda running production extract
resource "aws_lambda_function" "extract_production" {
  architectures                      = ["x86_64"]
  function_name                      = "c12-energy-extract-production"
  image_uri                          = "129033205317.dkr.ecr.eu-west-2.amazonaws.com/c12-energy-extract:latest"
  package_type                       = "Image"
  role                               = aws_iam_role.lambda.arn
  environment {
    variables = {
      ACCESS_KEY_ID = var.AWS_ACCESS_KEY
      SECRET_ACCESS_KEY = var.AWS_SECRET_KEY
    }
  }
  logging_config {
    log_format            = "Text"
    log_group             = "/aws/lambda/c12-energy-production"
  }
}
resource "aws_iam_role" "extract_production" {
  name = "c12-energy-extract-production"
  assume_role_policy = jsonencode({
    Statement = [{
      Action = "sts:AssumeRole"
      Condition = {
        StringEquals = {
          "aws:SourceAccount" = "129033205317"
        }
      }
      Effect = "Allow"
      Principal = {
        Service = "scheduler.amazonaws.com"
      }
    }]
    Version = "2012-10-17"
  })
  managed_policy_arns   = ["arn:aws:iam::129033205317:policy/service-role/Amazon-EventBridge-Scheduler-Execution-Policy-9ddb4bfa-cc6b-405a-9275-03df4997c2e8"]
  max_session_duration  = 3600
  path                  = "/service-role/"
}
resource "aws_scheduler_schedule" "lambda_schedule_30_min" {
  group_name                   = "default"
  name                         = "c12-energy-extract-production"
  schedule_expression          = "cron(*/30 * * * ? *)"
  schedule_expression_timezone = "UTC"
  state                        = "ENABLED"
  flexible_time_window {
    maximum_window_in_minutes = 15
    mode                      = "FLEXIBLE"
  }
  target {
    arn      = aws_lambda_function.extract_production.arn
    role_arn = aws_iam_role.extract_production.arn
    retry_policy {
      maximum_event_age_in_seconds = 86400
      maximum_retry_attempts       = 185
    }
  }
}

# Lambda running carbon extract
resource "aws_lambda_function" "extract_carbon" {
  architectures                      = ["x86_64"]
  function_name                      = "c12-energy-extract-carbon"
  image_uri                          = "129033205317.dkr.ecr.eu-west-2.amazonaws.com/c12-energy-extract-carbon:latest"
  package_type                       = "Image"
  role                               = aws_iam_role.lambda.arn
  environment {
    variables = {
      ACCESS_KEY_ID = var.AWS_ACCESS_KEY
      SECRET_ACCESS_KEY = var.AWS_SECRET_KEY
    }
  }
  logging_config {
    log_format            = "Text"
    log_group             = "/aws/lambda/c12-energy-carbon"
  }
}
resource "aws_iam_role" "extract_carbon" {
  name = "c12-energy-extract-carbon"
  assume_role_policy = jsonencode({
    Statement = [{
      Action = "sts:AssumeRole"
      Condition = {
        StringEquals = {
          "aws:SourceAccount" = "129033205317"
        }
      }
      Effect = "Allow"
      Principal = {
        Service = "scheduler.amazonaws.com"
      }
    }]
    Version = "2012-10-17"
  })
  managed_policy_arns   = ["arn:aws:iam::129033205317:policy/service-role/Amazon-EventBridge-Scheduler-Execution-Policy-9ddb4bfa-cc6b-405a-9275-03df4997c2e8"]
  max_session_duration  = 3600
  path                  = "/service-role/"
}
resource "aws_scheduler_schedule" "lambda_schedule_1_day" {
  group_name                   = "default"
  name                         = "c12-energy-extract-carbon"
  schedule_expression          = "cron(0 0 * * ? *)"
  schedule_expression_timezone = "UTC"
  state                        = "ENABLED"
  flexible_time_window {
    maximum_window_in_minutes = 15
    mode                      = "FLEXIBLE"
  }
  target {
    arn      = aws_lambda_function.extract_carbon.arn
    role_arn = aws_iam_role.extract_carbon.arn
    retry_policy {
      maximum_event_age_in_seconds = 86400
      maximum_retry_attempts       = 185
    }
  }
}

# Dashboard service 
resource "aws_security_group" "dashboard_sg" {
  name        = "c12-energy-dashboard"
  description = "Allow inbound psql traffic"
  vpc_id      = "vpc-061c17c21b97427d8"
}
resource "aws_vpc_security_group_ingress_rule" "ipv4_sl_db_in" {
  security_group_id = aws_security_group.dashboard_sg.id
  cidr_ipv4         = "0.0.0.0/0"
  from_port         = 8501
  ip_protocol       = "tcp"
  to_port           = 8501
}
resource "aws_vpc_security_group_ingress_rule" "ipv4_rds_dbn" {
  security_group_id = aws_security_group.dashboard_sg.id
  cidr_ipv4         = "0.0.0.0/0"
  from_port         = 5432
  ip_protocol       = "tcp"
  to_port           = 5432
}
resource "aws_vpc_security_group_egress_rule" "ipv4_all__db_out" {
  security_group_id = aws_security_group.dashboard_sg.id
  cidr_ipv4         = "0.0.0.0/0"
  ip_protocol       = "-1"
}

resource "aws_ecs_task_definition" "energy-dashboard" {
  family = "c12-energy-dashboard"
  cpu = 1024
  memory = 6144
  execution_role_arn = "arn:aws:iam::129033205317:role/ecsTaskExecutionRole"
  task_role_arn = "arn:aws:iam::129033205317:role/ecsTaskExecutionRole"
  requires_compatibilities = ["FARGATE"]
  network_mode = "awsvpc"
  runtime_platform {
    operating_system_family = "LINUX"
    cpu_architecture        = "X86_64"
  }
  container_definitions = jsonencode([
  {
    name: "c12-energy-dashboard"
    image: "129033205317.dkr.ecr.eu-west-2.amazonaws.com/c12-energy-dashboard:latest"
    cpu: 0
    portMappings: [
    ]
    essential: true
    environment: [
      {name: "SECRET_KEY"
        value: tostring(var.AWS_SECRET_KEY)
      },
      {   name: "ACCESS_KEY"
        value: tostring(var.AWS_SECRET_KEY)
      },
      {name: "DB_HOST"
        value: tostring(var.DB_HOST)
      },
      {   name: "DB_PORT"
        value: tostring(var.DB_PORT)
      },
      {name: "DB_PASSWORD"
        value: tostring(var.DB_PASSWORD)
      },
      {   name: "DB_USER"
        value: tostring(var.DB_USER)
      },
      {name: "DB_NAME"
        value: tostring(var.DB_NAME)
      }
    ]
    logConfiguration: {
      logDriver: "awslogs"
      options: {
        awslogs-group: "/ecs/c12-energy-dashboard"
        awslogs-create-group: "true"
        awslogs-region: "eu-west-2"
        awslogs-stream-prefix: "ecs"
      }
    }
  }])
}
resource "aws_ecs_service" "dashboard" {
    name                    = "c12-energy-dashboard"
    cluster                 = "arn:aws:ecs:eu-west-2:129033205317:cluster/c12-ecs-cluster"
    desired_count           = 1
    task_definition         = aws_ecs_task_definition.energy-dashboard.arn
    capacity_provider_strategy {
      capacity_provider = "FARGATE"
      base = 1
      weight = 100

    }
    
    network_configuration {
        security_groups = [aws_security_group.dashboard_sg.id]
        subnets         = ["subnet-058f02e41ee6a5439", "subnet-0c459ebb007081668", "subnet-0ff947058bbc1165d"]
        assign_public_ip = true
  }
}

# Lambda running email service
resource "aws_lambda_function" "email_service" {
  architectures                      = ["x86_64"]
  function_name                      = "c12-energy-email-service"
  image_uri                          = "129033205317.dkr.ecr.eu-west-2.amazonaws.com/c12-energy-email-service:latest"
  package_type                       = "Image"
  role                               = aws_iam_role.lambda.arn
  environment {
    variables = {
      ACCESS_KEY_ID = var.AWS_ACCESS_KEY
      SECRET_ACCESS_KEY = var.AWS_SECRET_KEY
    }
  }
  logging_config {
    log_format            = "Text"
    log_group             = "/aws/lambda/c12-energy-email-service"
  }
}
resource "aws_iam_role" "email_service" {
  name = "c12-energy-email-service"
  assume_role_policy = jsonencode({
    Statement = [{
      Action = "sts:AssumeRole"
      Condition = {
        StringEquals = {
          "aws:SourceAccount" = "129033205317"
        }
      }
      Effect = "Allow"
      Principal = {
        Service = "scheduler.amazonaws.com"
      }
    }]
    Version = "2012-10-17"
  })
  managed_policy_arns   = ["arn:aws:iam::129033205317:policy/service-role/Amazon-EventBridge-Scheduler-Execution-Policy-9ddb4bfa-cc6b-405a-9275-03df4997c2e8"]
  max_session_duration  = 3600
  path                  = "/service-role/"
}
resource "aws_scheduler_schedule" "lambda_schedule_1_day_1" {
  group_name                   = "default"
  name                         = "c12-energy-email_service"
  schedule_expression          = "cron(0 6 * * ? *)"
  schedule_expression_timezone = "UTC"
  state                        = "ENABLED"
  flexible_time_window {
    maximum_window_in_minutes = 15
    mode                      = "FLEXIBLE"
  }
  target {
    arn      = aws_lambda_function.email_service.arn
    role_arn = aws_iam_role.email_service.arn
    retry_policy {
      maximum_event_age_in_seconds = 86400
      maximum_retry_attempts       = 185
    }
  }
}

# Lambda running email service
resource "aws_lambda_function" "webhook" {
  architectures                      = ["x86_64"]
  function_name                      = "c12-energy-webhooks"
  image_uri                          = "129033205317.dkr.ecr.eu-west-2.amazonaws.com/c12-energy-webhooks:latest"
  package_type                       = "Image"
  role                               = aws_iam_role.lambda.arn
  environment {
    variables = {
      ACCESS_KEY_ID = var.AWS_ACCESS_KEY
      SECRET_ACCESS_KEY = var.AWS_SECRET_KEY
    }
  }
  logging_config {
    log_format            = "Text"
    log_group             = "/aws/lambda/c12-energy-webhooks"
  }
}
resource "aws_iam_role" "webhook" {
  name = "c12-energy-webhook"
  assume_role_policy = jsonencode({
    Statement = [{
      Action = "sts:AssumeRole"
      Condition = {
        StringEquals = {
          "aws:SourceAccount" = "129033205317"
        }
      }
      Effect = "Allow"
      Principal = {
        Service = "scheduler.amazonaws.com"
      }
    }]
    Version = "2012-10-17"
  })
  managed_policy_arns   = ["arn:aws:iam::129033205317:policy/service-role/Amazon-EventBridge-Scheduler-Execution-Policy-9ddb4bfa-cc6b-405a-9275-03df4997c2e8"]
  max_session_duration  = 3600
  path                  = "/service-role/"
}
resource "aws_scheduler_schedule" "lambda_schedule_1_hour_1" {
  group_name                   = "default"
  name                         = "c12-energy-webhooks"
  schedule_expression          = "cron(0 */1 * * ? *)"
  schedule_expression_timezone = "UTC"
  state                        = "ENABLED"
  flexible_time_window {
    maximum_window_in_minutes = 15
    mode                      = "FLEXIBLE"
  }
  target {
    arn      = aws_lambda_function.webhook.arn
    role_arn = aws_iam_role.webhook.arn
    retry_policy {
      maximum_event_age_in_seconds = 86400
      maximum_retry_attempts       = 185
    }
  }
}