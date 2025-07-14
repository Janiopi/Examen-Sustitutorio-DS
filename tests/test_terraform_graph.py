import os
import pytest
from src.terraform_graph import (
    TerraformComponent, TerraformComposite, TerraformLeaf,
    TerraformDependencyAdapter, ResourceDependencyExtractor,
    ModuleDependencyExtractor, DataDependencyExtractor,
    ProviderDependencyExtractor, represent_hierarchy_with_adapter
)



def test_TerraformComposite():
    # Arrange
    elements = [
        TerraformComponent(name="root", element_type="module", resource_type=None, file_path=None),
        TerraformComponent(name="child1", element_type="resource", resource_type="aws_instance", file_path="/path/to/file.tf"),
        TerraformComponent(name="child2", element_type="resource", resource_type="aws_s3_bucket", file_path="/path/to/another_file.tf")
    ]

    # Act
    composite = TerraformComposite(elements[0], elements[0].element_type, elements[0].resource_type, elements[0].file_path)
    for element in elements[1:]:
        composite.add(element)
    # Assert
 
    assert len(composite.children) == 2
    assert composite.children[0].name == "child1"
    assert composite.children[1].name == "child2"



 








