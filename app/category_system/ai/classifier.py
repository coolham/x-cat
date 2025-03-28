# -*- coding: utf-8 -*-
"""
AI Classifier Implementation
Provides AI-based content classification functionality
"""
from typing import Dict, List, Optional, Any
import json
from loguru import logger

from app.services.mcp_service import ContentAnalysisMCPService
from ..models.category import Category, CategoryLevel
from .prompts import get_classification_prompt

class AIClassifier:
    """AI Classifier Implementation"""
    
    def __init__(self, runtime, category_storage):
        """Initialize the classifier"""
        self.runtime = runtime
        self.category_storage = category_storage
        self.mcp_service = None
    
    async def initialize(self, config: Dict[str, Any]) -> bool:
        """Initialize the classifier"""
        try:
            # Get AI analyzer configuration
            analyzer_config = config.get("content_analyzer", {})
            
            # Create MCP service instance
            self.mcp_service = ContentAnalysisMCPService(
                api_key=analyzer_config.get("api_key"),
                provider=analyzer_config.get("provider", "openrouter"),
                model=analyzer_config.get("model"),
                proxy_url=analyzer_config.get("proxy_url"),
                max_tokens=analyzer_config.get("max_tokens", 2000),
                temperature=0.3,  # Low temperature for more deterministic classification
                max_content_length=analyzer_config.get("max_content_length", 8000),
                max_total_length=analyzer_config.get("max_total_length", 15000),
                format_type="markdown"
            )
            
            return True
            
        except Exception as e:
            logger.error(f"Failed to initialize classifier: {str(e)}")
            return False
    
    async def classify_content(self, message_id: str, content: str, 
                             full_analysis: Dict = None) -> Optional[Dict]:
        """Classify content"""
        try:
            # Get current categories
            primary_categories = await self._get_primary_categories()
            secondary_categories = await self._get_secondary_categories()
            
            # Prepare classification prompt
            prompt = self._prepare_classification_prompt(
                content=content,
                primary_categories=primary_categories,
                secondary_categories=secondary_categories,
                full_analysis=full_analysis
            )
            
            # Get classification from AI
            response = await self.mcp_service.analyze_content(prompt)
            
            # Parse classification result
            result = self._parse_classification_result(
                response=response,
                primary_categories=primary_categories,
                secondary_categories=secondary_categories
            )
            
            if result:
                logger.info(f"Successfully classified content: {message_id}")
                return result
            else:
                logger.error(f"Failed to parse classification result: {message_id}")
                return None
                
        except Exception as e:
            logger.error(f"Failed to classify content: {str(e)}")
            return None
    
    async def _get_primary_categories(self) -> Dict[str, Dict]:
        """Get primary category list"""
        primary_cats = {}
        categories = await self.category_storage.get_category_list(CategoryLevel.PRIMARY)
        
        for cat in categories:
            primary_cats[cat["name"]] = cat
            
        return primary_cats
    
    async def _get_secondary_categories(self) -> Dict[str, Dict]:
        """Get secondary category list"""
        secondary_cats = {}
        categories = await self.category_storage.get_category_list(CategoryLevel.SECONDARY)
        
        for cat in categories:
            secondary_cats[cat["name"]] = cat
            
        return secondary_cats
    
    def _prepare_classification_prompt(self, content: str, 
                                     primary_categories: Dict[str, Dict],
                                     secondary_categories: Dict[str, Dict],
                                     full_analysis: Dict = None) -> str:
        """Prepare classification prompt"""
        # Format primary categories
        primary_cat_str = ""
        for name, cat in primary_categories.items():
            examples = ", ".join(cat.get("examples", []))
            primary_cat_str += f"- {name}: {cat.get('description')}. Examples: {examples}\n"
        
        # Format secondary categories by parent
        secondary_cat_str = ""
        parent_groups = {}
        for name, cat in secondary_categories.items():
            parent_id = cat.get("parent_id")
            if parent_id not in parent_groups:
                parent_groups[parent_id] = []
            parent_groups[parent_id].append(cat)
        
        # Format secondary categories under each parent
        for parent_id, cats in parent_groups.items():
            parent_name = None
            for name, cat in primary_categories.items():
                if cat.get("id") == parent_id:
                    parent_name = name
                    break
            
            if not parent_name:
                continue
                
            secondary_cat_str += f"\n### Secondary categories under {parent_name}:\n"
            for cat in cats:
                examples = ", ".join(cat.get("examples", []))
                secondary_cat_str += f"- {cat.get('name')}: {cat.get('description')}. Examples: {examples}\n"
        
        # Use content summary if available
        if full_analysis and "summary" in full_analysis:
            content_for_classification = f"Content title/topic: {full_analysis.get('title', 'Unknown')}\n\n"
            content_for_classification += f"Content summary: {full_analysis.get('summary')}\n\n"
            content_for_classification += f"Content keywords: {', '.join(full_analysis.get('keywords', []))}\n\n"
            content_for_classification += f"Content snippet: {content[:500]}..."
        else:
            content_for_classification = content[:3000] + ("..." if len(content) > 3000 else "")
        
        # Fill prompt template
        prompt = get_classification_prompt("en").format(
            primary_categories=primary_cat_str,
            secondary_categories=secondary_cat_str,
            content=content_for_classification
        )
        
        return prompt
    
    def _parse_classification_result(self, response: str, 
                                   primary_categories: Dict[str, Dict],
                                   secondary_categories: Dict[str, Dict]) -> Optional[Dict]:
        """Parse classification result"""
        try:
            # Extract JSON from response
            json_start = response.find("{")
            json_end = response.rfind("}")
            
            if json_start == -1 or json_end == -1:
                logger.error(f"No JSON found in response: {response}")
                return None
                
            json_str = response[json_start:json_end+1]
            result = json.loads(json_str)
            
            # Validate required fields
            if "primary_category" not in result:
                logger.error(f"Classification result missing required fields: {result}")
                return None
                
            # Find category IDs
            primary_name = result["primary_category"]
            primary_id = None
            for name, cat in primary_categories.items():
                if name.lower() == primary_name.lower():
                    primary_id = cat["id"]
                    primary_name = name
                    break
            
            if not primary_id:
                logger.warning(f"Primary category ID not found: {primary_name}")
                # Try fuzzy matching
                for name, cat in primary_categories.items():
                    if primary_name.lower() in name.lower() or name.lower() in primary_name.lower():
                        primary_id = cat["id"]
                        primary_name = name
                        logger.info(f"Using fuzzy matched primary category: {primary_name}")
                        break
            
            # Find secondary category ID if specified
            secondary_name = result.get("secondary_category")
            secondary_id = None
            
            if secondary_name:
                for name, cat in secondary_categories.items():
                    if name.lower() == secondary_name.lower():
                        secondary_id = cat["id"]
                        secondary_name = name
                        break
                
                if not secondary_id:
                    logger.warning(f"Secondary category ID not found: {secondary_name}")
                    # Try fuzzy matching
                    for name, cat in secondary_categories.items():
                        if secondary_name.lower() in name.lower() or name.lower() in secondary_name.lower():
                            if cat.get("parent_id") == primary_id:  # Ensure parent matches
                                secondary_id = cat["id"]
                                secondary_name = name
                                logger.info(f"Using fuzzy matched secondary category: {secondary_name}")
                                break
            
            # Return result
            return {
                "primary_category": primary_name,
                "primary_category_id": primary_id,
                "secondary_category": secondary_name if secondary_name else None,
                "secondary_category_id": secondary_id,
                "confidence": float(result.get("confidence", 0.7)),
                "reasoning": result.get("reasoning", "")
            }
            
        except Exception as e:
            logger.error(f"Failed to parse classification result: {str(e)}, response: {response}")
            return None
