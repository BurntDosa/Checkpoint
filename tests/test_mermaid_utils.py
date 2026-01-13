import os
import unittest
import shutil
import tempfile
from src.mermaid_utils import generate_file_dependency_mermaid, generate_class_hierarchy_mermaid

class TestMermaidUtils(unittest.TestCase):
    def setUp(self):
        self.test_dir = tempfile.mkdtemp()
        
        # Create a dummy file structure
        # main.py imports utils
        # utils.py defines methods
        # base.py defines Base class
        # child.py defines Child class inheriting Base
        
        with open(os.path.join(self.test_dir, "main.py"), "w") as f:
            f.write("import utils\nfrom base import Base\n")
            
        with open(os.path.join(self.test_dir, "utils.py"), "w") as f:
            f.write("def helper(): pass\n")

        with open(os.path.join(self.test_dir, "base.py"), "w") as f:
            f.write("class Base:\n    pass\n")

        with open(os.path.join(self.test_dir, "child.py"), "w") as f:
            f.write("from base import Base\n\nclass Child(Base):\n    pass\n")

    def tearDown(self):
        shutil.rmtree(self.test_dir)

    def test_dependency_graph(self):
        mermaid = generate_file_dependency_mermaid(self.test_dir)
        print("Dependency Mermaid:\n", mermaid)
        self.assertIn("main --> utils", mermaid)
        self.assertIn("main --> base", mermaid) # from base import Base imports 'base' module implicitly
        self.assertIn("child --> base", mermaid)
        self.assertIn("graph TD", mermaid)

    def test_class_hierarchy(self):
        mermaid = generate_class_hierarchy_mermaid(self.test_dir)
        print("Class Mermaid:\n", mermaid)
        self.assertIn("Base <|-- Child", mermaid)
        self.assertIn("classDiagram", mermaid)

if __name__ == "__main__":
    unittest.main()
