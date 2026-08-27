import os
import time
import random
import json
import threading
from flask import Flask
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
from selenium.common.exceptions import NoSuchElementException, TimeoutException

# ========== Flask для пинга ==========
app = Flask('')

@app.route('/')
def home():
    return "I'm alive!"

def run_flask():
    app.run(host='0.0.0.0', port=8080)

flask_thread = threading.Thread(target=run_flask, daemon=True)
# ====================================

def setup_remote_driver():
    """Подключается к Selenium Standalone Chrome"""
    host = os.environ.get('SELENIUM_HOST', 'standalone-chrome')
    command_executor = f"http://{host}:4444/wd/hub"
    print(f'[GenAternosMC] Пробую подключиться к Selenium: {command_executor}')
    
    options = Options()
    options.add_argument("--headless")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--disable-gpu")
    options.add_argument("--window-size=1920,1080")
    options.add_argument("--disable-blink-features=AutomationControlled")
    options.add_experimental_option("excludeSwitches", ["enable-automation"])
    options.add_experimental_option('useAutomationExtension', False)

    try:
        driver = webdriver.Remote(
            command_executor=command_executor,
            options=options
        )
        # Проверяем соединение
        driver.get('about:blank')
        print(f'[GenAternosMC] Успешно подключено к {command_executor}')
        return driver
    except Exception as e:
        raise Exception(f'Не удалось подключиться к {command_executor}: {e}')

def handle_ad_popup(driver):
    """Закрывает рекламный попап, если он есть"""
    try:
        ad_button = WebDriverWait(driver, 5).until(
            EC.element_to_be_clickable((By.XPATH, '//div[contains(text(), "Всё равно продолжить с блокировщиком рекламы")]'))
        )
        ad_button.click()
        time.sleep(2)
        return True
    except:
        return False

def get_server_status(driver):
    """Возвращает текст статуса сервера (Оффлайн, Запуск, Онлайн)"""
    try:
        # Пробуем найти элемент статуса по разным селекторам
        selectors = [
            "//span[@class='server-status']",  # частая структура
            "//span[contains(@class, 'status')]",
            "//div[@class='server-status']/span",
            "//*[@id='read-our-tos']/main/section/div[3]/div[2]/div[1]/div/span[1]/span"  # старый, на случай
        ]
        for xp in selectors:
            try:
                elem = driver.find_element(By.XPATH, xp)
                text = elem.text.strip()
                if text:
                    return text
            except:
                continue
        return None
    except:
        return None

def click_start_button(driver):
    """Нажимает кнопку 'Запустить' или 'Start'"""
    try:
        # Ищем кнопку по тексту или ID
        start_btn = WebDriverWait(driver, 10).until(
            EC.element_to_be_clickable((By.XPATH, "//button[contains(text(), 'Запустить') or contains(text(), 'Start')]"))
        )
        start_btn.click()
        return True
    except:
        try:
            # Альтернативный поиск по ID
            start_btn = driver.find_element(By.ID, "start")
            start_btn.click()
            return True
        except:
            return False

def extend_server(driver):
    """Нажимает кнопку 'Продлить' (+1 минута)"""
    try:
        # Поиск кнопки продления
        extend_btn = WebDriverWait(driver, 10).until(
            EC.element_to_be_clickable((By.XPATH, "//button[contains(@class, 'server-extend-end')]"))
        )
        extend_btn.click()
        return True
    except:
        return False

def maintain_server_connection(driver):
    """Основной цикл поддержания сервера"""
    print('[GenAternosMC] Начинаю поддержание сервера')
    while True:
        try:
            # Пытаемся продлить
            if extend_server(driver):
                print('[GenAternosMC] Сервер продлён на +1 минуту')
            else:
                print('[GenAternosMC] Кнопка продления не найдена, проверяем статус...')
                status = get_server_status(driver)
                print(f'[GenAternosMC] Статус сервера: {status}')
                if status and ("Оффлайн" in status or "Offline" in status):
                    print('[GenAternosMC] Сервер оффлайн, пробуем запустить...')
                    if click_start_button(driver):
                        print('[GenAternosMC] Кнопка запуска нажата, ждём...')
                        time.sleep(35)  # ждём запуска
                    else:
                        print('[GenAternosMC] Не удалось нажать кнопку запуска')
            
            # Пауза перед следующим циклом (проверяем каждые 30-60 секунд)
            wait_time = random.randint(30, 60)
            print(f'[GenAternosMC] Следующая проверка через {wait_time} секунд')
            time.sleep(wait_time)
            
        except KeyboardInterrupt:
            print('[GenAternosMC] Получен сигнал прерывания (Ctrl+C)')
            break
        except Exception as e:
            print(f'[GenAternosMC] Ошибка в цикле поддержания: {e}')
            time.sleep(10)

def show_logo():
    logo = """
   _____                    _                            __  __  _____ 
  / ____|              /\  | |                          |  \/  |/ ____|
 | |  __  ___ _ __    /  \ | |_ ___ _ __ _ __   ___  ___| \  / | |     
 | | |_ |/ _ \ '_ \  / /\ \| __/ _ \ '__| '_ \ / _ \/ __| |\/| | |     
 | |__| |  __/ | | |/ ____ \ ||  __/ |  | | | | (_) \__ \ |  | | |____ 
  \_____|\___|_| |_/_/    \_\__\___|_|  |_| |_|\___/|___/_|  |_|\_____|
    """
    print(logo)

def start_server(session_cookie, server_id, server_ip):
    driver = setup_remote_driver()
    try:
        print('[GenAternosMC] Remote драйвер подключен')
        
        # Переходим на страницу серверов
        driver.get('https://aternos.org/servers/')
        print('[GenAternosMC] Открыта страница /servers/')
        time.sleep(3)
        
        # Устанавливаем куки
        driver.add_cookie({'name': 'ATERNOS_SESSION', 'value': session_cookie})
        driver.add_cookie({'name': "ATERNOS_SERVER", 'value': server_id})
        print('[GenAternosMC] Куки установлены')
        
        # Переходим на страницу конкретного сервера
        driver.get('https://aternos.org/server/')
        print('[GenAternosMC] Переход на /server/')
        time.sleep(5)  # даём странице загрузиться
        
        # Закрываем рекламный попап
        handle_ad_popup(driver)
        
        # Обновляем, чтобы применились куки
        driver.refresh()
        time.sleep(3)
        handle_ad_popup(driver)
        
        # Получаем статус сервера
        status = get_server_status(driver)
        print(f'[GenAternosMC] Текущий статус сервера: {status}')
        
        if status is None:
            print('[GenAternosMC] Не удалось определить статус. Возможно, страница не загружена.')
            # Попробуем обновить ещё раз
            driver.refresh()
            time.sleep(5)
            status = get_server_status(driver)
            print(f'[GenAternosMC] Статус после обновления: {status}')
        
        # Действия в зависимости от статуса
        if status and ("Оффлайн" in status or "Offline" in status):
            print('[GenAternosMC] Сервер оффлайн, запускаем...')
            if click_start_button(driver):
                print('[GenAternosMC] Кнопка запуска нажата')
                time.sleep(35)  # ждём запуска
                # Проверим статус через 35 сек
                new_status = get_server_status(driver)
                print(f'[GenAternosMC] Статус после запуска: {new_status}')
                if new_status and ("Онлайн" in new_status or "Online" in new_status):
                    print('[GenAternosMC] Сервер запущен!')
                    maintain_server_connection(driver)
                else:
                    print('[GenAternosMC] Сервер не запустился, пытаемся снова...')
                    # можно повторить попытку или перезапустить цикл
            else:
                print('[GenAternosMC] Не удалось нажать кнопку запуска')
        
        elif status and ("Запуск" in status or "Starting" in status):
            print('[GenAternosMC] Сервер запускается, ждём...')
            time.sleep(35)
            new_status = get_server_status(driver)
            print(f'[GenAternosMC] Статус после ожидания: {new_status}')
            if new_status and ("Онлайн" in new_status or "Online" in new_status):
                print('[GenAternosMC] Сервер онлайн!')
                maintain_server_connection(driver)
            else:
                print('[GenAternosMC] Сервер не перешёл в онлайн, пробуем запустить заново...')
                if click_start_button(driver):
                    print('[GenAternosMC] Повторный запуск')
                    time.sleep(35)
                    maintain_server_connection(driver)
        
        elif status and ("Онлайн" in status or "Online" in status):
            print('[GenAternosMC] Сервер уже онлайн!')
            maintain_server_connection(driver)
        
        else:
            print('[GenAternosMC] Неизвестный статус, пробуем запустить принудительно...')
            if click_start_button(driver):
                print('[GenAternosMC] Принудительный запуск')
                time.sleep(35)
                maintain_server_connection(driver)
            else:
                print('[GenAternosMC] Не удалось запустить сервер.')
        
    except KeyboardInterrupt:
        print('[GenAternosMC] Прерывание пользователем')
    except Exception as e:
        print(f'[GenAternosMC] Критическая ошибка: {e}')
    finally:
        driver.quit()
        print('[GenAternosMC] Драйвер закрыт')

if __name__ == '__main__':
    os.system('cls' if os.name == 'nt' else 'clear')
    show_logo()
    print("""
╭──────────────────────────────────────────────────────╮
│ Использование: python GenAternosMC.py               │
│ (читает config.json)                                │
│ Переменная окружения SELENIUM_HOST (опционально)    │
╰──────────────────────────────────────────────────────╯
""")
    
    # Загружаем конфиг
    config_path = 'config.json'
    if not os.path.exists(config_path):
        print('[GenAternosMC] Ошибка: config.json не найден!')
        exit(1)
    
    with open(config_path, 'r') as f:
        config = json.load(f)
        ip_address = config['aternos_server']['ip']
        server_id = config['aternos_server']['server_id']
        session_cookie = config['aternos_server']['session_cookie']
    
    print(f'[GenAternosMC] IP сервера: {ip_address}')
    print(f'[GenAternosMC] ID сервера: {server_id}')
    print(f'[GenAternosMC] Сессия: {session_cookie[:20]}...')
    
    # Запускаем Flask (пинг)
    flask_thread.start()
    print('[GenAternosMC] Flask-сервер запущен на порту 8080 для пинга')
    
    # Запускаем основную логику
    start_server(session_cookie, server_id, ip_address)
