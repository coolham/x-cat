# -*- coding: utf-8 -*-
"""
Category Models
Define data models for categories
"""
from enum import Enum
from typing import List, Dict, Optional
from dataclasses import dataclass
import uuid
import time

class CategoryLevel(Enum):
    """Category level enum"""
    PRIMARY = 1    # Primary category
    SECONDARY = 2  # Secondary category


@dataclass
class Category:
    """Category entity class"""
    id: str                     # Category unique identifier
    name: str                   # Category name
    level: CategoryLevel        # Category level
    description: str            # Category description
    parent_id: Optional[str]    # Parent category ID (only for secondary categories)
    examples: List[str]         # Category examples
    created_at: int             # Creation timestamp
    updated_at: int             # Update timestamp
    count: int = 0              # Usage count
    
    @classmethod
    def create_primary(cls, name: str, description: str, examples: List[str]) -> 'Category':
        """Create primary category"""
        now = int(time.time())
        return cls(
            id=f"p_{uuid.uuid4().hex[:8]}",
            name=name,
            level=CategoryLevel.PRIMARY,
            description=description,
            parent_id=None,
            examples=examples,
            created_at=now,
            updated_at=now
        )
    
    @classmethod
    def create_secondary(cls, name: str, description: str, 
                        parent_id: str, examples: List[str]) -> 'Category':
        """Create secondary category"""
        now = int(time.time())
        return cls(
            id=f"s_{uuid.uuid4().hex[:8]}",
            name=name,
            level=CategoryLevel.SECONDARY,
            description=description,
            parent_id=parent_id,
            examples=examples,
            created_at=now,
            updated_at=now
        )
    
    def to_dict(self) -> Dict:
        """Convert to dictionary representation"""
        return {
            "id": self.id,
            "name": self.name,
            "level": self.level.value,
            "description": self.description,
            "parent_id": self.parent_id,
            "examples": self.examples,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
            "count": self.count
        }
    
    @classmethod
    def from_dict(cls, data: Dict) -> 'Category':
        """Create category from dictionary"""
        return cls(
            id=data["id"],
            name=data["name"],
            level=CategoryLevel(data["level"]),
            description=data["description"],
            parent_id=data["parent_id"],
            examples=data["examples"],
            created_at=data["created_at"],
            updated_at=data["updated_at"],
            count=data.get("count", 0)
        ) 