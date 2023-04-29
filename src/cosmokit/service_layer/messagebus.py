import logging
from collections.abc import Callable

from ..domain.model import Command, Event, Message
from .unit_of_work import AbstractUnitOfWork

logger = logging.getLogger(__name__)


class MessageBus:
    """
    Entrypoint for applications to interact with a particular bounded context
    (`Aggregate`) via message handling

    Applications can request the `MessageBus` to handle a given command or
    event message The MessageBus will invoke all the registered handlers for
    that message and do the same for all messages raised by the Aggregate
    during the handling of the first message.

    The `MessageBus` uses its `uow.repository` to collect the events generated
    by all `Aggregates` used in the event handlers, and `seen` by the
    repository

    All the `hanlders` registered for events and commands messages have their
    dependencies (such as UoW) injected during the `bootstrap` process, so that
    they only take one argument as input: the message to be handled

    """

    def __init__(
        self,
        uow: AbstractUnitOfWork,
        event_handlers: dict[type[Event], list[Callable[[Event], None]]],
        command_handlers: dict[type[Command], Callable[[Command], None]],
    ):
        self.uow = uow
        self.event_handlers = event_handlers
        self.command_handlers = command_handlers

    def handle(self, message: Message) -> None:
        self.queue = [message]
        while self.queue:
            message = self.queue.pop(0)
            if isinstance(message, Event):
                self.handle_event(message)
            elif isinstance(message, Command):
                self.handle_command(message)
            else:
                raise Exception(f"{message} was not an Event or Command")

    def handle_event(self, event: Event) -> None:
        for handler in self.event_handlers.get(type(event), []):
            try:
                logger.debug("handling event %s with handler %s", event, handler)
                handler(event)
                self.queue.extend(self.uow.collect_new_events())
            except Exception:
                logger.exception("Exception handling event %s", event)
                continue

    def handle_command(self, command: Command) -> None:
        logger.debug("handling command %s", command)
        try:
            handler = self.command_handlers[type(command)]
            handler(command)
            self.queue.extend(self.uow.collect_new_events())
        except Exception:
            logger.exception("Exception handling command %s", command)
            raise
