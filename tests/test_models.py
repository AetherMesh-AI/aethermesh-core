import re
import unittest

from aethermesh_core.models import NodeIdentity


class NodeIdentityTests(unittest.TestCase):
    def test_ephemeral_node_identity_keeps_node_prefix_shape(self) -> None:
        identity = NodeIdentity.ephemeral()

        self.assertRegex(identity.node_id, re.compile(r"^node-[0-9a-f]{32}$"))


if __name__ == "__main__":
    unittest.main()
