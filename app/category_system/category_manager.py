# -*- coding: utf-8 -*-
"""
Category Manager
Provides core management functionality for the classification system
"""
from typing import Dict, List, Optional, Any
from loguru import logger

from app.core.runtime import Runtime
from app.core.module import Module
from app.core.events import MessageAnalyzed

from .models.category import Category, CategoryLevel
from .storage.category_storage import CategoryStorage
from .ai.classifier import AIClassifier

class CategoryManager(Module):
    """Category Manager Class"""
    
    def __init__(self, runtime: Runtime):
        """Initialize the category manager"""
        super().__init__(runtime=runtime, module_id="category_manager")
        self.storage = None
        self.classifier = None
        self.config = {}
        self.is_running = False
        self.initialized = False
    
    async def initialize(self, config: Dict[str, Any]) -> bool:
        """Initialize the category manager"""
        try:
            self.config = config
            
            # Get storage module reference
            storage_module = self.runtime.get_module("storage")
            if not storage_module:
                logger.error("Failed to get storage module")
                return False
            
            # Create category storage
            self.storage = CategoryStorage(storage_module)
            if not await self.storage.initialize():
                logger.error("Failed to initialize category storage")
                return False
            
            # Create AI classifier
            self.classifier = AIClassifier(self.runtime, self.storage)
            if not await self.classifier.initialize(config):
                logger.error("Failed to initialize AI classifier")
                return False
            
            # Register event handler
            if hasattr(self.runtime, "event_bus"):
                self.runtime.event_bus.subscribe(MessageAnalyzed, self._handle_message_analyzed)
            
            self.initialized = True
            logger.info("Category manager initialization successful")
            return True
            
        except Exception as e:
            logger.error(f"Failed to initialize category manager: {str(e)}")
            return False
    
    async def start(self) -> bool:
        """Start the category manager"""
        if not self.initialized:
            logger.error("Category manager not initialized")
            return False
            
        self.is_running = True
        logger.info("Category manager started")
        return True
    
    async def stop(self) -> bool:
        """Stop the category manager"""
        self.is_running = False
        logger.info("Category manager stopped")
        return True
    
    async def _handle_message_analyzed(self, event: MessageAnalyzed) -> None:
        """Handle message analyzed event"""
        if not self.is_running:
            return
            
        message_id = event.message.message_id
        content = event.message.content
        analysis = event.analysis_result
        
        # Classify content
        logger.info(f"Starting to classify message: {message_id}")
        
        # Use AI to classify
        classification = await self.classifier.classify_content(
            message_id=message_id,
            content=content,
            full_analysis=analysis
        )
        
        if not classification:
            logger.error(f"Failed to classify message: {message_id}")
            return
            
        # Store classification result
        logger.info(f"Classification result: {classification}")
        
        await self.storage.store_content_category(
            message_id=message_id,
            primary_cat_id=classification["primary_category_id"],
            secondary_cat_id=classification.get("secondary_category_id"),
            confidence=classification["confidence"]
        )
        
        logger.info(f"Message classification completed: {message_id}")
    
    async def get_active_categories(self, level: Optional[CategoryLevel] = None) -> List[Dict]:
        """Get current active category list"""
        if not self.storage:
            return []
            
        return await self.storage.get_category_list(level)
    
    async def add_primary_category(self, name: str, description: str, 
                                examples: List[str]) -> Optional[Dict]:
        """Add primary category"""
        try:
            category = Category.create_primary(
                name=name,
                description=description,
                examples=examples
            )
            
            # Store in database
            conn = self.storage.storage_module.connection
            cursor = conn.cursor()
            
            cursor.execute("""
            INSERT INTO categories (id, name, level, description, examples, created_at, updated_at)
            VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (
                category.id,
                category.name,
                category.level.value,
                category.description,
                json.dumps(category.examples),
                int(time.time()),
                int(time.time())
            ))
            
            conn.commit()
            return category.to_dict()
            
        except Exception as e:
            logger.error(f"Failed to add primary category: {str(e)}")
            return None
    
    async def add_secondary_category(self, name: str, description: str, 
                                   parent_id: str, examples: List[str]) -> Optional[Dict]:
        """Add secondary category"""
        try:
            category = Category.create_secondary(
                name=name,
                description=description,
                parent_id=parent_id,
                examples=examples
            )
            
            # Store in database
            conn = self.storage.storage_module.connection
            cursor = conn.cursor()
            
            cursor.execute("""
            INSERT INTO categories (id, name, level, description, parent_id, examples, created_at, updated_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                category.id,
                category.name,
                category.level.value,
                category.description,
                category.parent_id,
                json.dumps(category.examples),
                int(time.time()),
                int(time.time())
            ))
            
            conn.commit()
            return category.to_dict()
            
        except Exception as e:
            logger.error(f"Failed to add secondary category: {str(e)}")
            return None
    
    async def classify_message(self, message_id: str, content: str) -> Optional[Dict]:
        """Classify message directly"""
        if not self.is_running or not self.classifier:
            logger.error("Category manager not running or classifier not initialized")
            return None
            
        # Directly call classifier
        classification = await self.classifier.classify_content(
            message_id=message_id,
            content=content
        )
        
        if not classification:
            return None
            
        # Store classification result
        await self.storage.store_content_category(
            message_id=message_id,
            primary_cat_id=classification["primary_category_id"],
            secondary_cat_id=classification.get("secondary_category_id"),
            confidence=classification["confidence"]
        )
        
        return classification
