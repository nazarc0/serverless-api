provider "aws" {
  region = "eu-central-1"
}

locals {
  prefix = "lomachynskyi-nazar-10"
}

# RDS
module "database" {
  source      = "../../modules/rds"
  db_name     = "labdb"
  db_user     = "postgres"
  db_password = "Password123!"
}

# Lambda
module "backend" {
  source        = "../../modules/lambda"
  function_name = "${local.prefix}-api"
  source_file   = "${path.root}/../../src/app.py"

  db_host     = module.database.db_endpoint
  db_name     = module.database.db_name
  db_user     = module.database.db_user
  db_password = "Password123!"
}

# API Gateway
module "api" {
  source                 = "../../modules/api_gateway"
  api_name               = "${local.prefix}-api"
  lambda_invoke_arn      = module.backend.invoke_arn
  lambda_function_name   = module.backend.function_name
}

output "api_url" {
  value = module.api.api_endpoint
}