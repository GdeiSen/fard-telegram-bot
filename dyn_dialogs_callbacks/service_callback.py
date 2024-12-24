from typing import TYPE_CHECKING
from constants import Dialogs, Variables
from entities.service_ticket import ServiceTicket
import json

if TYPE_CHECKING:
    from telegram import Update
    from telegram.ext import ContextTypes
    from entities.dialog import Dialog
    from bot import Bot

async def service_callback(
    bot: "Bot",
    update: "Update",
    context: "ContextTypes.DEFAULT_TYPE",
    dialog: "Dialog",
    sequence_id: "int",
    item_id: "int",
    option_id: "int | None",
    answer: "str | None",
    state: "int",
) -> int | str:
    service_ticket = bot.local_storage.get(context, Variables.USER_SERVICE_TICKET)
    if (item_id not in [97, 98, 99]):
        service_ticket = None
    if (item_id in [97, 98, 99]):
        if (service_ticket is None):
            service_ticket = ServiceTicket(
                id = None,
                user_id = update.effective_user.id,
                dialog_id=dialog.id,
                sequence_id=sequence_id,
                item_id=item_id,
                answer=None,
                description=None,
                location = None,
                details=None,
                status = 0
            )
            details = json.loads(service_ticket.details) if service_ticket.details else {}
            raw_trace = bot.router.get_current_trace(context)
            dialog = bot.local_storage.get(context, Variables.ACTIVE_DYN_DIALOG)
            items = dialog.items
            sequences = dialog.sequences
            filtered_items = []
            for raw_item in raw_trace:
                if (":" not in str(raw_item)):
                    continue
                _sequence_id = int(raw_item.split(":")[0])
                _item_index = int(raw_item.split(":")[1])
                if (_item_index is not None and _sequence_id is not None):
                    _item_id = sequences[_sequence_id].items_ids[_item_index]
                    item = items[_item_id]
                    if (item is not None):
                        filtered_items.append(item.text)
            details["raw_trace"] = raw_trace
            details["trace"] = filtered_items
            if service_ticket.description is None:
                trace = bot.router.get_current_trace(context)
                for i, item in enumerate(trace):
                    if str(item).startswith("97:") or str(item).startswith("98:"):
                            service_ticket.description = filtered_items[i-3] + " [auto generated]"
                            break
            service_ticket.details = json.dumps(details, ensure_ascii=False)
        if (item_id == 97):
            service_ticket.description = answer
        if (item_id == 98):
            service_ticket.location = answer
        if (item_id == 99):
            details = json.loads(service_ticket.details) if service_ticket.details else {}
            details["phone_number"] = answer
            service_ticket.details = json.dumps(details, ensure_ascii=False)
        bot.local_storage.set(context, Variables.USER_SERVICE_TICKET, service_ticket)
        
    if state == 1:
        bot.service_service.create_service_ticket(service_ticket)
        bot.local_storage.set(context, Variables.USER_SERVICE_TICKET, None)
        await bot.send_message(update, context, "service_ticket_completed", dynamic=False)
        return await bot.router.execute(Dialogs.MENU, update, context)

    return Dialogs.DYN_DIALOG_ITEM
