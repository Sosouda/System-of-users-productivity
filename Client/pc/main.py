from local_db.data_manager import init_db, daily_insert, update_tasks_status
from ui.app_manager import run_app

def main():
    print("Запуск системы управления продуктивностью...")
    init_db()
    daily_insert()
    update_tasks_status()

    run_app()

if __name__ == "__main__":
    main()
