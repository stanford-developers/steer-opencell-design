import os
import unittest


class TestEnvVariable(unittest.TestCase):
    def test_api_url_is_set(self):
        """Test that API_URL is set for production mode"""
        api_url = os.getenv('API_URL')
        self.assertIsNotNone(api_url, "API_URL must be set for production mode")

    def test_opencell_env_is_production(self):
        """Test that OPENCELL_ENV is not set to 'development' (defaults to production)"""
        env_value = os.getenv('OPENCELL_ENV', 'production')
        self.assertEqual(env_value, 'production',
                        f"OPENCELL_ENV should be 'production' (or unset), but got: {env_value}")


if __name__ == '__main__':
    unittest.main()

