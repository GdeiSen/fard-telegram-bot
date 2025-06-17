from typing import Dict, List, Callable, Any, Coroutine

class EventEmitter:
    """
    Simple event emitter implementation for asynchronous event handling.
    Allows registering and triggering event handlers in a publish-subscribe pattern.
    """
    
    def __init__(self):
        """Initialize an empty event registry."""
        self._events: Dict[str, List[Callable[..., Coroutine[Any, Any, Any]]]] = {}
        self._input_handlers: Dict[int, Callable[..., Coroutine[Any, Any, Any]]] = {}
        self._active_dialog_type: Dict[int, int] = {}  # user_id -> dialog_state
        
    def on(self, event_name: str, handler: Callable[..., Coroutine[Any, Any, Any]]) -> None:
        """
        Register an event handler for a specific event.
        
        Args:
            event_name: The name of the event to listen for
            handler: An async function to call when the event is emitted
        """
        if event_name not in self._events:
            self._events[event_name] = []
        self._events[event_name].append(handler)
        
    def off(self, event_name: str, handler: Callable[..., Coroutine[Any, Any, Any]]) -> None:
        """
        Remove an event handler for a specific event.
        
        Args:
            event_name: The name of the event
            handler: The handler function to remove
        """
        if event_name in self._events and handler in self._events[event_name]:
            self._events[event_name].remove(handler)
            
    async def once(self, event_name: str, handler: Callable[..., Coroutine[Any, Any, Any]]) -> None:
        """
        Register an event handler that will be removed after being called once.
        
        Args:
            event_name: The name of the event to listen for
            handler: An async function to call when the event is emitted
        """
        async def one_time_handler(*args, **kwargs):
            result = await handler(*args, **kwargs)
            self.off(event_name, one_time_handler)
            return result
            
        self.on(event_name, one_time_handler)
            
    async def emit(self, event_name: str, *args, **kwargs) -> List[Any]:
        """
        Trigger all handlers for a specific event.
        
        Args:
            event_name: The name of the event to emit
            *args, **kwargs: Arguments to pass to the event handlers
            
        Returns:
            A list of the return values from all event handlers
        """
        results = []
        if event_name in self._events:
            for handler in self._events[event_name]:
                results.append(await handler(*args, **kwargs))
        return results
    
    def register_input_handler(self, user_id: int, dialog_type: int, handler: Callable[..., Coroutine[Any, Any, Any]]) -> None:
        """
        Register an input handler for a specific user's active dialog.
        
        Args:
            user_id: The ID of the user
            dialog_type: The dialog state type (text input, photo input, etc.)
            handler: The async handler function to process the input
        """
        self._input_handlers[user_id] = handler
        self._active_dialog_type[user_id] = dialog_type
        
    def remove_input_handler(self, user_id: int) -> None:
        """
        Remove the input handler for a specific user.
        
        Args:
            user_id: The ID of the user
        """
        if user_id in self._input_handlers:
            del self._input_handlers[user_id]
        if user_id in self._active_dialog_type:
            del self._active_dialog_type[user_id]
            
    def get_input_handler(self, user_id: int) -> tuple[Callable[..., Coroutine[Any, Any, Any]] | None, int | None]:
        """
        Get the active input handler and dialog type for a specific user.
        
        Args:
            user_id: The ID of the user
            
        Returns:
            A tuple of (handler function, dialog type) or (None, None) if no handler exists
        """
        handler = self._input_handlers.get(user_id)
        dialog_type = self._active_dialog_type.get(user_id)
        return handler, dialog_type
        
    def has_input_handler(self, user_id: int) -> bool:
        """
        Check if a user has an active input handler.
        
        Args:
            user_id: The ID of the user
            
        Returns:
            True if the user has an active input handler, False otherwise
        """
        return user_id in self._input_handlers 