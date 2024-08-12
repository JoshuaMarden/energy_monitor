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

resource "aws_s3_bucket" "extract" {
  bucket = "c12-energy-tracker"
  force_destroy = true
}

resource "aws_s3_bucket_notification" "trigger" {
  bucket = aws_s3_bucket.extract.id
  eventbridge = true
}

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
        value: tostring(var.AWS_SECRET_KEY)
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
  role_arn  = "arn:aws:iam::129033205317:role/service-role/Amazon_EventBridge_Invoke_ECS_c12-jonathan"
  ecs_target {
    task_definition_arn = aws_ecs_task_definition.energy-pipeline.arn
    launch_type = "FARGATE"

    network_configuration {
      subnets = ["subnet-058f02e41ee6a5439", "subnet-0c459ebb007081668", "subnet-0ff947058bbc1165d"]
      assign_public_ip = true	
                                              
    }
  }
}