from telegram import helpers
LPR_ROLE = 10011
MA_ROLE = 20122
bot_username = "test_senoogi_bot"
lpr_url = helpers.create_deep_linked_url(bot_username, str(LPR_ROLE), group=False)
ma_url = helpers.create_deep_linked_url(bot_username, str(MA_ROLE), group=False)

print(f"ЛПР ссылка: {lpr_url}")
print(f"МА ссылка: {ma_url}")
