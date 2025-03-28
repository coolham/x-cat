# -*- coding: utf-8 -*-
from typing import Dict, List, Optional, Any, Tuple
import asyncio
import time

from loguru import logger

"""
Category Analyzer
Provides automatic evolution and optimization features for the classification system
"""
class CategoryAnalyzer:
    """Category Analyzer Class"""
    
    def __init__(self, category_manager):
        """Initialize the category analyzer"""
        self.category_manager = category_manager
        self.storage = None
        self.config = {}
        self.is_running = False
        
        # Category suggestion cache
        self.category_suggestions = {}
        # Last analysis time
        self.last_analysis_time = 0
        
        # Performance metrics and optimization suggestions
        self.performance_metrics = {}
        self.optimization_suggestions = []
        self.evolution_history = {}
    
    async def initialize(self, config: Dict[str, Any]) -> bool:
        """Initialize the category analyzer
        
        Args:
            config: Configuration dictionary
            
        Returns:
            Whether initialization was successful
        """
        try:
            self.config = config
            self.storage = self.category_manager.storage
            
            return True
            
        except Exception as e:
            logger.error(f"Failed to initialize category analyzer: {str(e)}")
            return False
    
    async def start(self) -> bool:
        """Start the category analyzer
        
        Returns:
            Whether startup was successful
        """
        if not self.storage:
            logger.error("Category analyzer not initialized")
            return False
            
        self.is_running = True
        
        # Start periodic analysis task
        asyncio.create_task(self._periodic_analysis())
        
        logger.info("Category analyzer started")
        return True
    
    async def stop(self) -> bool:
        """Stop the category analyzer
        
        Returns:
            Whether shutdown was successful
        """
        self.is_running = False
        logger.info("Category analyzer stopped")
        return True
    
    async def _periodic_analysis(self) -> None:
        """Perform periodic analysis of the classification system"""
        while self.is_running:
            try:
                # Analysis interval (default: once per day)
                analysis_interval = self.config.get("analysis_interval", 86400)
                
                # Check if analysis needs to be performed
                current_time = int(time.time())
                if current_time - self.last_analysis_time < analysis_interval:
                    # Wait for a while
                    await asyncio.sleep(3600)  # Check every hour
                    continue
                
                # Execute analysis
                logger.info("Starting classification system analysis...")
                
                # Analyze category usage
                await self._analyze_category_usage()
                
                # Analyze category suggestions
                await self._analyze_category_suggestions()
                
                # Update last analysis time
                self.last_analysis_time = current_time
                
                logger.info("Classification system analysis completed")
                
                # Wait for next analysis cycle
                await asyncio.sleep(3600)
                
            except Exception as e:
                logger.error(f"Failed to execute category analysis task: {str(e)}")
                await asyncio.sleep(3600)  # Wait for a while before retrying on error
    
    async def _analyze_category_usage(self) -> None:
        """Analyze category usage"""
        categories = await self.storage.get_category_list()
        
        # Add new analysis dimensions
        usage_patterns = self._analyze_usage_patterns(categories)
        performance_metrics = self._calculate_performance_metrics(categories)
        optimization_suggestions = self._generate_optimization_suggestions(
            categories, usage_patterns, performance_metrics
        )
        
        # Update analysis results
        await self._update_analysis_results(
            usage_patterns,
            performance_metrics,
            optimization_suggestions
        )
    
    async def _analyze_category_suggestions(self) -> None:
        """Analyze category suggestions"""
        # Analyze system-collected category suggestions
        suggestion_threshold = self.config.get("suggestion_threshold", 10)
        
        # Auto-create high-frequency suggestions
        for parent_id, suggestions in self.category_suggestions.items():
            for name, count in suggestions.items():
                if count >= suggestion_threshold:
                    logger.info(f"Preparing to auto-create new category: {name}, parent: {parent_id}, suggestions: {count}")
    
    async def add_category_suggestion(self, parent_id: str, name: str) -> None:
        """Add a category suggestion
        
        Args:
            parent_id: Parent category ID
            name: Suggested category name
        """
        if parent_id not in self.category_suggestions:
            self.category_suggestions[parent_id] = {}
            
        if name not in self.category_suggestions[parent_id]:
            self.category_suggestions[parent_id][name] = 0
            
        self.category_suggestions[parent_id][name] += 1
        
        logger.debug(f"Recorded category suggestion: {name}, parent: {parent_id}, "
                    f"current count: {self.category_suggestions[parent_id][name]}")
    
    def _analyze_usage_patterns(self, categories: List[Dict]) -> Dict:
        """Analyze usage patterns
        
        Args:
            categories: List of categories
            
        Returns:
            Usage pattern analysis results
        """
        patterns = {
            "usage_trend": {},
            "popular_categories": [],
            "low_usage_categories": []
        }
        
        # Sort by usage frequency
        sorted_categories = sorted(categories, key=lambda x: x["count"], reverse=True)
        
        # Record usage trends
        for cat in sorted_categories:
            patterns["usage_trend"][cat["id"]] = {
                "count": cat["count"],
                "last_used": cat.get("last_used", 0)
            }
        
        # Identify popular categories
        patterns["popular_categories"] = [
            cat["id"] for cat in sorted_categories[:5]
        ]
        
        # Identify low-usage categories
        low_usage_threshold = self.config.get("low_usage_threshold", 5)
        patterns["low_usage_categories"] = [
            cat["id"] for cat in sorted_categories
            if cat["count"] < low_usage_threshold
        ]
        
        return patterns
    
    def _calculate_performance_metrics(self, categories: List[Dict]) -> Dict:
        """Calculate performance metrics
        
        Args:
            categories: List of categories
            
        Returns:
            Performance metrics
        """
        metrics = {
            "classification_accuracy": 0.0,
            "response_time": 0.0,
            "category_coverage": 0.0
        }
        
        # Calculate classification accuracy (based on user feedback)
        total_feedback = sum(cat.get("feedback_count", 0) for cat in categories)
        if total_feedback > 0:
            positive_feedback = sum(
                cat.get("positive_feedback", 0) for cat in categories
            )
            metrics["classification_accuracy"] = positive_feedback / total_feedback
        
        # Calculate response time (based on metadata)
        response_times = [
            cat.get("metadata", {}).get("response_time", 0)
            for cat in categories
        ]
        if response_times:
            metrics["response_time"] = sum(response_times) / len(response_times)
        
        # Calculate category coverage
        total_categories = len(categories)
        if total_categories > 0:
            active_categories = sum(
                1 for cat in categories
                if cat.get("status") == "active"
            )
            metrics["category_coverage"] = active_categories / total_categories
        
        return metrics
    
    def _generate_optimization_suggestions(
        self,
        categories: List[Dict],
        usage_patterns: Dict,
        performance_metrics: Dict
    ) -> List[Dict]:
        """Generate optimization suggestions
        
        Args:
            categories: List of categories
            usage_patterns: Usage patterns
            performance_metrics: Performance metrics
            
        Returns:
            List of optimization suggestions
        """
        suggestions = []
        
        # Suggestions based on usage patterns
        for cat_id in usage_patterns["low_usage_categories"]:
            suggestions.append({
                "type": "low_usage",
                "category_id": cat_id,
                "message": "Category has low usage, consider merging or deleting"
            })
        
        # Suggestions based on performance metrics
        if performance_metrics["classification_accuracy"] < 0.8:
            suggestions.append({
                "type": "accuracy",
                "message": "Low classification accuracy, consider optimizing classification rules"
            })
        
        if performance_metrics["response_time"] > 1.0:
            suggestions.append({
                "type": "performance",
                "message": "Long classification response time, consider optimizing classification algorithm"
            })
        
        return suggestions
    
    async def _update_analysis_results(
        self,
        usage_patterns: Dict,
        performance_metrics: Dict,
        optimization_suggestions: List[Dict]
    ) -> None:
        """Update analysis results
        
        Args:
            usage_patterns: Usage patterns
            performance_metrics: Performance metrics
            optimization_suggestions: Optimization suggestions
        """
        # Update performance metrics
        self.performance_metrics = performance_metrics
        
        # Update optimization suggestions
        self.optimization_suggestions = optimization_suggestions
        
        # Record evolution history
        self.evolution_history[int(time.time())] = {
            "usage_patterns": usage_patterns,
            "performance_metrics": performance_metrics,
            "optimization_suggestions": optimization_suggestions
        }
        
        # Save analysis results
        if self.storage:
            await self.storage.save_analysis_results({
                "performance_metrics": performance_metrics,
                "optimization_suggestions": optimization_suggestions,
                "evolution_history": self.evolution_history
            }) 