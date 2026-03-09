import os
import unittest


class TestEnvVariable(unittest.TestCase):
    def test_opencell_env_is_set(self):
        """Test that OPENCELL_ENV is set to 'development'"""
        env_value = os.getenv('OPENCELL_ENV')
        print(f"OPENCELL_ENV value: {env_value}")
        self.assertEqual(env_value, 'development', 
                        f"OPENCELL_ENV should be 'development', but got: {env_value}")


if __name__ == '__main__':
    unittest.main()

