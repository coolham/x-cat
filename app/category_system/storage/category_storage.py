# -*- coding: utf-8 -*-
"""
Category Storage Interface
Provides storage functionality for the category system
"""
import os
import json
import time
from typing import Dict, List, Optional
from loguru import logger

from ..models.category import Category, CategoryLevel

class CategoryStorage:
    """Category Storage Interface"""
    
    def __init__(self, storage_module, db_path: str = None):
        """Initialize category storage"""
        self.storage_module = storage_module
        self.db_path = db_path or "data/categories.json"
        self.data = {
            "categories": {},
            "content_categories": {}
        }
    
    async def initialize(self) -> bool:
        """Initialize storage system"""
        try:
            # Create data directory if not exists
            os.makedirs(os.path.dirname(self.db_path), exist_ok=True)
            
            # Load existing data if file exists
            if os.path.exists(self.db_path):
                try:
                    with open(self.db_path, 'r', encoding='utf-8') as f:
                        self.data = json.load(f)
                except json.JSONDecodeError:
                    logger.warning("Corrupted JSON file detected, using empty data")
                    self.data = {"categories": {}, "content_categories": {}}
            
            # Create empty file if it doesn't exist
            if not os.path.exists(self.db_path):
                await self._save_data()
            
            return True
        except Exception as e:
            logger.error(f"Failed to initialize category storage: {str(e)}")
            return False
    
    async def _save_data(self) -> None:
        """Save data to file"""
        try:
            with open(self.db_path, 'w', encoding='utf-8') as f:
                json.dump(self.data, f, indent=2, ensure_ascii=False)
        except Exception as e:
            logger.error(f"Failed to save category data: {str(e)}")
            raise  # Re-raise the exception to handle it in the calling method
    
    async def store_category(self, category: Category) -> bool:
        """Store a category"""
        try:
            category_dict = category.to_dict()
            self.data["categories"][category.id] = category_dict
            
            # Update parent's children list if it's a secondary category
            if category.level == CategoryLevel.SECONDARY and category.parent_id:
                parent = self.data["categories"].get(category.parent_id)
                if parent:
                    if "children" not in parent:
                        parent["children"] = []
                    if category.id not in parent["children"]:
                        parent["children"].append(category.id)
            
            await self._save_data()
            return True
        except Exception as e:
            logger.error(f"Failed to store category: {str(e)}")
            return False
    
    async def update_category(self, category: Category) -> bool:
        """Update a category"""
        try:
            if category.id not in self.data["categories"]:
                return False
                
            category_dict = category.to_dict()
            self.data["categories"][category.id] = category_dict
            await self._save_data()
            return True
        except Exception as e:
            logger.error(f"Failed to update category: {str(e)}")
            return False
    
    async def delete_category(self, category_id: str) -> bool:
        """Delete a category"""
        try:
            if category_id not in self.data["categories"]:
                return False
                
            category = self.data["categories"][category_id]
            
            # Remove from parent's children list if it's a secondary category
            if category["level"] == CategoryLevel.SECONDARY.value and category["parent_id"]:
                parent = self.data["categories"].get(category["parent_id"])
                if parent:
                    if "children" not in parent:
                        parent["children"] = []
                    if category_id in parent["children"]:
                        parent["children"].remove(category_id)
            
            # Delete the category
            del self.data["categories"][category_id]
            await self._save_data()
            return True
        except Exception as e:
            logger.error(f"Failed to delete category: {str(e)}")
            return False
    
    async def get_category_by_id(self, category_id: str) -> Optional[Dict]:
        """Get a category by ID"""
        return self.data["categories"].get(category_id)
    
    async def get_category_list(self, level: Optional[CategoryLevel] = None) -> List[Dict]:
        """Get category list"""
        categories = list(self.data["categories"].values())
        
        if level is not None:
            categories = [cat for cat in categories if cat["level"] == level.value]
            
        return categories
    
    async def store_content_category(self, message_id: str, primary_cat_id: str, 
                                   secondary_cat_id: Optional[str], confidence: float) -> bool:
        """Store content classification result"""
        try:
            # Verify categories exist
            if primary_cat_id not in self.data["categories"]:
                return False
            if secondary_cat_id and secondary_cat_id not in self.data["categories"]:
                return False
            
            self.data["content_categories"][message_id] = {
                "primary_id": primary_cat_id,
                "secondary_id": secondary_cat_id,
                "confidence": confidence,
                "created_at": int(time.time())
            }
            
            # Update category usage count
            await self._increment_category_usage(primary_cat_id)
            if secondary_cat_id:
                await self._increment_category_usage(secondary_cat_id)
            
            await self._save_data()
            return True
        except Exception as e:
            logger.error(f"Failed to store classification result: {str(e)}")
            return False
    
    async def _increment_category_usage(self, category_id: str) -> None:
        """Increment category usage count"""
        if category_id in self.data["categories"]:
            self.data["categories"][category_id]["count"] += 1
            self.data["categories"][category_id]["updated_at"] = int(time.time())
            await self._save_data()
    
    async def save_analysis_results(self, results: Dict) -> bool:
        """Save analysis results"""
        try:
            self.data["analysis_results"] = results
            await self._save_data()
            return True
        except Exception as e:
            logger.error(f"Failed to save analysis results: {str(e)}")
            return False
