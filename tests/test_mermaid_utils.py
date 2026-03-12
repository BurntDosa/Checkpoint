import os
import unittest
import shutil
import tempfile
from checkpoint_agent.mermaid_utils import generate_all_mermaid_diagrams

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
        dep_mermaid, _ = generate_all_mermaid_diagrams(self.test_dir)
        print("Dependency Mermaid:\n", dep_mermaid)
        self.assertIn("main --> utils", dep_mermaid)
        self.assertIn("main --> base", dep_mermaid)
        self.assertIn("child --> base", dep_mermaid)
        self.assertIn("graph TD", dep_mermaid)

    def test_class_hierarchy(self):
        _, class_mermaid = generate_all_mermaid_diagrams(self.test_dir)
        print("Class Mermaid:\n", class_mermaid)
        self.assertIn("Base <|-- Child", class_mermaid)
        self.assertIn("classDiagram", class_mermaid)

if __name__ == "__main__":
    unittest.main()
