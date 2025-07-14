resource "local_file" "inicio" {
    content = "Inicio de terraform: ${timestamp()}"
    filename = "${path.cwd}/generated_environment/inicio.txt"
}

output "ruta_inicio" {
    value = local_file.inicio.filename
}


locals {
    common_app_config = {
        app1 = { version = "1.0", port = 8081}
        app2 = { version = "1.7", port = 8082}
    }
}

module "apps_simuladas" {
    for_each = local.common_app_config

    source = "./terraform/modules/application_service "
    app_name = each.key
    app_version = each.value.version
    app_port = each.value.port
    base_install_path = "${path.cwd}/generated_environment/${each.key}"




}