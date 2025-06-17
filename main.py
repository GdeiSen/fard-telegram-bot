import argparse
from bot import Agent

def main() -> None:
    parser = argparse.ArgumentParser(
        description="Telegram бот для управления заявками"
    )
    parser.add_argument(
        "--token", 
        type=str, 
        required=True,
        help="Токен Telegram бота"
    )
    parser.add_argument(
        "--db-url", 
        type=str, 
        required=True,
        help="URL подключения к базе данных"
    )
    parser.add_argument(
        "--admin-chat-id",
        type=str,
        required=True,
        help="ID группового чата администраторов для обработки заявок"
    )
    parser.add_argument(
        "--chief-engineer-chat-id",
        type=str,
        required=False,
        default=None,
        help="ID чата главного инженера для отправки замечаний"
    )
    
    args = parser.parse_args()
    
    agent = Agent()
    agent.start(
        token=args.token, 
        db_url=args.db_url, 
        admin_chat_id=args.admin_chat_id,  
        chief_engineer_chat_id=args.chief_engineer_chat_id
    )

if __name__ == "__main__":
    main() 