from typing import TYPE_CHECKING
from constants import Dialogs, Variables
from models import ServiceTicket
import json
from datetime import datetime

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
    service_ticket = bot.managers.storage.get(context, Variables.USER_SERVICE_TICKET)
    if (item_id not in [97, 98, 99]):
        service_ticket = None
        bot.managers.storage.set(context, Variables.USER_SERVICE_TICKET, None)
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
            
            active_dialog = bot.managers.storage.get(context, Variables.ACTIVE_DYN_DIALOG)
            active_items = active_dialog.items
            active_options = active_dialog.options
            
            raw_trace = bot.managers.router.get_current_trace(context)
            
            details = json.loads(service_ticket.details) if service_ticket.details else {}
            details["raw_trace"] = raw_trace
            
            filtered_items = []
            chosen_options = []
            
            for raw_item in raw_trace:
                if (":" not in str(raw_item)):
                    continue
                
                parts = str(raw_item).split(":")
                
                if len(parts) < 2:
                    continue
                
                try:
                    if len(parts) >= 4:
                        trace_dialog_item = int(parts[0])
                        dialog_id = int(parts[1])
                        _sequence_id = int(parts[2])
                        _item_id = int(parts[3])
                        _option_id = int(parts[4]) if len(parts) >= 5 and parts[4].isdigit() else None
                        
                        if _item_id in active_items:
                            item = active_items[_item_id]
                            if item is not None:
                                filtered_items.append({
                                    "id": _item_id,
                                    "text": item.text,
                                    "type": item.type
                                })
                                
                                if _option_id is not None:
                                    if _option_id in active_options:
                                        option = active_options[_option_id]
                                        chosen_options.append({
                                            "item_id": _item_id,
                                            "option_id": _option_id,
                                            "text": option.text
                                        })
                    
                except (ValueError, IndexError):
                    print(f"Failed to process trace item: {raw_item}")
                    continue
            
            formatted_trace = []
            item_to_options = {}
            
            for option in chosen_options:
                item_id = option["item_id"]
                item_to_options[item_id] = option
            
            for i, item in enumerate(filtered_items):
                item_id = item["id"]
                item_text = item["text"]
                
                next_option = None
                if i < len(filtered_items) - 1:
                    next_item_id = filtered_items[i + 1]["id"]
                    if next_item_id in item_to_options:
                        next_option = item_to_options[next_item_id]
                
                if next_option:
                    formatted_trace.append(f"{item_text}: {next_option['text']}")
                else:
                    formatted_trace.append(item_text)
            
            details["trace"] = formatted_trace
            
            if not service_ticket.description and formatted_trace:
                last_item_option_pair = None
                for i, item in enumerate(filtered_items):
                    item_id = item["id"]
                    if item_id in [97, 98, 99]:
                        break
                    if i < len(filtered_items) - 1:
                        next_item_id = filtered_items[i + 1]["id"]
                        if next_item_id in item_to_options:
                            last_item_option_pair = f"{item['text']} | {item_to_options[next_item_id]['text']}"
                if last_item_option_pair:
                    service_ticket.description = last_item_option_pair
            
            service_ticket.details = json.dumps(details, ensure_ascii=False)
        
        if (item_id == 97):
            service_ticket.description = answer
        if (item_id == 98):
            service_ticket.location = answer
        if (item_id == 99):
            details = json.loads(service_ticket.details) if service_ticket.details else {}
            details["phone_number"] = answer
            service_ticket.details = json.dumps(details, ensure_ascii=False)
        
        bot.managers.storage.set(context, Variables.USER_SERVICE_TICKET, service_ticket)
        
    if state == 1:
        saved_ticket = await bot.services.tickets.create_service_ticket(service_ticket)
        bot.managers.storage.set(context, Variables.USER_SERVICE_TICKET, None)
        
        if saved_ticket and saved_ticket.id:
            # Используем NotificationManager для отправки уведомления администраторам
            await bot.managers.notification.notify_new_ticket(saved_ticket)
            
        await bot.send_message(update, context, "service_ticket_completed", dynamic=False)
        return await bot.managers.router.execute(Dialogs.MENU, update, context)

    return Dialogs.DYN_DIALOG_ITEM



