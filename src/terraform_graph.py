import json
import os
import re
from pathlib import Path

# Recorrer recursivamente terraform, parsear bloques resource, module y data

# Representar la jerarquía mediante un composite  (nodos u hojas)

class TerraformParser:
       
    def __init__(self):
        self.resources = []
        self.modules = []
        self.data_sources = []
        self.locals = []
        self.outputs = []
        self.variables = []
    
    def parse_terraform_file(self, file_path):
        
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Parsear diferentes tipos de bloques
        self._parse_resources(content)
        self._parse_modules(content)
        self._parse_data_sources(content)
        self._parse_locals(content)
        self._parse_outputs(content)
        self._parse_variables(content)
    
    def _parse_resources(self, content):
        pattern = r'resource\s+"([^"]+)"\s+"([^"]+)"\s*\{'
        matches = re.finditer(pattern, content)
        for match in matches:
            resource_type = match.group(1)
            resource_name = match.group(2)
            self.resources.append({
                'type': 'resource',
                'resource_type': resource_type,
                'name': resource_name,
                'full_name': f"{resource_type}.{resource_name}"
            })
    
    def _parse_modules(self, content):
        pattern = r'module\s+"([^"]+)"\s*\{'
        matches = re.finditer(pattern, content)
        for match in matches:
            module_name = match.group(1)
            # Buscar el source del módulo
            module_block = self._extract_block_content(content, match.start())
            source_match = re.search(r'source\s*=\s*"([^"]+)"', module_block)
            source = source_match.group(1) if source_match else None
            
            self.modules.append({
                'type': 'module',
                'name': module_name,
                'source': source,
                'full_name': f"module.{module_name}"
            })
    
    def _parse_data_sources(self, content):
        pattern = r'data\s+"([^"]+)"\s+"([^"]+)"\s*\{'
        matches = re.finditer(pattern, content)
        for match in matches:
            data_type = match.group(1)
            data_name = match.group(2)
            self.data_sources.append({
                'type': 'data',
                'data_type': data_type,
                'name': data_name,
                'full_name': f"data.{data_type}.{data_name}"
            })
    
    def _parse_locals(self, content):
        pattern = r'locals\s*\{'
        matches = re.finditer(pattern, content)
        for match in matches:
            self.locals.append({
                'type': 'locals',
                'name': 'locals',
                'full_name': 'locals'
            })
    
    def _parse_outputs(self, content):
        pattern = r'output\s+"([^"]+)"\s*\{'
        matches = re.finditer(pattern, content)
        for match in matches:
            output_name = match.group(1)
            self.outputs.append({
                'type': 'output',
                'name': output_name,
                'full_name': f"output.{output_name}"
            })
    
    def _parse_variables(self, content):
        pattern = r'variable\s+"([^"]+)"\s*\{'
        matches = re.finditer(pattern, content)
        for match in matches:
            var_name = match.group(1)
            self.variables.append({
                'type': 'variable',
                'name': var_name,
                'full_name': f"var.{var_name}"
            })
    
    def _extract_block_content(self, content, start_pos):
        brace_count = 0
        i = start_pos
        while i < len(content):
            if content[i] == '{':
                brace_count += 1
            elif content[i] == '}':
                brace_count -= 1
                if brace_count == 0:
                    return content[start_pos:i+1]
            i += 1
        return content[start_pos:]
    
    def get_all_elements(self):
        return (self.resources + self.modules + self.data_sources + 
                self.locals + self.outputs + self.variables)


def recursive_terraform_search(terraform_root_path):
    parser = TerraformParser()
    terraform_elements = []
    
    # Recorrer recursivamente el directorio
    for root, dirs, files in os.walk(terraform_root_path):
        for file in files:
            if file.endswith('.tf'):
                file_path = os.path.join(root, file)
                print(f"Parsing: {file_path}")
                
                # Crear un parser para cada archivo
                parser.parse_terraform_file(file_path)
                
                # Agregar información del archivo
                for element in parser.get_all_elements():
                    element['file_path'] = file_path
                    element['file_name'] = file
                    element['directory'] = root
                    terraform_elements.append(element)
    
    return terraform_elements

# Generar grafo
def generate_graph_from_terraform(terraform_data):
    graph = {}
    for resource in terraform_data.get('resources', []):
        resource_type = resource['type']
        resource_name = resource['name']
        graph[resource_name] = []
        for attr, value in resource.get('attributes', {}).items():
            if isinstance(value, list):
                for item in value:
                    graph[resource_name].append(item)
            else:
                graph[resource_name].append(value)
    return graph


# Cargar datos de Terraform desde un archivo JSON
def load_terraform_data(filename):
    with open(filename, 'r') as f:
        terraform_data = json.load(f)
    return terraform_data



# Exportar grafo a formato DOT
def export_graph_to_dot(graph, filename):
    with open(filename, 'w') as f:
        f.write('digraph G {\n')
        for node, neighbors in graph.items():
            for neighbor in neighbors:
                f.write(f'    "{node}" -> "{neighbor}";\n')
        f.write('}\n')

# Exportar grafo a formato JSON
def export_graph_to_json(graph, filename):
    import json
    with open(filename, 'w') as f:
        json.dump(graph, f, indent=4)
   


# Identificar módulos huérfanos
def find_orphan_modules(graph):
    orphan_modules = []
    for node in graph:
        if not graph[node]:  # Si el nodo no tiene vecinos
            orphan_modules.append(node)
    return orphan_modules


# Obtener aristas de un grafo
def get_edges(graph):
    edges = []
    for node, neighbors in graph.items():
        for neighbor in neighbors:
            edges.append((node, neighbor))
    return edges


# Obtener metadata
def get_metadata(graph):
    metadata = {}
    for node in graph:
        metadata[node] = {
            'degree': len(graph[node]),
            'neighbors': graph[node]
        }
    return metadata


# Implementación del patrón Composite para representar la jerarquía de Terraform

# Componente base del árbol, puede ser un nodo o una hoja
class TerraformComponent:
    
    
    def __init__(self, name, element_type, resource_type, file_path=None):
        self.name = name
        self.element_type = element_type
        self.resource_type = resource_type
        self.file_path = file_path
    
    def add(self, component):
        raise NotImplementedError
    
    def remove(self, component):
        raise NotImplementedError
    
    def get_child(self, index):
        raise NotImplementedError
    
    def operation(self):
        raise NotImplementedError
    
    def show_details(self, indent=0):
        raise NotImplementedError


class TerraformComposite(TerraformComponent):
    
    def __init__(self, name, element_type, resource_type, file_path=None):
        super().__init__(name, element_type, resource_type, file_path)
        self.children = []
    
    def add(self, component):
        self.children.append(component)
    
    def remove(self, component):
        if component in self.children:
            self.children.remove(component)
    
    def get_child(self, index):
        if 0 <= index < len(self.children):
            return self.children[index]
        return None
    
    def operation(self):
        results = [self.name]
        for child in self.children:
            results.extend(child.operation())
        return results
    
    def show_details(self, indent=0):
        prefix = "  " * indent
        print(f"{prefix}{self.element_type}: {self.name}")
        if self.file_path:
            print(f"{prefix}   File: {self.file_path}")
        
        for child in self.children:
            child.show_details(indent + 1)
    
    def get_all_children(self):
       
        all_children = []
        for child in self.children:
            all_children.append(child)
            if isinstance(child, TerraformComposite):
                all_children.extend(child.get_all_children())
        return all_children

# Hoja del arbol, representa un componente específico de Terraform
class TerraformLeaf(TerraformComponent):

    def __init__(self, name, element_type, file_path=None, resource_type=None):
        super().__init__(name, element_type, resource_type, file_path)
    
    def add(self, component):
        raise Exception("No se puede añadir una hoja a otra hoja")
    
    def remove(self, component):
        raise Exception("No se puede eliminar de una hoja")
    
    def get_child(self, index):
        raise Exception("Las hojas no tienen hijos")
    
    def operation(self):
        return [f"{self.element_type}.{self.name}"]
    
    def show_details(self, indent=0):
  
        prefix = "  " * indent
      
        type_info = f" ({self.resource_type})" if self.resource_type else ""
        print(f"{prefix} {self.element_type}: {self.name}{type_info}")
        if self.file_path:
            print(f"{prefix}   File: {os.path.basename(self.file_path)}")
    
 
# Implementación del patrón Adapter para unificar la interfaz de acceso a dependencias
# Principio OCP: Abierto para extensión, cerrado para modificación

class DependencyExtractor:
       
    def extract_dependencies(self, element):
        raise NotImplementedError
    
    def get_element_metadata(self, element):
        raise NotImplementedError


class ResourceDependencyExtractor(DependencyExtractor):
    
    
    def extract_dependencies(self, element):
        dependencies = []
        if 'attributes' in element:
            for attr, value in element['attributes'].items():
                if isinstance(value, str):
                    # Buscar referencias a otros recursos: ${resource_type.name}
                    dependencies.extend(self._find_references(value))
                elif isinstance(value, list):
                    for item in value:
                        if isinstance(item, str):
                            dependencies.extend(self._find_references(item))
        return dependencies
    
    def _find_references(self, value):
       
        import re
        references = []
        # Patrones para diferentes tipos de referencias
        patterns = [
            r'\$\{([^}]+)\}',  # ${resource.name} o ${module.name}
            r'data\.([^.]+)\.([^.}\s]+)',  # data.type.name
            r'module\.([^.}\s]+)',  # module.name
            r'var\.([^.}\s]+)',  # var.name
            r'local\.([^.}\s]+)'  # local.name
        ]
        
        for pattern in patterns:
            matches = re.findall(pattern, value)
            references.extend(matches)
        
        return references
    
    def get_element_metadata(self, element):
        return {
            'type': 'resource',
            'resource_type': element.get('resource_type'),
            'name': element['name'],
            'file_path': element.get('file_path'),
            'full_name': element.get('full_name')
        }


class ModuleDependencyExtractor(DependencyExtractor):
   
    
    def extract_dependencies(self, element):
        dependencies = []
        # Los módulos pueden depender de variables y otros recursos
        if 'source' in element:
            # Dependencia del módulo fuente
            dependencies.append(element['source'])
        
        # Aquí se podrían añadir más lógicas para extraer dependencias
        # de las variables del módulo, etc.
        return dependencies
    
    def get_element_metadata(self, element):
        return {
            'type': 'module',
            'name': element['name'],
            'source': element.get('source'),
            'file_path': element.get('file_path'),
            'full_name': element.get('full_name')
        }


class DataDependencyExtractor(DependencyExtractor):
       
    def extract_dependencies(self, element):
        dependencies = []
        # Los data sources pueden depender de otros recursos
        if 'attributes' in element:
            for attr, value in element['attributes'].items():
                if isinstance(value, str):
                    dependencies.extend(self._find_references(value))
        return dependencies
    
    def _find_references(self, value):
        import re
        references = []
        patterns = [
            r'\$\{([^}]+)\}',
            r'module\.([^.}\s]+)',
            r'var\.([^.}\s]+)'
        ]
        
        for pattern in patterns:
            matches = re.findall(pattern, value)
            references.extend(matches)
        
        return references
    
    def get_element_metadata(self, element):
        return {
            'type': 'data',
            'data_type': element.get('data_type'),
            'name': element['name'],
            'file_path': element.get('file_path'),
            'full_name': element.get('full_name')
        }


class OutputDependencyExtractor(DependencyExtractor):
    
    
    def extract_dependencies(self, element):
        dependencies = []
        # Los outputs pueden referenciar recursos, módulos, etc.
        if 'value' in element:
            value = element['value']
            if isinstance(value, str):
                dependencies.extend(self._find_references(value))
        return dependencies
    
    def _find_references(self, value):
        import re
        references = []
        patterns = [
            r'\$\{([^}]+)\}',
            r'data\.([^.]+)\.([^.}\s]+)',
            r'module\.([^.}\s]+)',
            r'local\.([^.}\s]+)'
        ]
        
        for pattern in patterns:
            matches = re.findall(pattern, value)
            references.extend(matches)
        
        return references
    
    def get_element_metadata(self, element):
        return {
            'type': 'output',
            'name': element['name'],
            'file_path': element.get('file_path'),
            'full_name': element.get('full_name')
        }


class VariableDependencyExtractor(DependencyExtractor):
    
    
    def extract_dependencies(self, element):
        # Las variables generalmente no tienen dependencias
        return []
    
    def get_element_metadata(self, element):
        return {
            'type': 'variable',
            'name': element['name'],
            'file_path': element.get('file_path'),
            'full_name': element.get('full_name')
        }


class LocalsDependencyExtractor(DependencyExtractor):
    
    
    def extract_dependencies(self, element):
        dependencies = []
        # Los locals pueden referenciar variables y otros recursos
        if 'value' in element:
            value = element['value']
            if isinstance(value, str):
                dependencies.extend(self._find_references(value))
        return dependencies
    
    def _find_references(self, value):
        import re
        references = []
        patterns = [
            r'\$\{([^}]+)\}',
            r'var\.([^.}\s]+)',
            r'data\.([^.]+)\.([^.}\s]+)'
        ]
        
        for pattern in patterns:
            matches = re.findall(pattern, value)
            references.extend(matches)
        
        return references
    
    def get_element_metadata(self, element):
        return {
            'type': 'locals',
            'name': element['name'],
            'file_path': element.get('file_path'),
            'full_name': element.get('full_name')
        }


class TerraformDependencyAdapter:
    
    
    def __init__(self):
        self.extractors = {
            'resource': ResourceDependencyExtractor(),
            'module': ModuleDependencyExtractor(),
            'data': DataDependencyExtractor(),
            'output': OutputDependencyExtractor(),
            'variable': VariableDependencyExtractor(),
            'locals': LocalsDependencyExtractor()
        }
    
    def register_extractor(self, element_type, extractor):
        
        self.extractors[element_type] = extractor
    
    def get_edges(self, terraform_elements):
        
        edges = []
        
        for element in terraform_elements:
            element_type = element.get('type')
            if element_type in self.extractors:
                extractor = self.extractors[element_type]
                dependencies = extractor.extract_dependencies(element)
                
                source = element.get('full_name', element['name'])
                for dependency in dependencies:
                    edges.append((source, dependency))
        
        return edges
    
    def get_metadata(self, terraform_elements):
       
        metadata = {}
        
        for element in terraform_elements:
            element_type = element.get('type')
            if element_type in self.extractors:
                extractor = self.extractors[element_type]
                element_metadata = extractor.get_element_metadata(element)
                
                # Añadir información de dependencias
                dependencies = extractor.extract_dependencies(element)
                element_metadata['dependencies'] = dependencies
                element_metadata['degree'] = len(dependencies)
                
                key = element.get('full_name', element['name'])
                metadata[key] = element_metadata
        
        return metadata
    
    def build_dependency_graph(self, terraform_elements):
        
        graph = {}
        
        for element in terraform_elements:
            element_type = element.get('type')
            if element_type in self.extractors:
                extractor = self.extractors[element_type]
                dependencies = extractor.extract_dependencies(element)
                
                source = element.get('full_name', element['name'])
                graph[source] = dependencies
        
        return graph


def represent_hierarchy_with_adapter(terraform_elements):
    
    adapter = TerraformDependencyAdapter()
    
    # Crear el nodo raíz
    root = TerraformComposite("terraform_root", "root", None, None)
    
    # Agrupar elementos por archivo
    files_dict = {}
    for element in terraform_elements:
        file_path = element.get('file_path', 'unknown')
        if file_path not in files_dict:
            files_dict[file_path] = []
        files_dict[file_path].append(element)
    
    # Crear la jerarquía
    for file_path, elements in files_dict.items():
        file_name = os.path.basename(file_path) if file_path != 'unknown' else 'unknown'
        file_composite = TerraformComposite(file_name, "file", None, file_path)
        
        for element in elements:
            # Crear hoja para cada elemento
            leaf = TerraformLeaf(
                name=element['name'],
                element_type=element['type'],
                file_path=element.get('file_path'),
                resource_type=element.get('resource_type')
            )
            file_composite.add(leaf)
        
        root.add(file_composite)
    
    return root, adapter

# Ejemplo de uso con OCP - fácil añadir nuevos tipos
class ProviderDependencyExtractor(DependencyExtractor):
   
    
    def extract_dependencies(self, element):
        return []  # Los providers generalmente no tienen dependencias
    
    def get_element_metadata(self, element):
        return {
            'type': 'provider',
            'name': element['name'],
            'file_path': element.get('file_path'),
            'full_name': element.get('full_name')
        }


# Función de demostración del Adapter y OCP
def demonstrate_adapter_pattern(terraform_root_path):

    
    print(" Demostración del Patrón Adapter con OCP \n")
    
    #  Parsear archivos Terraform
    print("Parseando archivos Terraform...")
    terraform_elements = recursive_terraform_search(terraform_root_path)
    print(f"   Encontrados {len(terraform_elements)} elementos\n")
    
    # Crear adapter
    print("Creando Terraform Dependency Adapter...")
    adapter = TerraformDependencyAdapter()
    
    #  Obtener edges usando el adapter
    print("Obteniendo aristas con adapter unificado...")
    edges = adapter.get_edges(terraform_elements)
    print(f"   Encontradas {len(edges)} dependencias:")
    for source, target in edges[:5]:  # Mostrar solo las primeras 5
        print(f"   {source} -> {target}")
    if len(edges) > 5:
        print(f"   ... y {len(edges) - 5} más\n")
    else:
        print()
    
    # Obtener metadata usando el adapter
    print("Obteniendo metadata con adapter unificado...")
    metadata = adapter.get_metadata(terraform_elements)
    print(f"   Metadata para {len(metadata)} elementos:")
    for key, meta in list(metadata.items())[:3]:  # Mostrar solo los primeros 3
        print(f"   {key}: {meta['type']} con {meta['degree']} dependencias")
    if len(metadata) > 3:
        print(f"   ... y {len(metadata) - 3} elementos más\n")
    else:
        print()
    
    #  Demostrar OCP - añadir nuevo tipo sin modificar código existente
    print(" Demostrando OCP - Añadiendo nuevo extractor de Provider...")
    
    # Simulamos un elemento provider
    provider_element = {
        'type': 'provider',
        'name': 'aws',
        'full_name': 'provider.aws',
        'file_path': '/terraform/providers.tf'
    }
    
    # Registrar nuevo extractor (extensión sin modificación)
    adapter.register_extractor('provider', ProviderDependencyExtractor())
    
    # Probar con el nuevo tipo
    test_elements = terraform_elements + [provider_element]
    new_metadata = adapter.get_metadata(test_elements)
    
    if 'provider.aws' in new_metadata:
        print("    Nuevo tipo 'provider' añadido exitosamente!")
        print(f"   Metadata del provider: {new_metadata['provider.aws']}")
    else:
        print("    Error al añadir nuevo tipo")
    
    print("\n6. Construyendo grafo de dependencias...")
    dependency_graph = adapter.build_dependency_graph(terraform_elements)
    print(f"   Grafo construido con {len(dependency_graph)} nodos")
    
    # 7. Crear jerarquía con Composite
    print("\n7. Creando jerarquía con patrón Composite...")
    root, _ = represent_hierarchy_with_adapter(terraform_elements)
    print("   Jerarquía creada:")
    root.show_details()
    
    return adapter, terraform_elements, dependency_graph


# Función para analizar dependencias específicas
def analyze_dependencies(adapter, terraform_elements, element_name):
   
    
    print(f"\nAnálisis de dependencias para: {element_name}")
    
    # Buscar el elemento
    target_element = None
    for element in terraform_elements:
        if element.get('full_name') == element_name or element.get('name') == element_name:
            target_element = element
            break
    
    if not target_element:
        print(f" Elemento '{element_name}' no encontrado")
        return
    
    # Obtener extractor específico
    element_type = target_element.get('type')
    if element_type not in adapter.extractors:
        print(f" No hay extractor para tipo '{element_type}'")
        return
    
    extractor = adapter.extractors[element_type]
    
    # Extraer dependencias
    dependencies = extractor.extract_dependencies(target_element)
    metadata = extractor.get_element_metadata(target_element)
    
    print(f"Tipo: {metadata['type']}")
    print(f"Archivo: {metadata.get('file_path', 'N/A')}")
    print(f"Dependencias ({len(dependencies)}):")
    
    if dependencies:
        for dep in dependencies:
            print(f"  -> {dep}")
    else:
        print("  No tiene dependencias")
    
    return dependencies, metadata


# Función para exportar análisis
def export_dependency_analysis(adapter, terraform_elements, output_dir="./analysis"):
    
    
    import os
    os.makedirs(output_dir, exist_ok=True)
    
    print(f"Exportando análisis a {output_dir}")
    
    # 1. Exportar edges
    edges = adapter.get_edges(terraform_elements)
    edges_file = os.path.join(output_dir, "dependencies_edges.json")
    with open(edges_file, 'w') as f:
        json.dump(edges, f, indent=2)
    print(f" Aristas exportadas a {edges_file}")
    
    # 2. Exportar metadata
    metadata = adapter.get_metadata(terraform_elements)
    metadata_file = os.path.join(output_dir, "elements_metadata.json")
    with open(metadata_file, 'w') as f:
        json.dump(metadata, f, indent=2)
    print(f" Metadata exportada a {metadata_file}")
    
    # 3. Exportar grafo
    dependency_graph = adapter.build_dependency_graph(terraform_elements)
    graph_file = os.path.join(output_dir, "dependency_graph.json")
    with open(graph_file, 'w') as f:
        json.dump(dependency_graph, f, indent=2)
    print(f" Grafo exportado a {graph_file}")
    
    # 4. Exportar en formato DOT para visualización
    dot_file = os.path.join(output_dir, "dependencies.dot")
    export_graph_to_dot(dependency_graph, dot_file)
    print(f" Grafo DOT exportado a {dot_file}")
    
    print(" Análisis completo exportado exitosamente!")


