# -*- coding: utf-8 -*-
"""
Classification Prompts
Load and manage prompts for AI classification
"""
import os
import yaml
from typing import Dict, Optional

class PromptManager:
    """Prompt manager for loading and managing prompts"""
    
    def __init__(self, config_dir: str = "config/prompts"):
        """Initialize the prompt manager
        
        Args:
            config_dir: Directory containing prompt configuration files
        """
        self.config_dir = config_dir
        self.prompts: Dict[str, Dict] = {}
        self._load_prompts()
    
    def _load_prompts(self) -> None:
        """Load prompts from configuration files"""
        try:
            # Load classification prompts
            prompt_file = os.path.join(self.config_dir, "classification.yaml")
            if os.path.exists(prompt_file):
                with open(prompt_file, 'r', encoding='utf-8') as f:
                    self.prompts = yaml.safe_load(f)
            else:
                raise FileNotFoundError(f"Prompt configuration file not found: {prompt_file}")
                
        except Exception as e:
            raise RuntimeError(f"Failed to load prompts: {str(e)}")
    
    def get_prompt(self, prompt_type: str, language: str = "en") -> Optional[str]:
        """Get a prompt template by type and language
        
        Args:
            prompt_type: Type of prompt (e.g., "classification")
            language: Language code (e.g., "en", "zh")
            
        Returns:
            Prompt template string or None if not found
        """
        try:
            return self.prompts[language][prompt_type]["template"]
        except KeyError:
            return None
    
    def reload_prompts(self) -> None:
        """Reload prompts from configuration files"""
        self._load_prompts()

# Create a global prompt manager instance
prompt_manager = PromptManager()

# Export commonly used prompts
def get_classification_prompt(language: str = "en") -> str:
    """Get the classification prompt template
    
    Args:
        language: Language code (e.g., "en", "zh")
        
    Returns:
        Classification prompt template
    """
    prompt = prompt_manager.get_prompt("classification", language)
    if not prompt:
        raise ValueError(f"Classification prompt not found for language: {language}")
    return prompt
