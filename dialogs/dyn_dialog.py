from typing import TYPE_CHECKING
from constants import Dialogs, Actions, Variables

if TYPE_CHECKING:
    from telegram import Update
    from telegram.ext import ContextTypes
    from bot import Bot


async def start_dyn_dialog(update: "Update", context: "ContextTypes.DEFAULT_TYPE", bot: "Bot") -> int | str:

    bot.router.set_parent_item(context, Dialogs.DYN_DIALOG_ITEM)
    dialog = bot.local_storage.get(context, Variables.ACTIVE_DYN_DIALOG)

    if dialog is None:
        return Actions.END

    sequences = dialog.sequences
    items = dialog.items
    options = dialog.options

    active_sequence_id = bot.local_storage.get(context, Variables.ACTIVE_DIALOG_SEQUENCE_ID) or 0
    active_sequence_item_index = bot.local_storage.get(context, Variables.ACTIVE_DIALOG_SEQUENCE_ITEM_INDEX) or 0
    active_sequence = sequences.get(active_sequence_id)
    active_items = [items[i] for i in active_sequence.items_ids]
    active_item = active_items[active_sequence_item_index]
    args = None

    if update.callback_query and update.callback_query.data is not None:
        callback_data = update.callback_query.data.split(":")
        try:
            args = int(callback_data[1]) if len(callback_data) > 1 else None
        except ValueError:
            args = None

    handled_data = bot.local_storage.get(context, Variables.HANDLED_DATA)
    answer: str | None = None
    if handled_data:
        answer = handled_data
        bot.local_storage.set(context, Variables.HANDLED_DATA, None)
    elif args is not None:
        answer = options.get(args).text

    fallback_item = bot.router.get_entry_point_item(context) or -1

    if args is not None or handled_data:
        state = 0
        index = active_items.index(active_item)
        selected_option = options.get(args)
        if selected_option is not None and selected_option.sequence_id is not None:
            bot.local_storage.set(context, Variables.ACTIVE_DIALOG_SEQUENCE_ID, selected_option.sequence_id)
            bot.local_storage.set(context, Variables.ACTIVE_DIALOG_SEQUENCE_ITEM_INDEX, 0)
        elif index + 1 < len(active_items):
            bot.local_storage.set(context, Variables.ACTIVE_DIALOG_SEQUENCE_ITEM_INDEX, index + 1)
        elif active_sequence.next_sequence_id is not None:
            bot.local_storage.set(context, Variables.ACTIVE_DIALOG_SEQUENCE_ID, active_sequence.next_sequence_id)
            bot.local_storage.set(context, Variables.ACTIVE_DIALOG_SEQUENCE_ITEM_INDEX, 0)
        else:
            state = 1
            
        trace_item = str(active_sequence_id) + ":" + str(active_sequence_item_index)
        bot.router.add_trace_item(context, trace_item)
        

        await bot.dyn_dialog_handlers_manager.handle(
            fallback_item,
            bot,
            update,
            context,
            dialog,
            active_sequence.id,
            active_item.id,
            args,
            answer,
            state
        )

        if state == 1: return fallback_item
        

        active_sequence_id = bot.local_storage.get(context, Variables.ACTIVE_DIALOG_SEQUENCE_ID)
        active_sequence_item_index = bot.local_storage.get(context, Variables.ACTIVE_DIALOG_SEQUENCE_ITEM_INDEX) or 0
        active_sequence = sequences.get(active_sequence_id)
        active_items = [items[i] for i in active_sequence.items_ids]
        if active_sequence_item_index < len(active_items):
            active_item = active_items[active_sequence_item_index]
        else:
            active_item = None

    button = ("send", Dialogs.DYN_DIALOG_TEXT_INPUT)

    if active_item:
        if active_item.type == 0:
            return await bot.router.execute(Dialogs.DYN_DIALOG_OPTION_SELECT, update, context)
        elif active_item.type == 1:
            return await bot.router.execute(Dialogs.DYN_DIALOG_TEXT_INPUT, update, context)
        elif active_item.type == 2:
            button = ("send", Dialogs.DYN_DIALOG_IMAGE_UPLOAD)

    fallback_item = bot.router.get_entry_point_item(context) or -1

    if(dialog.trace): keyboard = bot.create_keyboard([[("back", Actions.BACK)]])
    else: keyboard = bot.create_keyboard([[("cancel", fallback_item)]])
    
    item_text = active_item.text if active_item else "---"
    await bot.send_message(update, context, item_text, keyboard)
    return Dialogs.SERVICE


async def start_dyn_dialog_typing_subdialog( update: "Update", context: "ContextTypes.DEFAULT_TYPE", bot: "Bot") -> int:

    dialog = bot.local_storage.get(context, Variables.ACTIVE_DYN_DIALOG)
    if dialog is None:
        return Actions.END

    sequences = dialog.sequences
    items = dialog.items

    active_sequence_id = bot.local_storage.get(context, Variables.ACTIVE_DIALOG_SEQUENCE_ID) or 0
    active_sequence_item_index = bot.local_storage.get(context, Variables.ACTIVE_DIALOG_SEQUENCE_ITEM_INDEX) or 0
    active_sequence = sequences.get(active_sequence_id)
    active_item_id = active_sequence.items_ids[active_sequence_item_index]
    active_item = items.get(active_item_id)
    fallback_item = bot.router.get_entry_point_item(context) or -1
    if(dialog.trace): keyboard = bot.create_keyboard([[("back", Actions.BACK)]])
    else: keyboard = bot.create_keyboard([[("cancel", fallback_item)]])

    await bot.send_message(
        update, context, "multi_dialog_item_text_handler_prompt", keyboard, payload=[active_item.text]
    )

    return Actions.TYPING


async def start_dyn_dialog_select_subdialog(update: "Update", context: "ContextTypes.DEFAULT_TYPE", bot: "Bot") -> int:

    dialog = bot.local_storage.get(context, Variables.ACTIVE_DYN_DIALOG)
    if dialog is None:
        return Actions.END

    sequences = dialog.sequences
    items = dialog.items
    options = dialog.options

    active_sequence_id = bot.local_storage.get(context, Variables.ACTIVE_DIALOG_SEQUENCE_ID) or 0
    active_sequence_item_index = bot.local_storage.get(context, Variables.ACTIVE_DIALOG_SEQUENCE_ITEM_INDEX) or 0
    active_sequence = sequences.get(active_sequence_id)
    active_item_index = active_sequence.items_ids[active_sequence_item_index]
    active_item = items.get(active_item_index)
    active_options = [options[i] for i in (active_item.options_ids or []) if i in options]
    fallback_item = bot.router.get_entry_point_item(context) or -1

    options_by_row = {}
    for option in active_options:
        if option.row not in options_by_row:
            options_by_row[option.row] = []
        options_by_row[option.row].append((option.text, str(Dialogs.DYN_DIALOG_ITEM) + ":" + str(option.id)))

    keyboard_rows = []
    for row in sorted(options_by_row.keys()):
        keyboard_rows.append(options_by_row[row])
    if(dialog.trace): keyboard_rows.append([("back", Actions.BACK)])
    else: keyboard_rows.append([("cancel", fallback_item)])

    keyboard = bot.create_keyboard(keyboard_rows)

    await bot.send_message(
        update, context, "multi_dialog_item_select_handler_prompt", keyboard, payload=[active_item.text]
    )

    return Actions.SELECTING


async def start_dyn_dialog_upload_subdialog( update: "Update", context: "ContextTypes.DEFAULT_TYPE", bot: "Bot") -> int:

    dialog = bot.local_storage.get(context, Variables.ACTIVE_DYN_DIALOG)
    if dialog is None:
        return Actions.END

    sequences = dialog.sequences
    items = dialog.items

    active_sequence_id = bot.local_storage.get(context, Variables.ACTIVE_DIALOG_SEQUENCE_ID) or 0
    active_sequence_item_index = bot.local_storage.get(context, Variables.ACTIVE_DIALOG_SEQUENCE_ITEM_INDEX) or 0
    active_sequence = sequences.get(active_sequence_id)
    active_item_index = active_sequence.items_ids[active_sequence_item_index]
    active_item = items.get(active_item_index)
    fallback_item = bot.router.get_entry_point_item(context) or -1

    if(dialog.trace): keyboard = bot.create_keyboard([[("back", Actions.BACK)]])
    else: keyboard = bot.create_keyboard([[("cancel", fallback_item)]])

    await bot.send_message(
        update, context, "multi_dialog_item_text_handler_prompt ", keyboard, payload=[active_item.text]
    )

    return Actions.UPLOADING

async def start_prev_dyn_dialog( update: "Update", context: "ContextTypes.DEFAULT_TYPE", bot: "Bot") -> int:
    dialog = bot.local_storage.get(context, Variables.ACTIVE_DYN_DIALOG)
    if dialog is None:
        return Actions.END

    sequences = dialog.sequences
    items = dialog.items
    options = dialog.options

    active_sequence_id = bot.local_storage.get(context, Variables.ACTIVE_DIALOG_SEQUENCE_ID) or 0
    active_sequence_item_index = bot.local_storage.get(context, Variables.ACTIVE_DIALOG_SEQUENCE_ITEM_INDEX) or 0
    active_sequence = sequences.get(active_sequence_id)
    active_item_index = active_sequence.items_ids[active_sequence_item_index]
    active_item = items.get(active_item_index)
    parent_item = bot.router.get_parent_item(context)
    entry_item = bot.router.get_entry_point_item(context)
    trace_item = bot.router.pop_previous_trace_item(context)
    
    if trace_item is None:
        return Actions.END
    
    print(parent_item, entry_item, trace_item)
    
    if trace_item == parent_item or trace_item == entry_item:
        bot.local_storage.set(context, Variables.ACTIVE_DIALOG_SEQUENCE_ID, 0)
        bot.local_storage.set(context, Variables.ACTIVE_DIALOG_SEQUENCE_ITEM_INDEX, 0)
        return await bot.router.execute_entry_point(update, context, bot)
    else: 
        trace_item_sequence, trace_sequence_item_index = trace_item.split(":")
        trace_item_sequence = int(trace_item_sequence)
        trace_sequence_item_index = int(trace_sequence_item_index)
        bot.local_storage.set(context, Variables.ACTIVE_DIALOG_SEQUENCE_ID, trace_item_sequence)
        bot.local_storage.set(context, Variables.ACTIVE_DIALOG_SEQUENCE_ITEM_INDEX, trace_sequence_item_index)
        
    return await bot.router.execute_parent(update, context, bot)
