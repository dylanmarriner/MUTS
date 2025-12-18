"""Tests for services dealer_service module."""
import unittest
import sys
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock

# Import using full path to avoid queue module conflict
sys.path.insert(0, str(Path(__file__).parent.parent))
from muts.services.dealer_service import MazdaDealerSecurity


class TestMazdaDealerSecurity(unittest.TestCase):
    """Test MazdaDealerSecurity class."""
    
    def setUp(self):
        """Set up test fixtures."""
        with patch('dealer_service.MazdaSeedKeyDatabase'):
            self.dealer = MazdaDealerSecurity()
    
    def test_initialization(self):
        """Test MazdaDealerSecurity initialization."""
        self.assertIsNotNone(self.dealer.dealer_codes)
        self.assertIsNotNone(self.dealer.security_levels)
        self.assertIsNotNone(self.dealer.diagnostic_procedures)
        self.assertEqual(self.dealer.current_security_level, 'user')
        self.assertFalse(self.dealer.session_active)
    
    def test_initialize_dealer_codes(self):
        """Test _initialize_dealer_codes method."""
        codes = self.dealer._initialize_dealer_codes()
        
        self.assertIsInstance(codes, dict)
        self.assertIn('manufacturer_mode', codes)
        self.assertIn('dealer_override', codes)
        self.assertIn('engineering_mode', codes)
    
    def test_initialize_security_levels(self):
        """Test _initialize_security_levels method."""
        levels = self.dealer._initialize_security_levels()
        
        self.assertIsInstance(levels, dict)
        self.assertIn('user', levels)
        self.assertIn('dealer', levels)
        self.assertIn('manufacturer', levels)
        self.assertIn('engineering', levels)
        
        # Check level hierarchy
        self.assertLess(levels['user']['level'], levels['dealer']['level'])
        self.assertLess(levels['dealer']['level'], levels['manufacturer']['level'])
    
    def test_initialize_diagnostic_procedures(self):
        """Test _initialize_diagnostic_procedures method."""
        procedures = self.dealer._initialize_diagnostic_procedures()
        
        self.assertIsInstance(procedures, dict)
        self.assertIn('security_access', procedures)
        self.assertIn('read_memory', procedures)
        self.assertIn('write_memory', procedures)
    
    def test_perform_security_access_invalid_level(self):
        """Test perform_security_access with invalid level."""
        result = self.dealer.perform_security_access('invalid_level')
        
        self.assertIn('Invalid access level', result)
    
    @patch.object(MazdaDealerSecurity, '_execute_security_sequence')
    def test_perform_security_access_already_has_access(self, mock_execute):
        """Test perform_security_access when already has access."""
        # Set current level to dealer (level 2)
        self.dealer.current_security_level = 'dealer'
        
        # Try to get user access (level 1) - should already have it
        result = self.dealer.perform_security_access('user')
        
        self.assertIn('Already have', result)
        mock_execute.assert_not_called()
    
    @patch.object(MazdaDealerSecurity, '_execute_security_sequence')
    def test_perform_security_access_success(self, mock_execute):
        """Test perform_security_access with successful access."""
        mock_execute.return_value = True
        
        result = self.dealer.perform_security_access('dealer')
        
        self.assertIn('granted', result.lower())
        self.assertEqual(self.dealer.current_security_level, 'dealer')
        self.assertTrue(self.dealer.session_active)
    
    @patch.object(MazdaDealerSecurity, '_execute_security_sequence')
    def test_perform_security_access_failure(self, mock_execute):
        """Test perform_security_access with failed access."""
        mock_execute.return_value = False
        
        result = self.dealer.perform_security_access('dealer')
        
        self.assertIn('denied', result.lower())
        self.assertNotEqual(self.dealer.current_security_level, 'dealer')
    
    def test_execute_security_sequence(self):
        """Test _execute_security_sequence method."""
        # Mock seed_key_db
        mock_db = Mock()
        mock_db.ecu_database = {
            'ENGINE_ECU': {
                'seed_length': 4,
                'algorithm': 'ENGINE_ECU_2011'
            }
        }
        self.dealer.seed_key_db = mock_db
        
        # This should work even if simplified
        result = self.dealer._execute_security_sequence('dealer')
        
        # Result should be boolean
        self.assertIsInstance(result, bool)


if __name__ == '__main__':
    unittest.main()

