variable "db_name" {
  type = string
}

variable "db_user" {
  type = string
}

variable "db_password" {
  type = string
}

# 🔥 Security Group
resource "aws_security_group" "rds_sg" {
  name        = "rds-open-sg"
  description = "Allow PostgreSQL access"

  # 🔥 ДОСТУП ЗЗОВНІ + ВНУТРІ AWS
  ingress {
    description = "PostgreSQL public"
    from_port   = 5432
    to_port     = 5432
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
  }

  # 🔥 ВАЖЛИВО: доступ всередині VPC (Lambda → RDS)
  ingress {
    description = "PostgreSQL internal"
    from_port   = 5432
    to_port     = 5432
    protocol    = "tcp"
    self        = true
  }

  egress {
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }
}

# 🔥 RDS PostgreSQL
resource "aws_db_instance" "main" {
  identifier        = "lab4-db"
  allocated_storage = 20
  engine            = "postgres"
  engine_version    = "15"
  instance_class    = "db.t3.micro"

  db_name  = var.db_name
  username = var.db_user
  password = var.db_password

  publicly_accessible = true
  skip_final_snapshot = true

  # 🔥 ПІДКЛЮЧАЄМО SG
  vpc_security_group_ids = [aws_security_group.rds_sg.id]
}

# Outputs
output "db_endpoint" {
  value = aws_db_instance.main.endpoint
}

output "db_name" {
  value = var.db_name
}

output "db_user" {
  value = var.db_user
}