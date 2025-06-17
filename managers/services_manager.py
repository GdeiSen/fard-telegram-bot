from typing import TYPE_CHECKING, Any
from .base_manager import BaseManager

if TYPE_CHECKING:
    from ..bot import Bot


class ServicesRegistry:
    """Registry for managing service instances with direct property access."""
    
    def __init__(self, bot: 'Bot'):
        self.bot = bot
        self._services = {}
    
    def register_service(self, name: str, service_instance: Any) -> None:
        """Register a service instance."""
        self._services[name] = service_instance
        # Set as attribute for direct access
        setattr(self, name, service_instance)
    
    def get_service(self, name: str) -> Any:
        """Get a service by name."""
        return self._services.get(name)
    
    def __getattr__(self, name: str) -> Any:
        """Fallback for accessing services as attributes."""
        if name in self._services:
            return self._services[name]
        raise AttributeError(f"Service '{name}' not found")


class ServicesManager(BaseManager):
    """Manager for service registration and initialization."""
    
    def __init__(self, bot: 'Bot'):
        super().__init__(bot)
        self.registry = ServicesRegistry(bot)
    
    async def initialize(self) -> None:
        """Initialize all services."""
        from services.users_service import UsersService
        from services.services_service import ServicesService
        from services.poll_service import PollService
        from services.feedbacks_service import FeedbacksService
        
        # Register all services
        self.registry.register_service('users', UsersService(self.bot.database_manager))
        self.registry.register_service('tickets', ServicesService(self.bot.database_manager, self.bot.managers.event))
        self.registry.register_service('polls', PollService(self.bot.database_manager))
        self.registry.register_service('feedbacks', FeedbacksService(self.bot.database_manager))
    
    def get_registry(self) -> ServicesRegistry:
        """Get the services registry for bot.services access."""
        return self.registry 